# STRATAIQ — ANTIGRAVITY ALWAYS-ON SYSTEM BRAIN & ENGINEERING RULES

@[Master Architecture and Phase Plan](./PLAN.md)

## 1. CORE MINDSET & NON-NEGOTIABLE INVARIANTS
- **Production-Grade Product, NOT a Toy Prototype:** We are competing in the Google Cloud AI Builder Cup (Working Professionals Track). Every feature must be end-to-end functional so judges say: *"Why is this a prototype? I would love for this to be an actual application that I can use."*
- **Zero-Mock / Zero-Dummy Policy:** NEVER hardcode fake responses, static arrays, or dummy timers in API endpoints. Every endpoint MUST query or mutate the real 10-table relational database (`./enterprise_data_vault/rdbms/local_enterprise.db` in local dev, or `DATABASE_URL` for Google Cloud SQL PostgreSQL in production).
- **Instant Day-Zero Personalization (No Waiting on User History):** Personalization is driven immediately on login by the user's `layer_id` (`UPPER`, `MIDDLE`, `LOWER`) and `dept_id` (`DEPT-FIN`, `DEPT-HR`, `DEPT-ENG`, `DEPT-LEG`, `DEPT-OPS`, `DEPT-IT`) from the `users` table, combined with silent layout preference persistence (`ui_preferences_json` / Firestore / Backboard.io).
- **AI Empowers Decision Makers, Never Replaces Them:** For high-stakes company issues, AI must never make unilateral decisions. It must present verified facts, cross-silo conflict alerts, and a 3-Option Quantified Decision Matrix (`decision_matrix_logs`) for a human decision-maker to approve via an ACID database transaction.
- **Strict Phase Gate Protocol:** Complete ONLY the currently requested Phase. At the end of each Phase, run automated tests (`pytest` / build checks) and provide a clear summary of implemented endpoints/features and how the developer can manually verify them before moving to the next Phase.

## 2. EXISTING DATA VAULT (DO NOT OVERWRITE OR BREAK)
- `./enterprise_data_vault/files/`: 22 synthesized enterprise documents (`.pdf`, `.csv`, `.docx`) modeling a 60-day Corporate Health Insurance Vendor Transition from **LegacyCare Assurance (`POL-LEGACY-2025`)** to **NovaShield Health (`POL-NOVASHIELD-2026`)**.
- `./enterprise_data_vault/rdbms/local_enterprise.db`: Populated 10-table SQLite replica with 500 employees, 6 showcase personas, 22 documents, 55+ document chunks, 12 transition hospital claims, 7 workflow tasks, and 1 executive decision matrix record.
- `./enterprise_data_vault/rdbms/cloud_sql_postgres_schema_and_rls.sql`: Production Cloud SQL for PostgreSQL DDL with `pgvector` and Row-Level Security (RLS).
