"""
StrataIQ Phase 2 Pytest Suite — Multi-Agent Engine, Hybrid Vector/SQL RAG & Groundedness Evals

Tests:
  1. IntentRouter classifications (DOC_QUERY, SQL_METRIC_QUERY, CROSS_SILO_CONFLICT, EXECUTIVE_DECISION)
  2. Zero-Trust RLS enforcement in DocumentRAGAgent (Clearance 1 blocked from Clearance 2/3 chunks)
  3. Sahyadri Hospital & Cataract Limit retrieval (DOC-010, DOC-019, DOC-021)
  4. RelationalSQLAgent personal status scoping for Lower Layer (no leakage of peer data)
  5. RelationalSQLAgent cross-silo conflict detection (TSK-03 vs TSK-05, 142 blocked, 12 stuck claims)
  6. RelationalSQLAgent executive variance & Option B metrics (INR 38.4L variance, INR 19.2L refund)
  7. GroundednessEvaluator verification & scoring (>= 0.80 threshold)
  8. GroundednessEvaluator hallucination detection & penalty
  9. End-to-End API /api/v1/agent/query for Lower layer (Naman Goel - Sahyadri cataract inquiry)
 10. End-to-End API /api/v1/agent/query for Middle HR (Priya Kulkarni - conflict & blocked enrollments)
 11. End-to-End API /api/v1/agent/query for Upper CFO (Arvind Mehta - variance & Option B approval)
 12. Fast routing endpoint /api/v1/agent/route
"""
import pytest
from fastapi.testclient import TestClient

from app.agents.eval_agent import GroundednessEvaluator, SynthesisAgent
from app.agents.rag_agent import DocumentRAGAgent, RAGResult
from app.agents.router import (
    INTENT_CROSS_SILO,
    INTENT_DOC_QUERY,
    INTENT_EXEC_DECISION,
    INTENT_SQL_METRIC,
    IntentRouter,
)
from app.agents.sql_agent import RelationalSQLAgent, SQLResult
from app.database import SessionLocal, get_security_context


# ── Fixtures & Helpers ────────────────────────────────────────────────────────

def get_context_for(user_id: str):
    """Helper to obtain SecurityContext directly for unit tests."""
    db = SessionLocal()
    try:
        return get_security_context(x_user_id=user_id, db=db)
    finally:
        db.close()


# ── 1. Intent Router Tests ─────────────────────────────────────────────────────

def test_router_classifies_doc_query():
    router = IntentRouter()
    ctx = get_context_for("USR-LOW-ENG-005")  # Lower
    res = router.classify("Is Sahyadri Hospital cashless for cataract surgery under NovaShield?", ctx)
    assert res.intent == INTENT_DOC_QUERY
    assert any("hospital" in kw.lower() or "cataract" in kw.lower() or "sahyadri" in kw.lower() for kw in res.keywords)
    assert len(res.doc_hints) > 0


def test_router_classifies_sql_metric_query():
    router = IntentRouter()
    ctx = get_context_for("USR-MID-HR-003")  # Middle HR
    res = router.classify("How many employees have pending confirmation status for parental opt-in?", ctx)
    assert res.intent == INTENT_SQL_METRIC
    assert "employee_enrollments" in res.sql_hints or len(res.sql_hints) > 0


def test_router_classifies_cross_silo_conflict():
    router = IntentRouter()
    ctx = get_context_for("USR-MID-HR-003")  # Middle HR
    res = router.classify("Is there a schedule conflict between TSK-03 payroll lock and TSK-05 SSO portal launch?", ctx)
    assert res.intent == INTENT_CROSS_SILO
    assert "workflow_tasks" in res.sql_hints


def test_router_classifies_executive_decision():
    router = IntentRouter()
    ctx = get_context_for("USR-UPPER-FIN-001")  # Upper CFO
    res = router.classify("What is the financial impact of Option B for the DEC-2026-001 parental premium variance?", ctx)
    assert res.intent == INTENT_EXEC_DECISION
    assert "decision_matrix_logs" in res.sql_hints


# ── 2. Zero-Trust Document RAG Agent Tests ────────────────────────────────────

def test_rag_agent_enforces_zero_trust_rls():
    """Lower clearance (1) must NEVER receive chunks from clearance 2 or clearance 3 documents."""
    agent = DocumentRAGAgent()
    db = SessionLocal()
    try:
        lower_ctx = get_context_for("USR-LOW-ENG-005")  # Clearance 1
        results = agent.search(
            query="transition claims audit and confidential board budget approval",
            ctx=lower_ctx,
            db=db,
            top_k=10,
        )
        # All returned chunks must strictly come from documents with min_layer_clearance <= 1
        for r in results:
            # DOC-005, DOC-007, DOC-008 are clearance 2 or 3
            assert r.doc_id not in ("DOC-005", "DOC-007", "DOC-008"), (
                f"Security breach: Clearance 1 user received chunk from {r.doc_id}"
            )
    finally:
        db.close()


