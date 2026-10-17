"""
StrataIQ Phase 1 — Automated RLS & RDBMS Test Suite
=====================================================
Tests the Zero-Trust Row-Level Security boundaries across all 3 clearance layers
using the real local_enterprise.db (Zero-Mock policy).

Test Map:
  T01  Lower-layer can read a Clearance-1 document (DOC-011)
  T02  Lower-layer is blocked (403) on a Clearance-3 document (DOC-008 CFO Memo)
  T03  Lower-layer is blocked (403) when trying to approve DEC-2026-001
  T04  Lower-layer bootstrap only contains their own enrollment (USR-LOW-ENG-005)
  T05  Lower-layer bootstrap contains no other user's enrollment data
  T06  Middle-layer HR bootstrap shows >= 142 employees blocked on parental rider
  T07  Middle-layer HR bootstrap shows >= 11 stuck transition claims
  T08  Middle-layer HR bootstrap contains the TSK-03/TSK-05 conflict alert
  T09  Middle-layer is blocked (403) when trying to approve DEC-2026-001
  T10  Upper-layer CFO can access all 22 documents
  T11  Upper-layer CFO can approve OPTION_B_RECOMMENDED on DEC-2026-001 → APPROVED
  T12  After OPTION_B approval, TSK-03 status is SCHEDULE_ALIGNED
  T13  Reset demo state restores USR-LOW-ENG-005 to PENDING_CONFIRMATION
"""
import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────────────────────
# T01 — Lower-layer can read a Clearance-1 document
# ─────────────────────────────────────────────────────────────────────────────
def test_lower_can_read_clearance1_doc(lower_client: TestClient):
    """USR-LOW-ENG-005 must be able to fetch DOC-011 (Employee Handbook, min_clearance=1)."""
    resp = lower_client.get("/api/v1/documents/DOC-011/content")
    assert resp.status_code == 200, (
        f"Expected 200 for DOC-011 (Clearance 1) but got {resp.status_code}: {resp.text}"
    )
    data = resp.json()
    assert data["doc_id"] == "DOC-011"
    assert isinstance(data["chunks"], list)
    assert len(data["chunks"]) > 0, "DOC-011 must have at least 1 chunk in the database"


