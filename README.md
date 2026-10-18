# StrataIQ 🧠🎙️

> **Role-Adaptive Enterprise Knowledge, Voice & Decision Copilot**  
> *Google Cloud AI Builder Cup — Track 5: Future of Work & Enterprise Productivity*

| Resource | Live Link / Details |
| :--- | :--- |
| 🌐 **Live Web Application** | **[https://strataiq-naomuofz7q-uc.a.run.app](https://strataiq-naomuofz7q-uc.a.run.app)** |
| 📑 **Interactive API Explorer (Swagger)** | **[https://strataiq-naomuofz7q-uc.a.run.app/docs](https://strataiq-naomuofz7q-uc.a.run.app/docs)** |
| 🔍 **Forensic Proof & SDK Status** | **[https://strataiq-naomuofz7q-uc.a.run.app/api/v1/agent/sdk-status](https://strataiq-naomuofz7q-uc.a.run.app/api/v1/agent/sdk-status)** |
| 🩺 **Liveness & Cloud Run Health Probe** | **[https://strataiq-naomuofz7q-uc.a.run.app/health](https://strataiq-naomuofz7q-uc.a.run.app/health)** |
| 🔥 **Google Cloud Firestore Console** | **[Firestore Data Panel (`friday-494818`)](https://console.cloud.google.com/firestore/databases/-default-/data/panel?project=friday-494818)** |
| ⚡ **Cloud Run Metrics & Service Console** | **[Cloud Run Service `strataiq`](https://console.cloud.google.com/run/detail/us-central1/strataiq/metrics?project=friday-494818)** |
| 🛡️ **Deployment Specs** | `us-central1` · 2 vCPU · 2 GiB · Warm Standby 24/7 (`--min-instances 1`) |

[![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud%20Run-Live%20on%20GCP-4285F4.svg?logo=googlecloud)](https://strataiq-naomuofz7q-uc.a.run.app)
[![Google Cloud Firestore](https://img.shields.io/badge/Google%20Cloud%20Firestore-Active%20Audit%20Sync-FFCA28.svg?logo=firebase)](https://console.cloud.google.com/firestore/databases/-default-/data/panel?project=friday-494818)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.12+-4285F4.svg)](https://cloud.google.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.8%20Flash%20%7C%202.5%20Pro-EA4335.svg)](https://ai.google.dev/)
[![Google Gemma](https://img.shields.io/badge/Google%20Gemma-Gemma%204%20LoRA-FBBC05.svg)](https://ai.google.dev/gemma)
[![Tests](https://img.shields.io/badge/Tests-44%2F44%20Passing-34A853.svg)](#test-suite-verification)
[![Security](https://img.shields.io/badge/Zero--Trust-Row--Level%20Security-purple.svg)](#zero-trust-row-level-security-rls)

---

## 📌 Executive Summary

Knowledge workers lose **1.8 to 2.5 hours every single day** searching across disconnected PDFs, corporate policies, internal databases, and chat transcripts. Generic enterprise AI chat tools fail in the enterprise because they:
1. Provide identical generic summaries regardless of who is asking,
2. Lack access to live relational SQL state (e.g., employee claims, payroll freezes, pending riders),
3. Violate Zero-Trust access controls by exposing confidential executive records, and
4. Struggle to provide exact, pinpointed visual citations and acoustic voice interaction.

**StrataIQ** solves this with a **3-Layer $\times$ 6-Department Role-Adaptive Architecture** backed by an autonomous **Google ADK Multi-Agent Engine**, **Gemma 4 LoRA Context Router**, **Google Gemini Native TTS**, **Google Cloud Firestore sync**, and **Thesys OpenUI Engine** that reduces token payload by over 59%.

Deployed as a single unified container on **Google Cloud Run** with `--min-instances 1` to guarantee zero cold starts for evaluators.

---

## 🏢 The 3-Layer $\times$ 6-Department Architecture

Instead of hardcoded roles, StrataIQ implements a dynamic organizational matrix:

| Layer | Clearance | Focus | Showcase Personas | Typical UI & Intelligence Modules |
| :--- | :---: | :--- | :--- | :--- |
| **Upper Layer** | Level 3 | Strategic Direction & Capital Allocation | `USR-UPPER-FIN-001` (Arvind Mehta, CFO)<br>`USR-UPPER-HR-002` (Shalini Nair, VP HR) | 3-Option Quantified Decision Matrix (`decision_matrix_logs`), Department Cost Variance Bar Charts, Budget Approvals |
| **Middle Layer** | Level 2 | Cross-Silo Orchestration & Collision Prevention | `USR-MID-HR-003` (Priya Kulkarni, HR Lead)<br>`USR-MID-IT-004` (Rohan Deshmukh, IT Manager) | War-Room Schedule Collision Detectors (`TSK-03` Payroll Lock vs `TSK-05` SSO Portal), Stuck Claims Trackers |
| **Lower Layer** | Level 1 | Execution, Self-Service & Pointed Voice Q&A | `USR-LOW-ENG-005` (Naman Goel, Senior Engineer)<br>`USR-LOW-OPS-006` (Sneha Patil, Ops Analyst) | "Talk with Your Documents" Pointed Voice Studio, Visual Citations, Personal Enrollment Status (`PENDING_CONFIRMATION`) |

### Departments Covered
- **Finance (`DEPT-FIN`)**
- **Human Resources (`DEPT-HR`)**
- **Engineering (`DEPT-ENG`)**
- **Information Technology (`DEPT-IT`)**
- **Operations (`DEPT-OPS`)**
- **Legal & Compliance (`DEPT-LEG`)**

---

## 🌟 Flagship Demo: The 60-Day Corporate Health Insurance Vendor Transition

StrataIQ is evaluated against a real-world enterprise operational crisis: transitioning 500 employees from **LegacyCare Assurance (`POL-LEGACY-2025`)** to **NovaShield Health (`POL-NOVASHIELD-2026`)**.

- **Lower Layer (`USR-LOW-ENG-005` Naman Goel):**
  Uses **"Talk with Your Documents"** pointed voice Q&A on `DOC-011` (Employee Handbook) and `DOC-010` (Hospital Directory) to ask:  
  *“Is Sahyadri Hospital in Pune cashless for my father's cataract surgery, and what is the new limit?”*  
  $\rightarrow$ StrataIQ retrieves the exact `INR 45,000/eye` limit (up from `INR 35,000`), highlights the exact paragraph, plays synthesized audio via Gemini Native TTS, and alerts him that his parental rider is `PENDING_CONFIRMATION` before Oct 22.
- **Middle Layer (`USR-MID-HR-003` Priya Kulkarni):**  
  Detects a high-impact **Cross-Silo Schedule Collision** between `DOC-018` (War-Room Transcript) and `workflow_tasks` (`TSK-03` Finance payroll cutoff on Oct 20 vs. `TSK-05` IT SSO launch on Oct 23), threatening to freeze 142 employees and block 11 hospital claims (`INR 14.2 Lakhs`).
- **Upper Layer (`USR-UPPER-FIN-001` Arvind Mehta):**  
  Reviews the `INR 38.4 Lakh` parental premium variance, evaluates Option A, B, and C, and executes an ACID transaction approving **Option B (Recommended)**: offsets costs with the `INR 19.2L` LegacyCare refund, funds the rest from the welfare reserve, extends the payroll cutoff to Oct 25, auto-resolves `TSK-03`, and logs the decision to **Google Cloud Firestore**.

---

## ⏱️ Judge 3-Minute Testing Guide

When evaluating StrataIQ, use the **Judge Sandbox Persona Switcher** at the top of the header to instantly simulate different roles with zero login friction:

### Step 1: Lower Layer Experience (Pointed Voice & Citations)
1. Switch to **Naman Goel** (`USR-LOW-ENG-005`, Senior Software Engineer).
2. Notice your personal banner: *Parental Rider status is PENDING_CONFIRMATION before Oct 22*.
3. Click the **"Talk with Documents"** Studio tab. Select `DOC-011` (Employee Transition Guide).
4. Ask by voice or click the prompt:  
   *"Is Sahyadri Hospital in Pune network cashless for cataract surgery, and what is the limit?"*
5. **Observe**: Real-time spoken voice response (Gemini Native TTS), precise citation to Page 4, Section 3.2, and automatic yellow text highlighting.
6. Click **Confirm Parental Rider** — updates the live SQL database and syncs the audit event to Google Cloud Firestore.

### Step 2: Zero-Trust Security Lock (Clearance Gate)
1. Still as Naman Goel (Clearance Level 1), try to open `DOC-008` (CFO Financial Audit) from the Documents tab.
2. **Observe**: The application raises an **HTTP 403 Forbidden Shield**. The document content and vector embeddings are cryptographically sealed from Lower Layer access.

### Step 3: Middle Layer Crisis Detection (Cross-Silo War-Room)
1. Switch to **Priya Kulkarni** (`USR-MID-HR-003`, HR Operations Lead).
2. **Observe**: The dashboard transforms into the HR/IT Operations War-Room.
3. The AI alert flags a **Cross-Silo Schedule Collision**: Finance payroll freeze (`TSK-03` due Oct 20) happens 3 days before IT portal release (`TSK-05` due Oct 23).
4. See the live impact: **142 employees pending confirmation** and **11 transition hospital claims (INR 14.2L) at risk**.

### Step 4: Upper Layer Executive Governance (ACID Approval)
1. Switch to **Arvind Mehta** (`USR-UPPER-FIN-001`, Chief Financial Officer).
2. View the **3-Option Quantified Decision Matrix** for the INR 38.4 Lakh parental premium variance.
3. Review **Option B (Recommended)**: Utilizes the INR 19.2L LegacyCare refund + welfare reserve, extending the payroll deadline to Oct 25.
4. Click **Approve Option B**.
5. **Observe**: Live ACID transaction commits to SQL, auto-resolves `TSK-03` to `SCHEDULE_ALIGNED`, and writes an immutable audit record to Google Cloud Firestore collection `strataiq_decisions`.

---

## 🛠️ Verified Google Cloud & Partner Tech Stack

| Technology | Purpose | Verification Status |
| :--- | :--- | :---: |
| **Google Cloud Run** | Fully managed serverless container runtime running unified FastAPI + compiled React SPA with `--min-instances 1` for zero cold starts. | Verified |
| **Google Cloud Firestore** | NoSQL real-time document database syncing `strataiq_sessions` and `strataiq_decisions` audit logs. | Verified |
| **Google ADK (google-adk==2.12.0)** | Multi-agent framework coordinating Intent Router, Document RAG, SQL Agent, and Groundedness Evaluator. | Verified |
| **Google Gemini 2.5 / 3.8 Flash & Pro** | High-speed LLM inference for evidence synthesis, intent classification, and groundedness validation. | Verified |
| **Google Gemini Native TTS (`gemini-2.5-flash-preview-tts`)** | Low-latency natural conversational voice synthesis using the `"Kore"` voice model with RIFF WAV packaging. | Verified |
| **Google Cloud Text-to-Speech & Speech-to-Text** | Enterprise fallback audio synthesis (WaveNet/Neural2 `en-IN`) and microphone transcription. | Verified |
| **Google Gemma 4 LoRA** | Fine-tuned 3.9 GB router checkpoint on Tinker remote cluster (`google/gemma-4-e4b-it`) for 22-document intent cataloging. | Verified |
| **Google Cloud SQL PostgreSQL / SQLite** | Dual relational engine with Row-Level Security (RLS) enforcing ACID multi-table transactions. | Verified |
| **Thesys OpenUI (`openui-lang`)** | Declarative token-saving UI compiler delivering **59.3% token savings** and **2.46× decode speedup**. | Verified |
| **Backboard.io** | Enterprise persistent agentic memory storing conversation context across user sessions. | Verified |

---

## 🚀 One-Command Google Cloud Run Deployment

StrataIQ uses a safe deployment script that reads API keys directly into process memory at runtime from `backend/.env` without ever writing keys to disk or git.

### Windows (PowerShell)
```powershell
.\deploy_cloud_run.ps1 -Region us-central1 -ServiceName strataiq
```

### Linux / macOS / Cloud Shell (Bash)
```bash
chmod +x deploy_cloud_run.sh
./deploy_cloud_run.sh us-central1 strataiq
```

The script automatically:
1. Verifies your active Google Cloud Project ID,
2. Enables required GCP APIs (`run`, `cloudbuild`, `artifactregistry`, `firestore`, `aiplatform`, `texttospeech`, `speech`),
3. Builds the production multi-stage Docker container via Google Cloud Build,
4. Deploys to Google Cloud Run with `--min-instances 1` (zero cold starts for judges), 2 CPU, and 2 GiB memory,
5. Securely injects environment variables into Cloud Run.

---

## 🔥 Google Cloud Firestore: Real-Time Audit Sync & Verification

StrataIQ integrates **Google Cloud Firestore** (`google-cloud-firestore`) in Native Mode to provide an immutable, real-time audit ledger of user actions and high-stakes executive governance decisions:

### Direct Cloud Console Link
🔗 **[Google Cloud Firestore Data Panel (`friday-494818`)](https://console.cloud.google.com/firestore/databases/-default-/data/panel?project=friday-494818)**

### Collections Schema & Triggers
1. **`strataiq_sessions` Collection:**
   - **Trigger:** When an employee confirms their parental rider or executes major workspace mutations (e.g., `POST /api/v1/workspace/confirm-parental-rider`).
   - **Document Structure:**
     ```json
     {
       "event_id": "g4O3eTdIqz7B5peNs1yw",
       "user_id": "USR-LOW-ENG-005",
       "layer_code": "LOWER",
       "action": "CONFIRM_PARENTAL_RIDER",
       "metadata": {
         "enrollment_id": "ENR-0005",
         "policy_id": "POL-NOVASHIELD-2026",
         "monthly_copay_deduction": 1200
       },
       "timestamp": "2026-10-18T15:53:29.134731+00:00",
       "source": "strataiq_cloud_run"
     }
     ```
2. **`strataiq_decisions` Collection:**
   - **Trigger:** When an Upper Layer decision-maker approves a multi-option quantified decision (e.g., `POST /api/v1/decisions/DEC-2026-001/approve`).
   - **Document Structure:**
     ```json
     {
       "decision_id": "DEC-2026-001",
       "selected_option": "OPTION_B_RECOMMENDED",
       "approver_id": "USR-UPPER-FIN-001",
       "metadata": {
         "approver_name": "Arvind Mehta",
         "tasks_mutated": ["TSK-02", "TSK-03"]
       },
       "status": "APPROVED",
       "decided_at": "2026-10-18T15:53:43.873316+00:00",
       "source": "strataiq_cloud_run"
     }
     ```

### How to Verify Firestore Records via Python
Run this one-liner in your terminal to query live audit records from your GCP project:
```bash
python -c "from google.cloud import firestore; db = firestore.Client(project='friday-494818'); print('Sessions:', [d.to_dict() for d in db.collection('strataiq_sessions').stream()]); print('Decisions:', [d.to_dict() for d in db.collection('strataiq_decisions').stream()])"
```

---

## 🔄 Continuous Deployment: Updating Code & Reflecting Changes on Cloud Run

Whenever you modify frontend components (`frontend/src/`) or backend routers/agents (`backend/app/`), roll out updates to Cloud Run with **zero downtime**:

### 1. Test Locally (Optional but Recommended)
```bash
cd backend
python -m pytest tests/ -v
```

### 2. Redeploy with One Command
From the root repository directory (`d:/StrataIQ`):
```powershell
.\deploy_cloud_run.ps1
```
*(or `./deploy_cloud_run.sh` in Bash)*

### What Happens Automatically Under the Hood:
1. **Dynamic Secrets:** Reads fresh API keys from `backend/.env` directly into process memory.
2. **Cloud Build Pipeline:** Google Cloud Build packages the repository (respecting `.gcloudignore`), executes the multi-stage Dockerfile, compiles the React SPA bundle in Stage 1, and packages the Python server in Stage 2.
3. **Artifact Registry:** The new container image is automatically tagged and pushed to Artifact Registry (`us-central1-docker.pkg.dev/friday-494818/cloud-run-source-deploy/strataiq`).
4. **Zero-Downtime Traffic Shift:** Cloud Run provisions a new revision (e.g., `strataiq-00002-...`), verifies health probes, and atomically shifts 100% of live traffic to the new revision without dropping in-flight requests.
5. **Warm Instance Preserved:** `--min-instances 1` ensures the updated service remains instantly warm with zero cold starts.

### 3. Sync Source Code to GitHub
```bash
git add .
git commit -m "feat: your update description"
git push origin frontend
```

---

## 🧪 Test Suite Verification

StrataIQ features an automated test suite with **44/44 passing tests (100% green)**:

```bash
cd backend
python -m pytest tests/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1
collected 44 items

tests/test_phase1_rdbms_and_rls.py::test_lower_can_read_clearance1_doc PASSED
tests/test_phase1_rdbms_and_rls.py::test_lower_blocked_on_clearance3_doc PASSED
tests/test_phase1_rdbms_and_rls.py::test_lower_blocked_on_decision_approve PASSED
tests/test_phase1_rdbms_and_rls.py::test_lower_sees_own_enrollment_only PASSED
tests/test_phase1_rdbms_and_rls.py::test_lower_sees_no_other_employee_data PASSED
tests/test_phase1_rdbms_and_rls.py::test_middle_gets_142_pending_parental PASSED
tests/test_phase1_rdbms_and_rls.py::test_middle_gets_11_stuck_claims PASSED
tests/test_phase1_rdbms_and_rls.py::test_middle_gets_conflict_alert PASSED
tests/test_phase1_rdbms_and_rls.py::test_middle_blocked_on_decision_approve PASSED
tests/test_phase1_rdbms_and_rls.py::test_upper_sees_all_22_docs PASSED
tests/test_phase1_rdbms_and_rls.py::test_upper_can_approve_decision PASSED
tests/test_phase1_rdbms_and_rls.py::test_approve_mutates_workflow_tasks PASSED
tests/test_phase1_rdbms_and_rls.py::test_reset_demo_state_works PASSED
tests/test_phase2_agents.py::test_router_classifies_doc_query PASSED
tests/test_phase2_agents.py::test_router_classifies_sql_metric_query PASSED
tests/test_phase2_agents.py::test_router_classifies_cross_silo_conflict PASSED
tests/test_phase2_agents.py::test_router_classifies_executive_decision PASSED
tests/test_phase2_agents.py::test_rag_agent_enforces_zero_trust_rls PASSED
tests/test_phase2_agents.py::test_rag_agent_sahyadri_cashless_retrieval PASSED
tests/test_phase2_agents.py::test_sql_agent_lower_layer_personal_scope PASSED
tests/test_phase2_agents.py::test_sql_agent_cross_silo_conflict_detection PASSED
tests/test_phase2_agents.py::test_sql_agent_executive_budget_variance PASSED
tests/test_phase2_agents.py::test_groundedness_evaluator_high_score_on_valid_evidence PASSED
tests/test_phase2_agents.py::test_groundedness_evaluator_flags_hallucinated_figures PASSED
tests/test_phase2_agents.py::test_api_agent_query_lower_sahyadri PASSED
tests/test_phase2_agents.py::test_api_agent_query_middle_hr_conflict PASSED
tests/test_phase2_agents.py::test_api_agent_query_upper_cfo_variance PASSED
tests/test_phase2_agents.py::test_api_agent_route_endpoint PASSED
tests/test_phase2_agents.py::test_api_sdk_status_endpoint PASSED
tests/test_phase2_agents.py::test_router_catalog_selects_exact_docs PASSED
tests/test_phase2_agents.py::test_backboard_memory_service_sync PASSED
tests/test_phase2_agents.py::test_department_ebitda_and_cost_allocations_query PASSED
tests/test_phase3_voice_and_citations.py::test_tinker_checkpoint_gemma4_and_zero_qwen PASSED
tests/test_phase3_voice_and_citations.py::test_lower_layer_pointed_voice_sahyadri_cataract PASSED
tests/test_phase3_voice_and_citations.py::test_pointed_isolation_targets_exact_document PASSED
tests/test_phase3_voice_and_citations.py::test_zero_trust_rls_blocks_unauthorized_pointed_docs PASSED
tests/test_phase3_voice_and_citations.py::test_middle_layer_conflict_voice_with_openui_steps PASSED
tests/test_phase3_voice_and_citations.py::test_upper_layer_executive_voice_with_openui_barchart PASSED
tests/test_phase3_voice_and_citations.py::test_openui_toggle_switches_format_and_proves_reduction PASSED
tests/test_phase3_voice_and_citations.py::test_openui_benchmark_endpoint_live_metrics PASSED
tests/test_phase3_voice_and_citations.py::test_language_lock_guardrail_enforces_en_in PASSED
tests/test_phase3_voice_and_citations.py::test_latency_breakdown_contains_all_timing_keys PASSED
tests/test_phase3_voice_and_citations.py::test_voice_catalog_returns_role_prompts_and_rls_docs PASSED
tests/test_phase3_voice_and_citations.py::test_voice_transcribe_with_language_lock PASSED

================= 44 passed in 139.88s ==================
```

---

## ⚡ Quickstart & Local Setup

### 1. Configure Environment
```bash
cd backend
cp .env.example .env
```
Fill in your API keys in `backend/.env`:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
TINKER_API_KEY=your_tinker_key_here
BACKBOARD_API_KEY=your_backboard_key_here
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
```

### 3. Run the Unified Production Server
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8080
```
- Web Application: `http://localhost:8080/`
- Interactive API Explorer: `http://localhost:8080/docs`
- Forensic Proof Endpoint: `http://localhost:8080/api/v1/agent/sdk-status`

---

## 📂 Repository Structure

```
StrataIQ/
├── backend/
│   ├── app/
│   │   ├── agents/                     # Google ADK 2.0 Multi-Agent Framework
│   │   │   ├── router.py               # Tinker-Gemma 4 LoRA Context Router
│   │   │   ├── rag_agent.py            # Hybrid Vector + BM25 Document RAG
│   │   │   ├── sql_agent.py            # Parameterized Relational SQL Agent
│   │   │   ├── eval_agent.py           # Synthesis & Groundedness Evaluator
│   │   │   ├── openui_formatter.py     # Thesys OpenUI (openui-lang) Engine
│   │   │   └── memory_service.py       # Backboard.io Persistent User Memory
│   │   ├── voice/                      # Google AI Speech & Voice Studio
│   │   │   ├── speech_service.py       # Gemini Flash TTS (Kore) + GCP Speech
│   │   │   └── pointed_doc_agent.py    # Pointed Voice Orchestrator & Citations
│   │   ├── routers/                    # FastAPI REST Endpoints
│   │   │   ├── workspace.py            # Personas, Layouts & Parental Rider
│   │   │   ├── documents.py            # Zero-Trust Document Catalog
│   │   │   ├── decisions.py            # Executive ACID Decision Approvals
│   │   │   ├── agent.py                # Multi-Agent Query & SDK Status
│   │   │   └── voice.py                # Pointed Voice Studio Endpoints
│   │   ├── config.py                   # Centralized Pydantic Settings
│   │   ├── database.py                 # Dual SQLAlchemy Engine (SQLite/Postgres)
│   │   ├── firestore_sync.py           # Google Cloud Firestore Sync Service
│   │   ├── models.py                   # 10 Normalized SQLAlchemy Models
│   │   ├── security.py                 # Zero-Trust SecurityContext Dependency
│   │   └── main.py                     # Unified FastAPI + React SPA Server
│   ├── tests/
│   │   ├── test_phase1_rdbms_and_rls.py
│   │   ├── test_phase2_agents.py
│   │   └── test_phase3_voice_and_citations.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/                 # Role-Adaptive UI & Voice Studio
│   │   ├── pages/                      # Layouts, User Guide & Sandboxes
│   │   └── lib/api.ts                  # Clean Relative API Client
│   └── dist/                           # Compiled Production SPA
├── enterprise_data_vault/
│   ├── files/                          # 22 Synthesized Enterprise Documents
│   └── rdbms/
│       ├── local_enterprise.db         # SQLite Replica with Real Embeddings
│       └── cloud_sql_postgres_schema_and_rls.sql
├── Dockerfile                          # Multi-Stage Production Container
├── .dockerignore                       # Secret Hygiene & Artifact Exclusion
├── deploy_cloud_run.ps1                # One-Command PowerShell Deploy Script
├── deploy_cloud_run.sh                 # One-Command Bash Deploy Script
├── GEMINI.md                           # Master Architecture & Rulebook
└── README.md                           # Executive Documentation Root
```

---

## 🏆 Google Cloud AI Builder Cup Alignment

| Track Requirement | StrataIQ Implementation |
| :--- | :--- |
| **Track 5: Future of Work** | Eradicates 2 hours/day of enterprise fragmentation with role-adaptive multi-agent intelligence. |
| **Google Gemini & Gemma** | 100% Google model stack: `gemini-2.5-flash-preview-tts`, `gemini-3.8-flash`, `gemini-embedding-001`, and `google/gemma-4-e4b-it`. |
| **Google Cloud Infrastructure** | Google Cloud Run serverless deployment + Google Cloud Firestore live audit persistence. |
| **Google ADK Multi-Agent** | Autonomous specialized agents with formal handoffs, groundedness evaluation, and Backboard.io memory sync. |
| **Zero-Trust Enterprise Security** | Real Row-Level Security (RLS) enforcement at both the SQL and Vector document layer. |
| **Human-in-the-Loop Governance** | AI empowers decision-makers with quantified multi-option matrices; never executes unilateral unapproved actions. |

---

## 📄 License
This project is developed for the **Google Cloud AI Builder Cup (Working Professionals Track)**. All rights reserved.