def test_rag_agent_sahyadri_cashless_retrieval():
    """Search for Sahyadri Hospital returns relevant network hospital chunks."""
    agent = DocumentRAGAgent()
    db = SessionLocal()
    try:
        lower_ctx = get_context_for("USR-LOW-ENG-005")
        results = agent.search(
            query="Is Sahyadri Hospital in Pune cashless for cataract treatment?",
            ctx=lower_ctx,
            db=db,
            top_k=5,
        )
        assert len(results) > 0
        doc_ids = [r.doc_id for r in results]
        # Should include network list DOC-010 or Pune coverage DOC-019 or benefit schedule DOC-021
        assert any(d in doc_ids for d in ("DOC-010", "DOC-019", "DOC-021")), (
            f"Expected DOC-010, DOC-019 or DOC-021 in results, got: {doc_ids}"
        )
    finally:
        db.close()


# ── 3. Relational SQL Agent Tests ──────────────────────────────────────────────

def test_sql_agent_lower_layer_personal_scope():
    """Lower layer user only gets their own records and no other employee's private details."""
    agent = RelationalSQLAgent()
    db = SessionLocal()
    try:
        ctx = get_context_for("USR-LOW-ENG-005")
        res = agent.run_query("What is my current parental opt-in status and copay deduction?", ctx, db)
        assert res.query_type == "PERSONAL_ENROLLMENT_STATUS"
        assert res.metrics["user_id"] == "USR-LOW-ENG-005"
        assert "sum_insured_inr" in res.metrics
        assert "parental_opt_in" in res.metrics
        # Must not expose 500 records
        assert res.row_count <= 5
    finally:
        db.close()


def test_sql_agent_cross_silo_conflict_detection():
    """Middle layer HR detects the TSK-03 vs TSK-05 collision with exact numbers."""
    agent = RelationalSQLAgent()
    db = SessionLocal()
    try:
        ctx = get_context_for("USR-MID-HR-003")
        res = agent.run_query("Detect schedule conflict between Finance payroll lock and IT SSO launch", ctx, db)
        assert res.query_type == "CROSS_SILO_CONFLICT"
        assert res.metrics["blocked_employees"] == 142
        assert res.metrics["stuck_claims_count"] == 12
        assert res.metrics["stuck_claims_amount_inr"] == 1465000.0
        assert "TSK-03" in res.summary and "TSK-05" in res.summary
    finally:
        db.close()


def test_sql_agent_executive_budget_variance():
    """Upper CFO query retrieves unbudgeted parental premium variance and Option B."""
    agent = RelationalSQLAgent()
    db = SessionLocal()
    try:
        ctx = get_context_for("USR-UPPER-FIN-001")
        res = agent.run_query("What is the parental premium variance and Option B financial impact?", ctx, db)
        assert res.query_type == "EXECUTIVE_DECISION_MATRIX"
        assert res.metrics["parental_premium_variance_inr"] == 3840000.0
        assert res.metrics["legacycare_refund_inr"] == 1920000.0
        assert "DEC-2026-001" in res.summary
    finally:
        db.close()


# ── 4. Groundedness Evaluation Tests ──────────────────────────────────────────

def test_groundedness_evaluator_high_score_on_valid_evidence():
    """Groundedness score is >= 0.80 and is_grounded is True when facts match evidence."""
    evaluator = GroundednessEvaluator()
    rag_results = [
        RAGResult(
            chunk_id="chk-1",
            doc_id="DOC-021",
            file_name="DOC-021-NovaShield-Benefit-Schedule.pdf",
            file_type="pdf",
            page_number=3,
            section_title="Cataract & Daycare Sublimits",
            chunk_text="Under NovaShield Health, the cataract surgery sublimit is upgraded to INR 45,000 per eye. Sahyadri Hospital in Pune is an active cashless network provider.",
            relevance_score=0.92,
        )
    ]
    sql_result = SQLResult(
        query_type="PERSONAL_ENROLLMENT_STATUS",
        sql_query="SELECT * FROM employee_enrollments",
        rows=[{"parental_opt_in": "PENDING_CONFIRMATION"}],
        summary="Employee parental opt-in is PENDING_CONFIRMATION.",
        metrics={"parental_opt_in": "PENDING_CONFIRMATION"},
    )
    answer = (
        "Under NovaShield Health, Sahyadri Hospital in Pune provides cashless cataract treatment "
        "with an upgraded sublimit of INR 45,000 per eye. Your parental opt-in is currently PENDING_CONFIRMATION."
    )
    result = evaluator.evaluate(answer, rag_results, sql_result)
    assert result.groundedness_score >= 0.80
    assert result.is_grounded is True
    assert result.hallucination_detected is False


