"""
StrataIQ Phase 3 Test Suite — Real Google AI Voice, Visual Citations & OpenUI Engine
(tests/test_phase3_voice_and_citations.py)

12 Rigorous Verification Tests:
  1. test_tinker_checkpoint_gemma4_and_zero_qwen: Validates checkpoint and zero Qwen policy
  2. test_lower_layer_pointed_voice_sahyadri_cataract: Live voice query, 45,000 limit, WAV audio
  3. test_pointed_isolation_targets_exact_document: Pointing to DOC-014 isolates primary citation
  4. test_zero_trust_rls_blocks_unauthorized_pointed_docs: 403 Forbidden on CL:2/3 for Lower
  5. test_middle_layer_conflict_voice_with_openui_steps: Schedule collision & openui Steps
  6. test_upper_layer_executive_voice_with_openui_barchart: Executive variance & openui BarChart
  7. test_openui_toggle_switches_format_and_proves_reduction: ui_mode toggle & >40% token reduction
  8. test_openui_benchmark_endpoint_live_metrics: POST /api/v1/agent/benchmark-openui
  9. test_language_lock_guardrail_enforces_en_in: 'fr-FR' force-locks to 'en-IN'
  10. test_latency_breakdown_contains_all_timing_keys: Millisecond audit across 6 stages
  11. test_voice_catalog_returns_role_prompts_and_rls_docs: GET /api/v1/voice/catalog
  12. test_voice_transcribe_with_language_lock: POST /api/v1/voice/transcribe
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Standard personas
LOWER_USER = "USR-LOW-ENG-005"   # Naman Goel (Engineering, Clearance 1)
MIDDLE_USER = "USR-MID-HR-003"   # Priya Kulkarni (HR Lead, Clearance 2)
UPPER_USER = "USR-UPPER-FIN-001" # Arvind Mehta (CFO, Clearance 3)


# ── Test 1: Tinker Checkpoint Targets Gemma 4 & Zero Qwen Invariant ───────────
def test_tinker_checkpoint_gemma4_and_zero_qwen():
    ckpt_path = Path(__file__).resolve().parent.parent / "app" / "agents" / "tinker_checkpoint.json"
    assert ckpt_path.exists(), "tinker_checkpoint.json must exist in app/agents/"

    with open(ckpt_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("status") == "trained"
    assert data.get("target_model") == "google/gemma-4-e4b-it"
    assert data.get("tinker_checkpoint_path", "").startswith("tinker://")
    assert data.get("steps_completed", 0) >= 3

    # Scan entire app directory for any Qwen string
    app_dir = Path(__file__).resolve().parent.parent / "app"
    for p in app_dir.rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        assert "qwen" not in text.lower(), f"Forbidden 'Qwen' reference discovered in {p}"


# ── Test 2: Lower-Layer Pointed Voice Query on Sahyadri Cataract Surgery ──────
def test_lower_layer_pointed_voice_sahyadri_cataract():
    payload = {
        "query": "Is Sahyadri Hospital in Pune cashless for my father's cataract surgery under NovaShield?",
        "pointed_doc_ids": ["DOC-011", "DOC-010"],
        "language_code": "en-IN",
        "voice_speed": 1.0,
        "ui_mode": "openui",
    }
    response = client.post(
        "/api/v1/voice/talk-to-docs",
        json=payload,
        headers={"X-User-Id": LOWER_USER},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    # Clinical & financial accuracy assertions
    answer_text = (data["display_answer"] + " " + data["spoken_answer"]).lower()
    assert "sahyadri" in answer_text
    assert "45,000" in answer_text or "45000" in answer_text
    assert "pending" in answer_text and "confirmation" in answer_text

    # Citation assertions
    assert data["primary_citation"] is not None
    assert data["primary_citation"]["doc_id"] in ["DOC-010", "DOC-011"]
    assert len(data["primary_citation"]["highlight_snippet"]) > 10

    # Groundedness & Audio assertions
    assert data["groundedness_score"] >= 0.80
    assert data["is_grounded"] is True
    assert len(data["audio_base64"]) > 1000
    assert data["audio_content_type"] == "audio/wav"
    assert data["tts_engine"] in [
        "google_gemini_2.5_flash_tts_kore",
        "gcp_chirp3_hd_or_wavenet",
        "local_wav_with_web_speech_fallback",
    ]


# ── Test 3: Pointed Isolation Targets Exact Document ──────────────────────────
def test_pointed_isolation_targets_exact_document():
    payload = {
        "query": "What is the single sign-on API architecture specification?",
        "pointed_doc_ids": ["DOC-014"],
        "ui_mode": "openui",
    }
    response = client.post(
        "/api/v1/voice/talk-to-docs",
        json=payload,
        headers={"X-User-Id": LOWER_USER},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["primary_citation"]["doc_id"] == "DOC-014"
    assert "14_HRMS_to_NovaShield_API_SSO_Architecture_Spec.pdf" in data["primary_citation"]["file_name"]


# ── Test 4: Zero-Trust RLS Blocks Unauthorized Pointed Documents ───────────────
def test_zero_trust_rls_blocks_unauthorized_pointed_docs():
    # USR-LOW-ENG-005 (CL:1) trying to access DOC-008 (CL:3) or DOC-002 (CL:2)
    forbidden_docs = [["DOC-008"], ["DOC-002"], ["DOC-005", "DOC-011"]]
    for f_docs in forbidden_docs:
        payload = {
            "query": "Tell me about executive budget allocations.",
            "pointed_doc_ids": f_docs,
        }
        response = client.post(
            "/api/v1/voice/talk-to-docs",
            json=payload,
            headers={"X-User-Id": LOWER_USER},
        )
        assert response.status_code == 403, f"Expected 403 for {f_docs}, got {response.status_code}"
        assert "Zero-Trust Access Denied" in response.json()["detail"]


# ── Test 5: Middle-Layer Conflict Voice Query with OpenUI Steps ────────────────
def test_middle_layer_conflict_voice_with_openui_steps():
    payload = {
        "query": "Detect cross-silo schedule collisions between Finance payroll cutoff and IT SSO launch",
        "pointed_doc_ids": ["DOC-018", "DOC-016"],
        "ui_mode": "openui",
    }
    response = client.post(
        "/api/v1/voice/talk-to-docs",
        json=payload,
        headers={"X-User-Id": MIDDLE_USER},
    )
    assert response.status_code == 200
    data = response.json()

    ans = (data["display_answer"] + " " + data["spoken_answer"]).lower()
    assert "tsk-03" in ans
    assert "tsk-05" in ans
    assert "142" in ans

    # OpenUI syntax check
    openui = data["openui_lang"]
    assert "Steps(" in openui
    assert "TSK-03" in openui
    assert "Table(" in openui


# ── Test 6: Upper-Layer Executive Voice Query with OpenUI BarChart ─────────────
def test_upper_layer_executive_voice_with_openui_barchart():
    payload = {
        "query": "What is the unbudgeted parental premium variance and how does Option B resolve it?",
        "pointed_doc_ids": ["DOC-008", "DOC-005"],
        "ui_mode": "openui",
    }
    response = client.post(
        "/api/v1/voice/talk-to-docs",
        json=payload,
        headers={"X-User-Id": UPPER_USER},
    )
    assert response.status_code == 200
    data = response.json()

    ans = (data["display_answer"] + " " + data["spoken_answer"]).lower()
    assert "38.4" in ans or "3840000" in ans
    assert "option b" in ans

    # OpenUI syntax check
    openui = data["openui_lang"]
    assert "BarChart(" in openui
    assert "Executive Decision Matrix" in openui
    assert "Option B (Recommended)" in openui


# ── Test 7: OpenUI ON vs OFF Toggle Test & Token Reduction > 40% ──────────────
def test_openui_toggle_switches_format_and_proves_reduction():
    # 1. Voice endpoint with openui
    res_on = client.post(
        "/api/v1/voice/talk-to-docs",
        json={"query": "Is Sahyadri hospital cashless?", "pointed_doc_ids": ["DOC-010"], "ui_mode": "openui"},
        headers={"X-User-Id": LOWER_USER},
    )
    assert res_on.status_code == 200
    data_on = res_on.json()
    assert data_on["openui_telemetry"]["active_ui_mode"] == "openui"
    assert data_on["openui_lang"].startswith("header = Header(")
    assert data_on["openui_telemetry"]["token_reduction_pct"] > 40.0

    # 2. Voice endpoint with legacy
    res_off = client.post(
        "/api/v1/voice/talk-to-docs",
        json={"query": "Is Sahyadri hospital cashless?", "pointed_doc_ids": ["DOC-010"], "ui_mode": "legacy"},
        headers={"X-User-Id": LOWER_USER},
    )
    assert res_off.status_code == 200
    data_off = res_off.json()
    assert data_off["openui_telemetry"]["active_ui_mode"] == "legacy"
    assert "schema_version" in data_off["openui_lang"]

    # 3. Agent query endpoint toggle
    agent_on = client.post(
        "/api/v1/agent/query",
        json={"query": "What are my parental copay deductions?", "ui_mode": "openui"},
        headers={"X-User-Id": LOWER_USER},
    )
    assert agent_on.status_code == 200
    assert agent_on.json()["openui_telemetry"]["token_reduction_pct"] > 40.0


# ── Test 8: Live OpenUI Benchmark Endpoint Metrics ────────────────────────────
def test_openui_benchmark_endpoint_live_metrics():
    payload = {
        "query": "Is there a conflict between TSK-03 and TSK-05?",
        "doc_hints": ["DOC-018"],
    }
    response = client.post(
        "/api/v1/agent/benchmark-openui",
        json=payload,
        headers={"X-User-Id": MIDDLE_USER},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["token_reduction_pct"] > 40.0
    assert data["speedup_multiplier"] >= 1.5
    assert data["openui_tokens"] < data["legacy_tokens"]
    assert data["estimated_llm_decode_saved_ms"] > 1000
    assert "Steps(" in data["openui_lang_code"]
    assert "schema_version" in data["legacy_verbose_payload"]


# ── Test 9: Language Lock Guardrail Enforces en-IN ─────────────────────────────
def test_language_lock_guardrail_enforces_en_in():
    # Pass unsupported language (e.g., 'fr-FR' or 'es-ES')
    payload = {
        "query": "Is Sahyadri Hospital cashless?",
        "pointed_doc_ids": ["DOC-010"],
        "language_code": "fr-FR",
    }
    response = client.post(
        "/api/v1/voice/talk-to-docs",
        json=payload,
        headers={"X-User-Id": LOWER_USER},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["language_code"] == "en-IN"
    assert data["language_lock_enforced"] is True


# ── Test 10: Latency Breakdown Contains All 6 Timing Keys ──────────────────────
def test_latency_breakdown_contains_all_timing_keys():
    payload = {
        "query": "Where can I find pre-authorization guidelines?",
        "pointed_doc_ids": ["DOC-011"],
    }
    response = client.post(
        "/api/v1/voice/talk-to-docs",
        json=payload,
        headers={"X-User-Id": LOWER_USER},
    )
    assert response.status_code == 200
    latencies = response.json()["latency_breakdown_ms"]

    required_keys = [
        "rls_validation_ms",
        "pointed_vector_rag_ms",
        "sql_context_ms",
        "synthesis_eval_ms",
        "tts_synthesis_ms",
        "total_ms",
    ]
    for k in required_keys:
        assert k in latencies
        assert isinstance(latencies[k], (int, float))
        assert latencies[k] >= 0.0


# ── Test 11: Voice Catalog Returns Role Prompts and RLS Documents ─────────────
def test_voice_catalog_returns_role_prompts_and_rls_docs():
    # 1. Lower Layer
    res_low = client.get("/api/v1/voice/catalog", headers={"X-User-Id": LOWER_USER})
    assert res_low.status_code == 200
    data_low = res_low.json()
    assert data_low["user_clearance_level"] == 1
    # Check max clearance of accessible docs
    assert all(d["min_layer_clearance"] <= 1 for d in data_low["accessible_documents"])
    assert any("Sahyadri" in p["title"] for p in data_low["sample_voice_prompts"])

    # 2. Upper Layer
    res_up = client.get("/api/v1/voice/catalog", headers={"X-User-Id": UPPER_USER})
    assert res_up.status_code == 200
    data_up = res_up.json()
    assert data_up["user_clearance_level"] == 3
    assert len(data_up["accessible_documents"]) == 22
    assert any("Parental Premium" in p["title"] for p in data_up["sample_voice_prompts"])


# ── Test 12: Voice Transcribe with Language Lock ──────────────────────────────
def test_voice_transcribe_with_language_lock():
    # Test fallback transcription with language lock
    payload = {
        "fallback_text": "Is Sahyadri Hospital in Pune network cashless under NovaShield?",
        "language_code": "de-DE",
    }
    response = client.post(
        "/api/v1/voice/transcribe",
        json=payload,
        headers={"X-User-Id": LOWER_USER},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["transcription"] == payload["fallback_text"]
    assert data["language_code"] == "en-IN"
    assert data["language_lock_enforced"] is True
    assert data["confidence"] > 0.9
