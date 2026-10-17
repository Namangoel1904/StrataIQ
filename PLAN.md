# STRATAIQ — MASTER ARCHITECTURE, ITERATION CONTEXT & 5-PHASE PLAN

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