def test_groundedness_evaluator_flags_hallucinated_figures():
    """Groundedness evaluator penalizes made-up amounts or fake hospital names."""
    evaluator = GroundednessEvaluator()
    rag_results = [
        RAGResult(
            chunk_id="chk-1",
            doc_id="DOC-021",
            file_name="DOC-021-NovaShield-Benefit-Schedule.pdf",
            file_type="pdf",
            page_number=3,
            section_title="Cataract & Daycare Sublimits",
            chunk_text="Cataract surgery sublimit is INR 45,000 per eye at Sahyadri Hospital Pune.",
            relevance_score=0.92,
        )
    ]
    # Answer cites fabricated hospital and bogus amount not in evidence
    hallucinated_answer = (
        "Under Apollo Hospital in Delhi, the cataract coverage is INR 99,999,999 per eye on Dec 31."
    )
    result = evaluator.evaluate(hallucinated_answer, rag_results, None)
    # The score should be penalized and hallucination flagged
    assert (
        result.hallucination_detected is True
        or result.is_grounded is False
        or result.groundedness_score < 0.50
        or len(result.unverified_claims) > 0
    )


# ── 5. End-to-End REST API /api/v1/agent/query Tests ─────────────────────────

def test_api_agent_query_lower_sahyadri(lower_client: TestClient):
    """Lower layer user asks about Sahyadri cashless cataract surgery."""
    resp = lower_client.post(
        "/api/v1/agent/query",
        json={"query": "Is Sahyadri Hospital in Pune cashless for cataract surgery and what is the limit?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in (INTENT_DOC_QUERY, INTENT_SQL_METRIC)
    assert "Sahyadri" in data["answer"]
    assert "45,000" in data["answer"]
    assert data["groundedness_score"] >= 0.80
    assert data["is_grounded"] is True
    assert len(data["citations"]) > 0
    assert data["user_context"]["user_id"] == "USR-LOW-ENG-005"


def test_api_agent_query_middle_hr_conflict(middle_hr_client: TestClient):
    """Middle HR lead queries the schedule conflict blocking employees."""
    resp = middle_hr_client.post(
        "/api/v1/agent/query",
        json={"query": "Is there a conflict between TSK-03 and TSK-05 blocking employees?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == INTENT_CROSS_SILO
    assert "TSK-03" in data["answer"]
    assert "TSK-05" in data["answer"]
    assert "142" in data["answer"]
    assert data["groundedness_score"] >= 0.80
    assert data["sql_data"] is not None
    assert data["sql_data"]["metrics"]["blocked_employees"] == 142


def test_api_agent_query_upper_cfo_variance(upper_cfo_client: TestClient):
    """Upper CFO queries parental premium variance and Option B."""
    resp = upper_cfo_client.post(
        "/api/v1/agent/query",
        json={"query": "What is the unbudgeted parental premium variance and how does Option B solve it?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == INTENT_EXEC_DECISION
    assert "38.4" in data["answer"] or "3,840,000" in data["answer"]
    assert "Option B" in data["answer"]
    assert data["groundedness_score"] >= 0.80
    assert data["sql_data"] is not None


def test_api_agent_route_endpoint(lower_client: TestClient):
    """Fast intent classification endpoint returns valid routing schema."""
    resp = lower_client.post(
        "/api/v1/agent/route",
        json={"query": "What documents describe the cashless hospitalization process?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == INTENT_DOC_QUERY
    assert isinstance(data["keywords"], list)
    assert isinstance(data["doc_hints"], list)


def test_api_sdk_status_endpoint(lower_client: TestClient):
    """Proof endpoint returns real package versions and 3072-dim embeddings count."""
    resp = lower_client.get("/api/v1/agent/sdk-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"
    assert data["google_adk_version"] == "2.12.0"
    assert data["tinker_version"] == "0.33.1"
    assert data["backboard_sdk_version"] == "1.5.19"
    assert data["embedded_chunks_count"] == 44
    assert data["total_chunks_count"] == 44
    assert data["embedding_dimension"] == 3072
    assert data["embedding_model"] == "gemini-embedding-001"
    assert data["providers"]["gemini_api_key_configured"] is True
    assert data["providers"]["tinker_api_key_configured"] is True
    assert data["providers"]["backboard_api_key_configured"] is True


def test_router_catalog_selects_exact_docs():
    """Tinker/Gemini router selects exact doc IDs from 22-document catalog."""
    router = IntentRouter()
    ctx = get_context_for("USR-LOW-ENG-005")
    res = router.classify("Is Sahyadri Hospital in Pune cashless for cataract surgery?", ctx)
    assert res.intent == INTENT_DOC_QUERY
    assert any(d in res.doc_hints for d in ("DOC-010", "DOC-011", "DOC-019", "DOC-021"))


def test_backboard_memory_service_sync():
    """Backboard memory service records interaction and updates user UI preferences."""
    from app.agents.memory_service import BackboardMemoryService
    service = BackboardMemoryService()
    db = SessionLocal()
    try:
        service.record_interaction(
            user_id="USR-LOW-ENG-005",
            query="Test query about cataract",
            intent="DOC_QUERY",
            answer="Cataract coverage is INR 45,000",
            db=db,
        )
        mem = service.get_user_memory("USR-LOW-ENG-005", db)
        assert mem.interaction_count > 0
        assert len(mem.recent_topics) > 0
        assert "cataract" in mem.recent_topics[0].lower()
    finally:
        db.close()
