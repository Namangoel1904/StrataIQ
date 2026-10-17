"""
StrataIQ — Populate Real Vector Embeddings
Computes 3072-dimensional embeddings via Google GenAI (gemini-embedding-001)
and writes them directly into local_enterprise.db document_chunks_vectors.embedding_json.
"""
import json
import os
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from google import genai
import sqlite3

def populate_all_chunk_embeddings():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment!")
        sys.exit(1)

    db_path = backend_dir.parent / "enterprise_data_vault" / "rdbms" / "local_enterprise.db"
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        sys.exit(1)

    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT chunk_id, doc_id, page_number, section_title, chunk_text FROM document_chunks_vectors")
    chunks = cursor.fetchall()
    total_chunks = len(chunks)
    print(f"Found {total_chunks} total chunks to embed.")

    client = genai.Client(api_key=api_key)
    model_name = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    print(f"Using Google GenAI embedding model: {model_name}")

    updated_count = 0
    dim_size = 0

    for idx, (chunk_id, doc_id, page_no, sec_title, text) in enumerate(chunks, 1):
        content_to_embed = f"Document: {doc_id} | Section: {sec_title}\n{text}"
        try:
            resp = client.models.embed_content(
                model=model_name,
                contents=content_to_embed,
            )
            vec = resp.embeddings[0].values
            dim_size = len(vec)
            vec_json = json.dumps(vec)

            cursor.execute(
                "UPDATE document_chunks_vectors SET embedding_json = ? WHERE chunk_id = ?",
                (vec_json, chunk_id),
            )
            updated_count += 1
            if idx % 5 == 0 or idx == total_chunks:
                conn.commit()
                print(f"[{idx}/{total_chunks}] Embedded {chunk_id} ({doc_id} p.{page_no}) - Dim: {dim_size}")
            time.sleep(0.1)  # friendly rate pacing
        except Exception as e:
            print(f"Error embedding {chunk_id}: {e}")

    conn.commit()
    conn.close()

    print(f"\n[OK] COMPLETED: Successfully embedded {updated_count}/{total_chunks} chunks.")
    print(f"Vector dimension: {dim_size}")

if __name__ == "__main__":
    populate_all_chunk_embeddings()
