"""
StrataIQ — Document RAG Agent (rag_agent.py)

Retrieves the most relevant document chunks for a user query.
Enforces Zero-Trust RLS: only chunks from documents with
min_layer_clearance <= user.clearance_level are ever considered.

Search strategy (no live embeddings in Phase 1 DB):
1. BM25-like keyword scoring over chunk_text from document_chunks_vectors
2. For CSV-type documents: also parse raw CSV rows as virtual chunks
3. Returns top-k results ranked by relevance score
"""
from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SecurityContext
from app.models import Document, DocumentChunk

settings = get_settings()


@dataclass
class RAGResult:
    """A single retrieved evidence chunk with provenance metadata."""
    chunk_id: str
    doc_id: str
    file_name: str
    file_type: str
    page_number: int
    section_title: str
    chunk_text: str
    relevance_score: float
    source_type: str = "db_chunk"   # "db_chunk" | "csv_row"


def _tokenize(text: str) -> list[str]:
    """Lowercase tokenizer — splits on non-word chars, strips stop words."""
    _STOP = {
        "the", "and", "for", "are", "that", "this", "with", "from", "into",
        "our", "their", "was", "has", "have", "been", "will", "can", "its",
        "not", "all", "one", "two", "per", "day", "also", "such",
    }
    tokens = re.findall(r"\b[a-z0-9]+(?:'[a-z]+)?\b", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in _STOP]


def _bm25_score(query_tokens: list[str], doc_tokens: list[str],
                avg_dl: float = 80.0, k1: float = 1.5, b: float = 0.75) -> float:
    """BM25 relevance score between query and document token lists."""
    if not query_tokens or not doc_tokens:
        return 0.0

    dl = len(doc_tokens)
    doc_freq: dict[str, int] = {}
    for t in doc_tokens:
        doc_freq[t] = doc_freq.get(t, 0) + 1

    N = 1  # single doc scoring (no IDF corpus needed — we rank within results)
    score = 0.0
    for qt in query_tokens:
        tf = doc_freq.get(qt, 0)
        if tf == 0:
            continue
        idf = math.log((N + 0.5) / 0.5 + 1)  # simplified IDF
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
        score += idf * tf_norm
    return score


def _csv_row_to_text(row: dict) -> str:
    """Serialize a CSV dict row into a flat string for scoring."""
    return " | ".join(f"{k}: {v}" for k, v in row.items() if v)