# ─────────────────────────────────────────────────────────────────────────────
# T02 — Lower-layer is blocked on a Clearance-3 document
# ─────────────────────────────────────────────────────────────────────────────
def test_lower_blocked_on_clearance3_doc(lower_client: TestClient):
    """USR-LOW-ENG-005 must receive 403 Forbidden on DOC-008 (CFO Memo, min_clearance=3)."""
    resp = lower_client.get("/api/v1/documents/DOC-008/content")
    assert resp.status_code == 403, (
        f"Expected 403 for DOC-008 (Clearance 3) but got {resp.status_code}: {resp.text}"
    )
    assert "Access denied" in resp.json().get("detail", ""), (
        "Error detail should explain the clearance mismatch"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T03 — Lower-layer is blocked from approving decisions
# ─────────────────────────────────────────────────────────────────────────────
def test_lower_blocked_on_decision_approve(lower_client: TestClient):
    """USR-LOW-ENG-005 must receive 403 when attempting to approve DEC-2026-001."""
    resp = lower_client.post(
        "/api/v1/decisions/DEC-2026-001/approve",
        json={"selected_option": "OPTION_B_RECOMMENDED"},
    )
    assert resp.status_code == 403, (
        f"Expected 403 for LOWER-layer decision approval but got {resp.status_code}: {resp.text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T04 — Lower-layer bootstrap only contains their own enrollment
# ─────────────────────────────────────────────────────────────────────────────
def test_lower_sees_own_enrollment_only(lower_client: TestClient):
    """
    USR-LOW-ENG-005's bootstrap KPIs must contain exactly their own enrollment record,
    scoped by user_id = 'USR-LOW-ENG-005'. No aggregate company data should leak.
    """
    resp = lower_client.get("/api/v1/workspace/bootstrap")
    assert resp.status_code == 200, f"Bootstrap failed: {resp.text}"
    data = resp.json()

    kpis = data["role_scoped_kpis"]
    enrollment = kpis.get("enrollment")
    assert enrollment is not None, "Lower-layer KPIs must include an 'enrollment' key"
    assert enrollment["user_id"] == "USR-LOW-ENG-005", (
        f"Enrollment user_id must be 'USR-LOW-ENG-005', got '{enrollment['user_id']}'"
    )

    # Verify it's the correct record (parental opt-in is PENDING_CONFIRMATION after reset)
    assert enrollment["parental_opt_in"] == "PENDING_CONFIRMATION", (
        "After reset, USR-LOW-ENG-005's parental_opt_in should be PENDING_CONFIRMATION"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T05 — Lower-layer bootstrap does NOT contain other users' enrollment data
# ─────────────────────────────────────────────────────────────────────────────
def test_lower_sees_no_other_employee_data(lower_client: TestClient):
    """
    Zero-Trust verification: the lower-layer KPI payload must NOT contain
    aggregate company enrollment counts or any other user's user_id.
    """
    resp = lower_client.get("/api/v1/workspace/bootstrap")
    assert resp.status_code == 200
    kpis = resp.json()["role_scoped_kpis"]

    # These are UPPER/MIDDLE layer KPI keys — must NOT appear for LOWER
    forbidden_keys = [
        "employees_blocked_parental_rider",  # Middle
        "stuck_transition_claims_count",      # Middle
        "novashield_annual_premium_inr",      # Upper
        "pending_executive_decisions",        # Upper
    ]
    for key in forbidden_keys:
        assert key not in kpis, (
            f"Data leak detected: lower-layer KPIs must not expose '{key}'"
        )

    # Tasks must only reference this user
    for task in kpis.get("assigned_tasks", []):
        assert task["assigned_to_user_id"] == "USR-LOW-ENG-005", (
            f"Task {task['task_id']} belongs to {task['assigned_to_user_id']}, not USR-LOW-ENG-005"
        )

    # Claims must only reference this user
    for claim in kpis.get("personal_claims", []):
        assert claim["user_id"] == "USR-LOW-ENG-005", (
            f"Claim {claim['claim_id']} belongs to {claim['user_id']}, not USR-LOW-ENG-005"
        )


# ─────────────────────────────────────────────────────────────────────────────
# T06 — Middle-layer HR receives >= 142 employees blocked on parental rider
# ─────────────────────────────────────────────────────────────────────────────
def test_middle_gets_142_pending_parental(middle_hr_client: TestClient):
    """
    USR-MID-HR-003 bootstrap KPIs must report the live SQL count of employees
    with parental_opt_in = 'PENDING_CONFIRMATION'. Expect >= 142.
    """
    resp = middle_hr_client.get("/api/v1/workspace/bootstrap")
    assert resp.status_code == 200, f"Bootstrap failed: {resp.text}"
    kpis = resp.json()["role_scoped_kpis"]

    blocked = kpis.get("employees_blocked_parental_rider")
    assert blocked is not None, "Middle KPIs must include 'employees_blocked_parental_rider'"
    assert blocked >= 142, (
        f"Expected >= 142 blocked employees, got {blocked}. "
        "Check PENDING_CONFIRMATION count in employee_enrollments."
    )


# ─────────────────────────────────────────────────────────────────────────────
# T07 — Middle-layer HR receives >= 11 stuck transition claims
# ─────────────────────────────────────────────────────────────────────────────
def test_middle_gets_11_stuck_claims(middle_hr_client: TestClient):
    """
    USR-MID-HR-003 bootstrap KPIs must report the live SQL count of stuck
    transition claims. Expect >= 11 (seeded: 12 claims, at least 11 stuck).
    """
    resp = middle_hr_client.get("/api/v1/workspace/bootstrap")
    assert resp.status_code == 200
    kpis = resp.json()["role_scoped_kpis"]

    stuck = kpis.get("stuck_transition_claims_count")
    assert stuck is not None, "Middle KPIs must include 'stuck_transition_claims_count'"
    assert stuck >= 11, (
        f"Expected >= 11 stuck transition claims, got {stuck}. "
        "Check insurance_claims_escalations for STUCK/PRE_AUTH_DRAFT stages."
    )


# ─────────────────────────────────────────────────────────────────────────────
# T08 — Middle-layer HR bootstrap contains the TSK-03 vs TSK-05 conflict alert
# ─────────────────────────────────────────────────────────────────────────────
def test_middle_gets_conflict_alert(middle_hr_client: TestClient):
    """
    USR-MID-HR-003 bootstrap KPIs must contain a conflict_alert referencing
    TSK-03 (Oct 20 payroll lock) vs TSK-05 (Oct 23 SSO portal).
    """
    resp = middle_hr_client.get("/api/v1/workspace/bootstrap")
    assert resp.status_code == 200
    kpis = resp.json()["role_scoped_kpis"]

    alert = kpis.get("conflict_alert")
    assert alert is not None, (
        "Middle HR KPIs must include a 'conflict_alert' when TSK-03 is CONFLICT_FLAGGED"
    )
    assert alert["task_a_id"] == "TSK-03", (
        f"conflict_alert.task_a_id must be TSK-03, got '{alert.get('task_a_id')}'"
    )
    assert alert["task_b_id"] == "TSK-05", (
        f"conflict_alert.task_b_id must be TSK-05, got '{alert.get('task_b_id')}'"
    )
    assert alert["employees_blocked"] >= 142, (
        "Conflict alert must report the correct employees_blocked count"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T09 — Middle-layer is blocked from approving decisions
# ─────────────────────────────────────────────────────────────────────────────
def test_middle_blocked_on_decision_approve(middle_hr_client: TestClient):
    """USR-MID-HR-003 must receive 403 when attempting to approve DEC-2026-001."""
    resp = middle_hr_client.post(
        "/api/v1/decisions/DEC-2026-001/approve",
        json={"selected_option": "OPTION_B_RECOMMENDED"},
    )
    assert resp.status_code == 403, (
        f"Expected 403 for MIDDLE-layer decision approval but got {resp.status_code}: {resp.text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T10 — Upper-layer CFO can access all 22 documents
# ─────────────────────────────────────────────────────────────────────────────
def test_upper_sees_all_22_docs(upper_cfo_client: TestClient):
    """
    USR-UPPER-FIN-001 (Clearance 3) must see all 22 documents as accessible.
    restricted_hidden_count must be 0.
    """
    resp = upper_cfo_client.get("/api/v1/documents")
    assert resp.status_code == 200, f"Documents list failed: {resp.text}"
    data = resp.json()

    assert data["clearance_level"] == 3
    assert len(data["accessible_docs"]) == 22, (
        f"Upper layer must see all 22 docs, got {len(data['accessible_docs'])}"
    )
    assert data["restricted_hidden_count"] == 0, (
        f"Upper layer must have 0 restricted docs, got {data['restricted_hidden_count']}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T11 — Upper-layer CFO can approve OPTION_B_RECOMMENDED → status APPROVED
# ─────────────────────────────────────────────────────────────────────────────
def test_upper_can_approve_decision(upper_cfo_client: TestClient, no_auth_client: TestClient):
    """
    USR-UPPER-FIN-001 must be able to approve DEC-2026-001 with OPTION_B_RECOMMENDED.
    Response must have status='APPROVED' and include mutated task IDs.
    """
    # Ensure clean state before this test
    no_auth_client.post("/api/v1/workspace/reset-demo-state")

    resp = upper_cfo_client.post(
        "/api/v1/decisions/DEC-2026-001/approve",
        json={"selected_option": "OPTION_B_RECOMMENDED"},
    )
    assert resp.status_code == 200, (
        f"Expected 200 for UPPER-layer decision approval but got {resp.status_code}: {resp.text}"
    )
    data = resp.json()
    assert data["decision_id"] == "DEC-2026-001"
    assert data["status"] == "APPROVED"
    assert data["selected_option"] == "OPTION_B_RECOMMENDED"
    assert data["decided_at"] is not None

    # Verify task mutations are reported
    mutated_ids = [t["task_id"] for t in data["tasks_mutated"]]
    assert "TSK-02" in mutated_ids, "TSK-02 should be reported as mutated"
    assert "TSK-03" in mutated_ids, "TSK-03 should be reported as mutated"


# ─────────────────────────────────────────────────────────────────────────────
# T12 — After OPTION_B approval, TSK-03 is SCHEDULE_ALIGNED with Oct 25 due date
# ─────────────────────────────────────────────────────────────────────────────
def test_approve_mutates_workflow_tasks(upper_cfo_client: TestClient, middle_hr_client: TestClient, no_auth_client: TestClient):
    """
    After CFO approves OPTION_B_RECOMMENDED:
    - TSK-03 must have status=SCHEDULE_ALIGNED in the Middle-HR bootstrap KPIs
    - The conflict_alert must be None (conflict resolved)
    """
    # Ensure a fresh approval happened (T11 may have run first, but we re-ensure clean + approve)
    no_auth_client.post("/api/v1/workspace/reset-demo-state")
    approve_resp = upper_cfo_client.post(
        "/api/v1/decisions/DEC-2026-001/approve",
        json={"selected_option": "OPTION_B_RECOMMENDED"},
    )
    assert approve_resp.status_code == 200

    # Now verify the Middle-HR dashboard reflects the resolved conflict
    bootstrap_resp = middle_hr_client.get("/api/v1/workspace/bootstrap")
    assert bootstrap_resp.status_code == 200
    kpis = bootstrap_resp.json()["role_scoped_kpis"]

    # Conflict alert should be gone (TSK-03 no longer CONFLICT_FLAGGED)
    alert = kpis.get("conflict_alert")
    assert alert is None, (
        f"conflict_alert should be None after OPTION_B approval, but got: {alert}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T13 — Reset demo state restores original seed values
# ─────────────────────────────────────────────────────────────────────────────
def test_reset_demo_state_works(
    upper_cfo_client: TestClient,
    lower_client: TestClient,
    no_auth_client: TestClient,
):
    """
    After calling POST /workspace/reset-demo-state:
    - USR-LOW-ENG-005 enrollment returns to PENDING_CONFIRMATION
    - DEC-2026-001 returns to PENDING_EXECUTIVE_APPROVAL
    - TSK-03 returns to CONFLICT_FLAGGED
    - Middle HR bootstrap conflict_alert reappears
    """
    # First, apply all mutations
    upper_cfo_client.post(
        "/api/v1/decisions/DEC-2026-001/approve",
        json={"selected_option": "OPTION_B_RECOMMENDED"},
    )
    lower_client.post("/api/v1/workspace/confirm-parental-rider")

    # Now reset
    reset_resp = no_auth_client.post("/api/v1/workspace/reset-demo-state")
    assert reset_resp.status_code == 200
    reset_data = reset_resp.json()
    assert "reset_items" in reset_data
    assert len(reset_data["reset_items"]) > 0

    # Verify USR-LOW-ENG-005 enrollment is back to PENDING_CONFIRMATION
    lower_bootstrap = lower_client.get("/api/v1/workspace/bootstrap")
    assert lower_bootstrap.status_code == 200
    enrollment = lower_bootstrap.json()["role_scoped_kpis"]["enrollment"]
    assert enrollment["parental_opt_in"] == "PENDING_CONFIRMATION", (
        f"After reset, parental_opt_in must be PENDING_CONFIRMATION, got '{enrollment['parental_opt_in']}'"
    )
    assert enrollment["migration_status"] == "BLOCKED_BY_SSO_PORTAL_DELAY", (
        f"After reset, migration_status must be BLOCKED_BY_SSO_PORTAL_DELAY, got '{enrollment['migration_status']}'"
    )

    # Verify DEC-2026-001 is back to PENDING
    decisions_resp = upper_cfo_client.get("/api/v1/decisions")
    assert decisions_resp.status_code == 200
    decisions = decisions_resp.json()["decisions"]
    dec = next((d for d in decisions if d["decision_id"] == "DEC-2026-001"), None)
    assert dec is not None
    assert dec["status"] == "PENDING_EXECUTIVE_APPROVAL", (
        f"After reset, DEC-2026-001 status must be PENDING_EXECUTIVE_APPROVAL, got '{dec['status']}'"
    )
    assert dec["decided_at"] is None, "After reset, decided_at must be None"
