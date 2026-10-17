# StrataIQ 🧠🎙️

> **Role-Adaptive Enterprise Knowledge, Voice & Decision Copilot**  
> *Google Cloud AI Builder Cup — Track 5: Future of Work & Enterprise Productivity*

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0+-009688.svg)](https://fastapi.tiangolo.com/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.12+-4285F4.svg)](https://cloud.google.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.8%20Flash%20%7C%202.5%20Pro-EA4335.svg)](https://ai.google.dev/)
[![Google Gemma](https://img.shields.io/badge/Google%20Gemma-Gemma%204%20LoRA-FBBC05.svg)](https://ai.google.dev/gemma)
[![Tests](https://img.shields.io/badge/Tests-43%2F43%20Passing-34A853.svg)](#test-suite-verification)
[![Security](https://img.shields.io/badge/Zero--Trust-Row--Level%20Security-purple.svg)](#zero-trust-row-level-security-rls)

---

## 📌 Executive Summary

Knowledge workers lose **1.8 to 2.5 hours every single day** searching across disconnected PDFs, corporate policies, internal databases, and chat transcripts. Generic enterprise AI chat tools fail in the enterprise because they:
1. Provide identical generic summaries regardless of who is asking,
2. Lack access to live relational SQL state (e.g. employee claims, payroll freezes, pending riders),
3. Violate Zero-Trust access controls by hallucinating or exposing confidential executive data, and
4. Struggle to provide exact, pinpointed visual citations and acoustic voice interaction.

**StrataIQ** solves this with a **3-Layer $\times$ 6-Department Role-Adaptive Architecture** backed by an autonomous **Google ADK Multi-Agent Engine**, **Gemma 4 LoRA Context Router**, **Google Gemini Native TTS**, and **Thesys OpenUI Engine** that reduces token payload by over 59%.

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
  Reviews the `INR 38.4 Lakh` parental premium variance, evaluates Option A, B, and C, and executes an ACID transaction approving **Option B (Recommended)**: offsets costs with the `INR 19.2L` LegacyCare refund, funds the rest from the welfare reserve, extends the payroll cutoff to Oct 25, and auto-resolves `TSK-03`.

---

## 🤖 100% Google Model & Agent Pipeline

StrataIQ strictly adheres to a **100% Google Model Policy** (Google Gemma 4 + Gemini 2.5 / 3.8):

```
                        User Voice / Text Query
                                   │
                                   ▼
             ┌───────────────────────────────────────────┐
             │    Tinker-Gemma 4 LoRA Context Router    │
             │   (google/gemma-4-e4b-it / Gemini Flash)  │
             └─────────────────────┬─────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
      ┌───────────────────────────┐ ┌───────────────────────────┐
      │     Document RAG Agent    │ │   Relational SQL Agent    │
      │   (Hybrid Vector + BM25)  │ │ (Row-Level Security RLS)  │
      │ 3072-dim Google Embeddings│ │ 10-Table Dual DB Engine   │
      └─────────────┬─────────────┘ └─────────────┬─────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
             ┌───────────────────────────────────────────┐
             │       Google ADK 2.0 Synthesis Agent      │
             │     & Groundedness Verification Evaluator │
             │           (Deterministic + LLM)           │
             └─────────────────────┬─────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
      ┌───────────────────────────┐ ┌───────────────────────────┐
      │ Google AI Speech Service  │ │  Thesys OpenUI Formatter  │
      │  Gemini Flash TTS (Kore)  │ │  (openui-lang ON/OFF)     │
      │  Chirp 3 HD / WaveNet     │ │  >59% Token Reduction     │
      └───────────────────────────┘ └───────────────────────────┘
```

1. **Tinker-Gemma 4 LoRA Router (`backend/app/agents/router.py`)**:
   - Fine-tuned on Tinker remote cluster (`google/gemma-4-e4b-it`) targeting intent classification and pointed-document filtering across 22 enterprise documents.
2. **Document RAG Agent (`backend/app/agents/rag_agent.py`)**:
   - Hybrid Vector (`text-embedding-004` / 3072-dim embeddings) + BM25 keyword matching with strict clearance-level enforcement.
3. **Relational SQL Agent (`backend/app/agents/sql_agent.py`)**:
   - Parameterized SQL engine executing queries against 10 relational tables (`users`, `documents`, `policies`, `enrollments`, `claims`, `workflow_tasks`, `decision_matrix_logs`, etc.).
4. **Synthesis & Groundedness Evaluator (`backend/app/agents/eval_agent.py`)**:
   - Scores responses ($0.0$ to $1.0$) against retrieved doc/SQL evidence to eliminate hallucinations before delivery.
5. **Google AI Speech Service (`backend/app/voice/speech_service.py`)**:
   - Tier 1: **Google Gemini Native TTS** (`gemini-2.5-flash-preview-tts` with voice `"Kore"`, 24kHz PCM $\rightarrow$ standard RIFF WAV base64).
   - Tier 2: **Google Cloud Text-to-Speech** (Chirp 3 HD / WaveNet `en-IN`).
   - Strict `en-IN` language lock guardrail and natural speech cleaner (`INR` $\rightarrow$ `Rupees`).
6. **Thesys OpenUI (`openui-lang`) Engine (`backend/app/agents/openui_formatter.py`)**:
   - Declarative UI generation (`identifier = Component(...)`) producing rich role-tailored components.
   - Built-in live ON/OFF toggle and telemetry benchmark proving **59.3% token reduction** and **2.46× decode speedup**.

---

## 🔒 Zero-Trust Row-Level Security (RLS)

Every API request passes through a mandatory `SecurityContext` dependency:
- The user's clearance level (`1`, `2`, `3`) is validated against document `min_layer_clearance`.
- **Immediate Rejection**: If an employee requests or points to ANY document above their clearance level (e.g. Lower Layer user requesting `DOC-008` CFO Financial Audit), the API immediately raises `403 Forbidden` before executing RAG or LLM synthesis.
- Relational queries are automatically scoped (e.g., Lower Layer employees can strictly view their own `enrollment` record; Middle Layer HR leads can view department-wide pending lists).

---

## 🧪 Test Suite Verification

StrataIQ features an automated test suite with **43/43 passing tests (100% green)**:

```bash
cd backend
python -m pytest tests/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1
collected 43 items

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

================= 43 passed, 12 warnings in 89.05s ==================
```

---

## ⚡ Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11+
- Google Cloud Project with Gemini API Key (`GEMINI_API_KEY`)

### 2. Environment Configuration
```bash
cd backend
cp .env.example .env
```
Fill in your `GEMINI_API_KEY` (and optionally `TINKER_API_KEY`, `BACKBOARD_API_KEY`):
```ini
GEMINI_API_KEY=your_gemini_api_key_here
TINKER_BASE_MODEL=google/gemma-4-e4b-it
GOOGLE_GEMMA_ROUTER_MODEL=gemma-4-e4b-it
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Backend Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation is available live at `http://localhost:8000/docs`.

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
│   │   │   └── tinker_checkpoint.json  # Gemma 4 LoRA Checkpoint Metadata
│   │   ├── voice/                      # Google AI Speech & Voice Studio
│   │   │   ├── speech_service.py       # Gemini Flash TTS (Kore) + GCP Speech
│   │   │   └── pointed_doc_agent.py    # Pointed Voice Orchestrator & Citations
│   │   ├── routers/                    # FastAPI REST Endpoints
│   │   │   ├── workspace.py            # Personas & Demo State Management
│   │   │   ├── documents.py            # Zero-Trust Document Catalog
│   │   │   ├── decisions.py            # Executive ACID Decision Approvals
│   │   │   ├── agent.py                # Multi-Agent Query & OpenUI Benchmark
│   │   │   └── voice.py                # Pointed Voice Studio Endpoints
│   │   ├── config.py                   # Centralized Pydantic Settings
│   │   ├── database.py                 # Dual SQLAlchemy Engine (SQLite/Postgres)
│   │   ├── models.py                   # 10 Normalized SQLAlchemy Models
│   │   ├── security.py                 # Zero-Trust SecurityContext Dependency
│   │   └── main.py                     # FastAPI Application Factory & CORS
│   ├── scripts/
│   │   └── train_tinker_router.py      # Tinker Gemma 4 LoRA Fine-Tuning Script
│   ├── tests/
│   │   ├── test_phase1_rdbms_and_rls.py
│   │   ├── test_phase2_agents.py
│   │   └── test_phase3_voice_and_citations.py
│   ├── requirements.txt
│   └── .env.example
├── enterprise_data_vault/
│   ├── files/                          # 22 Synthesized Enterprise Documents
│   └── rdbms/
│       ├── local_enterprise.db         # SQLite Replica with Real Embeddings
│       └── cloud_sql_postgres_schema_and_rls.sql
├── dataSeed.py                         # Enterprise Database Seeder
├── GEMINI.md                           # Master Architecture & Rulebook
└── README.md                           # Documentation Root
```

---

## 🏆 Google Cloud AI Builder Cup Alignment

| Track Requirement | StrataIQ Implementation |
| :--- | :--- |
| **Track 5: Future of Work** | Eradicates 2 hours/day of enterprise fragmentation with role-adaptive multi-agent intelligence. |
| **Google Gemini & Gemma** | 100% Google model stack: `gemini-2.5-flash-preview-tts`, `gemini-3.8-flash`, `text-embedding-004`, and `google/gemma-4-e4b-it`. |
| **Google ADK Multi-Agent** | Autonomous specialized agents with formal handoffs, groundedness evaluation, and Backboard.io memory sync. |
| **Zero-Trust Enterprise Security** | Real Row-Level Security (RLS) enforcement at both the SQL and Vector document layer. |
| **Human-in-the-Loop Governance** | AI empowers decision-makers with quantified multi-option matrices; never executes unilateral unapproved actions. |

---

## 📄 License
This project is developed for the **Google Cloud AI Builder Cup (Working Professionals Track)**. All rights reserved.