class DocumentRAGAgent:
    """
    Retrieves RLS-scoped document chunks most relevant to a query.
    Combines DB chunk scoring with CSV row virtual-chunk generation.
    """

    def __init__(self) -> None:
        self._genai_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai  # type: ignore
                self._genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception:
                self._genai_client = None

    def search(
        self,
        query: str,
        ctx: SecurityContext,
        db: Session,
        top_k: int = 6,
        doc_hints: Optional[list[str]] = None,
    ) -> list[RAGResult]:
        """
        Return up to top_k RAGResult objects, ranked by relevance to query,
        respecting Zero-Trust RLS (only documents user is cleared for).

        Strategy:
        1. Score all DB chunks (keyword BM25)
        2. For accessible CSV docs: score CSV rows as virtual chunks
        3. Sort combined list, return top_k
        """
        if self._genai_client and settings.GEMINI_API_KEY:
            try:
                return self._embedding_search(query, ctx, db, top_k, doc_hints)
            except Exception:
                pass  # Fall through to keyword search

        return self._keyword_search(query, ctx, db, top_k, doc_hints)

    # ── Embedding-based search (when Gemini API is available) ─────────────────

    def _embedding_search(
        self, query: str, ctx: SecurityContext, db: Session,
        top_k: int, doc_hints: Optional[list[str]]
    ) -> list[RAGResult]:
        """
        True Hybrid Vector + Keyword RAG Search:
        1. Computes 3072-dim query embedding using gemini-embedding-001.
        2. Computes Cosine Similarity against document_chunks_vectors.embedding_json.
        3. Computes BM25 keyword match against chunk text.
        4. Blends both into a unified Hybrid Relevance Score.
        5. Strictly enforces Zero-Trust RLS (min_layer_clearance <= ctx.clearance_level).
        """
        import numpy as np  # noqa: PLC0415
        import json as _json  # noqa: PLC0415

        # Get query embedding
        response = self._genai_client.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=[query],
        )
        query_vec = np.array(response.embeddings[0].values, dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)

        # Fetch RLS-accessible chunks
        accessible_chunks = self._get_accessible_chunks(ctx, db, doc_hints)
        q_tokens = _tokenize(query)

        results: list[RAGResult] = []
        for chunk, doc in accessible_chunks:
            cosine_score = 0.0
            try:
                vec = _json.loads(chunk.embedding_json or "[]")
                if vec:
                    chunk_vec = np.array(vec, dtype=np.float32)
                    c_norm = np.linalg.norm(chunk_vec)
                    if q_norm > 0 and c_norm > 0:
                        cosine_score = float(np.dot(query_vec, chunk_vec) / (q_norm * c_norm))
                        cosine_score = max(0.0, cosine_score)
            except Exception:
                cosine_score = 0.0

            # Lexical BM25 score
            c_tokens = _tokenize(chunk.chunk_text)
            bm25 = _bm25_score(q_tokens, c_tokens)
            bm25_norm = min(1.0, bm25 / 12.0) if bm25 > 0 else 0.0

            # Hybrid score: 70% Dense Vector Cosine + 30% Sparse BM25 Keyword
            if cosine_score > 0:
                hybrid_score = round(0.70 * cosine_score + 0.30 * bm25_norm, 4)
            else:
                hybrid_score = round(bm25_norm, 4)

            # Boost if targeted in doc_hints
            if doc_hints and chunk.doc_id in doc_hints:
                hybrid_score = round(hybrid_score * 1.25, 4)

            if hybrid_score > 0.05:
                results.append(RAGResult(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    file_name=doc.file_name,
                    file_type=doc.file_type,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    chunk_text=chunk.chunk_text,
                    relevance_score=hybrid_score,
                    source_type="db_chunk",
                ))

        # Add CSV virtual chunks for real-time tabular rows
        csv_results = self._search_csv_docs(query, ctx, db, doc_hints)
        results.extend(csv_results)

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:top_k]

    # ── Keyword BM25 Search ───────────────────────────────────────────────────

    def _keyword_search(
        self, query: str, ctx: SecurityContext, db: Session,
        top_k: int, doc_hints: Optional[list[str]]
    ) -> list[RAGResult]:
        """BM25 keyword scoring over all RLS-accessible chunks + CSV virtual chunks."""
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        accessible_chunks = self._get_accessible_chunks(ctx, db, doc_hints)

        results: list[RAGResult] = []
        for chunk, doc in accessible_chunks:
            c_tokens = _tokenize(chunk.chunk_text)
            score = _bm25_score(q_tokens, c_tokens)
            if score > 0:
                results.append(RAGResult(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    file_name=doc.file_name,
                    file_type=doc.file_type,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    chunk_text=chunk.chunk_text,
                    relevance_score=score,
                    source_type="db_chunk",
                ))

        # Augment with CSV virtual chunks
        csv_results = self._search_csv_docs(query, ctx, db, doc_hints)
        results.extend(csv_results)

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:top_k]

    def _get_accessible_chunks(
        self, ctx: SecurityContext, db: Session,
        doc_hints: Optional[list[str]]
    ) -> list[tuple[DocumentChunk, Document]]:
        """
        Fetch all chunks from documents the user has clearance to view.
        Zero-Trust RLS: filters document_chunks_vectors WHERE
        documents.min_layer_clearance <= ctx.clearance_level.
        """
        query = (
            db.query(DocumentChunk, Document)
            .join(Document, DocumentChunk.doc_id == Document.doc_id)
            .filter(Document.min_layer_clearance <= ctx.clearance_level)
        )

        # If we have doc_hints, boost those docs by fetching them first
        if doc_hints:
            hinted = query.filter(Document.doc_id.in_(doc_hints)).all()
            others = query.filter(Document.doc_id.notin_(doc_hints)).all()
            return hinted + others

        return query.all()

    def _search_csv_docs(
        self, query: str, ctx: SecurityContext, db: Session,
        doc_hints: Optional[list[str]]
    ) -> list[RAGResult]:
        """
        For each CSV document accessible to the user, parse the raw CSV file
        and create virtual chunks from rows that match query keywords.
        This ensures hospital directory lookups always succeed.
        """
        q_tokens = set(_tokenize(query))
        if not q_tokens:
            return []

        csv_docs = (
            db.query(Document)
            .filter(
                Document.file_type == "CSV",
                Document.min_layer_clearance <= ctx.clearance_level,
            )
            .all()
        )

        results: list[RAGResult] = []
        for doc in csv_docs:
            file_path = settings.FILES_DIR / doc.file_name
            if not file_path.exists():
                continue
            try:
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        row_text = _csv_row_to_text(row)
                        row_tokens = set(_tokenize(row_text))
                        # Only include rows with meaningful keyword overlap
                        overlap = q_tokens & row_tokens
                        if len(overlap) >= 1:
                            score = _bm25_score(
                                list(q_tokens), list(row_tokens)
                            )
                            if score > 0:
                                results.append(RAGResult(
                                    chunk_id=f"csv-{doc.doc_id}-row-{i+1}",
                                    doc_id=doc.doc_id,
                                    file_name=doc.file_name,
                                    file_type=doc.file_type,
                                    page_number=i + 1,
                                    section_title=f"CSV Row {i+1}: {list(row.values())[0] if row else ''}",
                                    chunk_text=row_text,
                                    relevance_score=score,
                                    source_type="csv_row",
                                ))
            except Exception:
                continue  # Graceful skip on parse errors

        return results


# Module-level singleton
_rag_agent: Optional[DocumentRAGAgent] = None


def get_rag_agent() -> DocumentRAGAgent:
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = DocumentRAGAgent()
    return _rag_agent
