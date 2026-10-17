import os

GEMINI_MD_CONTENT = """# STRATAIQ — ANTIGRAVITY ALWAYS-ON SYSTEM BRAIN & ENGINEERING RULES

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
"""

PLAN_MD_CONTENT = """# STRATAIQ — MASTER ARCHITECTURE, ITERATION CONTEXT & 5-PHASE PLAN

## 1. HOW WE ARRIVED AT THIS ARCHITECTURE (CONTEXT FROM MENTOR SESSIONS)
1. **Why Track 5 (Future of Work & Enterprise Productivity):** Knowledge workers lose 1.8–2.5 hours/day searching across disconnected PDFs, spreadsheets, and databases. Standard AI tools fail because they give every employee the same generic summary, ignore database state, and lack role-level security.
2. **Why the 3-Layer x 6-Department Matrix:** Instead of restricting the app to 3 hardcoded roles, StrataIQ supports the entire organization across **3 Layers** (`UPPER` Strategic Clearance 3, `MIDDLE` Tactical Clearance 2, `LOWER` Execution Clearance 1) × **6 Departments** (`Finance`, `HR`, `Engineering`, `Legal`, `Operations`, `IT`).
3. **Why One Modular JSON-Driven Dashboard + Judge Sandbox Bar:** In production, an employee is locked to their authenticated role. However, for hackathon judges evaluating the app in a 3-minute window, the top header provides a **"Judge Sandbox Mode: Simulate Logged-In Employee"** switcher so judges can swap between 6 real database personas (`USR-UPPER-FIN-001`, `USR-UPPER-HR-002`, `USR-MID-HR-003`, `USR-MID-IT-004`, `USR-LOW-ENG-005`, `USR-LOW-OPS-006`) and watch the UI layout, SQL rows, and Zero-Trust security clearance transform in real time.
4. **Why Corporate Health Insurance Vendor Transition as Flagship Demo:** Based on a real enterprise pain point where switching health insurance vendors causes a 1–2 month operational storm across every layer:
   - **Lower Layer (`USR-LOW-ENG-005` Naman Goel - Senior Engineer):** Uses **"Talk with Your Documents"** (pointed Voice-to-Doc Q&A via Google STT + Gemini + Google TTS) on `DOC-011` and `DOC-010` to ask if Sahyadri Hospital in Pune is cashless for his father's cataract surgery and what the new limit is (`INR 45,000/eye`, up from `INR 35,000`), while seeing his personal SQL enrollment alert (`parental_opt_in = PENDING_CONFIRMATION` before Oct 22).
   - **Middle Layer (`USR-MID-HR-003` Priya Kulkarni - HR Lead):** Automatically detects a **Cross-Silo Schedule Collision** between `DOC-018` (War-Room Transcript) and `workflow_tasks` (`TSK-03` Finance payroll lock on Oct 20 vs. `TSK-05` IT SSO portal launch on Oct 23), blocking 142 employees and 11 transition hospital claims (`INR 14.2 Lakhs`).
   - **Upper Layer (`USR-UPPER-FIN-001` Arvind Mehta - CFO):** Reviews the `INR 38.4 Lakh` parental premium variance and approves `OPTION_B_RECOMMENDED` (applying the `INR 19.2L` LegacyCare refund + welfare reserve and extending the payroll cutoff to Oct 25), which executes a live ACID SQL transaction updating `decision_matrix_logs` and resolving `TSK-03` in `workflow_tasks`.

---

## 2. THE 5 SEQUENTIAL BUILD PHASES (WITH STRICT VERIFICATION GATES)

### PHASE 1: Backend Core, 10-Table RDBMS Engine & Zero-Trust RLS API (`./backend`)
- Dual-engine SQLAlchemy layer (`local_enterprise.db` + Cloud SQL Postgres `DATABASE_URL`).
- `SecurityContext` dependency enforcing Row-Level Security (`X-User-Id` -> `clearance_level` 1, 2, 3).
- REST endpoints for `/api/v1/workspace/personas`, `/api/v1/workspace/bootstrap`, `/api/v1/workspace/confirm-parental-rider`, `/api/v1/workspace/reset-demo-state`, `/api/v1/documents`, `/api/v1/documents/{doc_id}/content`, `/api/v1/decisions`, and `/api/v1/decisions/{decision_id}/approve`.
- Verification: 100% passing `pytest` suite (`test_phase1_rdbms_and_rls.py`) + live FastAPI `/docs` test.

### PHASE 2: Google ADK Multi-Agent Engine, Hybrid Vector/SQL RAG & Groundedness Evals
- Google ADK / Gemini (`gemini-2.5-flash` / `gemini-2.5-pro` & `gemini-3.8-flash` configurable) multi-agent pipeline:
  1. **Tinker-Gemma Context Router:** Fast intent classification & pointed-document filter.
  2. **Document RAG Agent:** Retrieves exact `document_chunks_vectors` (`doc_id`, `page_number`, `section_title`, `chunk_text`) respecting RLS clearance.
  3. **Relational SQL Agent:** Runs read-only parameterized SQL queries on enrollments, claims, tasks, and cost tables.
  4. **Synthesis & Groundedness Eval Agent:** Computes a deterministic + LLM Groundedness Score (`0.0` to `1.0`) verifying every number/claim against retrieved SQL/doc evidence.
- Verification: `pytest` agent accuracy & security tests + `/api/v1/agent/query` live test.

### PHASE 3: "Talk with Your Documents" Bidirectional Voice & Citation Pipeline
- Pointed document voice Q&A endpoint (`/api/v1/voice/talk-to-docs`) integrating **Google Cloud Speech-to-Text (STT)** and **Google Cloud Text-to-Speech (TTS WaveNet/Neural2)** with automatic browser Web Speech / clean audio synthesis fallback so voice demos work 100% reliably both offline and on GCP.
- Returns synthesized audio + exact citation coordinates (`doc_id`, `page_number`, `section_title`, `highlight_snippet`) so the UI auto-scrolls and highlights the exact paragraph while speaking.

### PHASE 4: Modular Role-Adaptive Frontend & Interactive Document Citation Studio (`./frontend`)
- Enterprise-grade React/Next.js + Tailwind UI featuring:
  - Top **Judge Sandbox Persona Switcher** + **Zero-Trust Clearance Shield Indicator**.
  - Dynamic **3-Layer × 6-Department Modular Workspace** (renders Executive Decision Matrix for Upper, Cross-Silo Conflict & Claims War-Room for Middle, Personal Benefits & Task Checklist for Lower).
  - Split-screen **"Talk with Your Documents" Voice Studio & Interactive PDF/CSV/DOCX Viewer** that auto-scrolls to cited pages and highlights text in real time.

### PHASE 5: Production Dockerization, Cloud Run Deployment & Final E2E Audit
- Multi-stage `Dockerfile`, `cloudbuild.yaml`, and one-command `deploy_cloud_run.sh` script with health checks, caching headers, and complete README documentation.
"""

with open("GEMINI.md", "w", encoding="utf-8") as f:
    f.write(GEMINI_MD_CONTENT.strip() + "\n")

with open("PLAN.md", "w", encoding="utf-8") as f:
    f.write(PLAN_MD_CONTENT.strip() + "\n")

print("SUCCESS: Created GEMINI.md and PLAN.md in workspace root!")
print("Antigravity will now automatically load both files into its always-on memory.")