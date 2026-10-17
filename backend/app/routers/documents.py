"""
StrataIQ Documents Router — Security-Scoped Document Vault & Viewer API

Endpoints:
  GET  /api/v1/documents                          — List all RLS-permitted documents
  GET  /api/v1/documents/{doc_id}/content         — Chunks + CSV rows (RLS enforced)
  GET  /api/v1/documents/{doc_id}/download        — Stream raw file (RLS enforced)
"""
import csv
import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import get_settings
from app.database import get_db, get_security_context, SecurityContext, assert_document_clearance
from app.models import Document, DocumentChunk
from app.schemas import (
    DocumentsListResponse, DocumentItem,
    DocumentContentResponse, DocumentChunk as DocumentChunkSchema,
)

router = APIRouter()
settings = get_settings()

# MIME type map for file downloads
_MIME_TYPES = {
    "PDF": "application/pdf",
    "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "CSV": "text/csv",
}


@router.get(
    "",
    response_model=DocumentsListResponse,
    summary="List RLS-Scoped Documents",
)
def list_documents(
    ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db),
):
    """
    Returns all documents from the vault, split into:
    - accessible_docs: documents where min_layer_clearance <= user's clearance_level
    - restricted_hidden_count: count of documents the user cannot access

    This powers the Zero-Trust Clearance Shield indicator in the UI:
    e.g. "16 Documents Accessible | 6 Restricted by L1 Clearance"
    """
    all_docs = db.query(Document).all()

    accessible = []
    restricted_count = 0

    for doc in all_docs:
        # Count chunks for this document
        chunk_count = db.query(func.count(DocumentChunk.chunk_id)).filter(
            DocumentChunk.doc_id == doc.doc_id
        ).scalar() or 0

        if doc.min_layer_clearance <= ctx.clearance_level:
            accessible.append(DocumentItem(
                doc_id=doc.doc_id,
                file_name=doc.file_name,
                file_type=doc.file_type,
                dept_id=doc.dept_id,
                min_layer_clearance=doc.min_layer_clearance,
                version=doc.version,
                chunk_count=chunk_count,
                gcs_uri=doc.gcs_uri,
                uploaded_by=doc.uploaded_by,
            ))
        else:
            restricted_count += 1

    return DocumentsListResponse(
        accessible_docs=accessible,
        restricted_hidden_count=restricted_count,
        total_docs=len(all_docs),
        clearance_level=ctx.clearance_level,
    )


@router.get(
    "/{doc_id}/content",
    response_model=DocumentContentResponse,
    summary="Get Document Chunks (RLS Enforced)",
)
def get_document_content(
    doc_id: str,
    ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db),
):
    """
    Returns all structured document_chunks_vectors for a document,
    ordered by page_number. For CSV files, also returns parsed CSV rows.
    Enforces Zero-Trust RLS: returns 403 if clearance is insufficient.
    """
    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found.",
        )

    # Zero-Trust RLS gate
    assert_document_clearance(doc.min_layer_clearance, ctx)

    # Fetch chunks ordered by page
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.doc_id == doc_id)
        .order_by(DocumentChunk.page_number)
        .all()
    )

    chunk_schemas = [
        DocumentChunkSchema(
            chunk_id=c.chunk_id,
            page_number=c.page_number,
            section_title=c.section_title,
            chunk_text=c.chunk_text,
        )
        for c in chunks
    ]

    # For CSV files: additionally parse the raw file for interactive table rendering
    csv_rows = None
    if doc.file_type == "CSV":
        file_path = settings.FILES_DIR / doc.file_name
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    csv_rows = [dict(row) for row in reader]
            except Exception:
                csv_rows = None  # Graceful degradation — chunks are still returned

    return DocumentContentResponse(
        doc_id=doc.doc_id,
        file_name=doc.file_name,
        file_type=doc.file_type,
        chunks=chunk_schemas,
        csv_rows=csv_rows,
    )


@router.get(
    "/{doc_id}/download",
    summary="Download Raw Document File (RLS Enforced)",
)
def download_document(
    doc_id: str,
    ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db),
):
    """
    Streams the raw .pdf, .docx, or .csv file from the enterprise_data_vault.
    Enforces Zero-Trust RLS: returns 403 if clearance is insufficient.
    """
    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found.",
        )

    # Zero-Trust RLS gate
    assert_document_clearance(doc.min_layer_clearance, ctx)

    file_path = settings.FILES_DIR / doc.file_name
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical file '{doc.file_name}' not found on server.",
        )

    media_type = _MIME_TYPES.get(doc.file_type.upper(), "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=doc.file_name,
    )
