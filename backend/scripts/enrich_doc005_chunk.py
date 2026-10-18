"""
StrataIQ — Enrich the DOC-005 chunk with the full department cost allocation table + EBITDA impact
and re-compute its gemini-embedding-001 (3072-dim) vector in local_enterprise.db.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from app.agents.dept_financials import build_ledger_text, load_department_ledger
from app.database import SessionLocal

CHUNK_ID = "CHK-D83474738A"
SECTION = "Q3-Q4 Insurance Cost Variance Summary - Department Cost Allocation & EBITDA Impact"


def main() -> None:
    db = SessionLocal()
    try:
        ledger_text = build_ledger_text(load_department_ledger(db))
    finally:
        db.close()

    text = (
        "Total 2025 LegacyCare Premium: INR 1,85,00,000. Total 2026 NovaShield Premium: INR 2,23,40,000. "
        "Gross Parental Rider Variance: INR 38,40,000 (INR 38.4 Lakhs). Unutilized LegacyCare Pro-Rata Refund "
        "available: INR 19,20,000 (INR 19.2 Lakhs). Net unfunded budget gap if split 50/50: INR 19,20,000.\n\n"
        + ledger_text
    )

    vec_json = None
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        from google import genai
        client = genai.Client(api_key=api_key)
        resp = client.models.embed_content(
            model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
            contents=f"Document: DOC-005 | Section: {SECTION}\n{text}",
        )
        vals = resp.embeddings[0].values
        print(f"Embedding dimension: {len(vals)}")
        vec_json = json.dumps(vals)
    else:
        print("WARNING: GEMINI_API_KEY missing - chunk text updated, embedding left unchanged.")

    db_path = backend_dir.parent / "enterprise_data_vault" / "rdbms" / "local_enterprise.db"
    conn = sqlite3.connect(str(db_path))
    if vec_json:
        conn.execute(
            "UPDATE document_chunks_vectors SET section_title=?, chunk_text=?, embedding_json=? WHERE chunk_id=?",
            (SECTION, text, vec_json, CHUNK_ID),
        )
    else:
        conn.execute(
            "UPDATE document_chunks_vectors SET section_title=?, chunk_text=? WHERE chunk_id=?",
            (SECTION, text, CHUNK_ID),
        )
    conn.commit()
    conn.close()
    print(f"Updated {CHUNK_ID}:\n{text}")


if __name__ == "__main__":
    main()
