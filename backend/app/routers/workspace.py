"""
StrataIQ Workspace Router — Dynamic JSON-Driven Role & Layer Workspace API

Endpoints:
  GET  /api/v1/workspace/personas              — 6 showcase personas for Judge Sandbox
  GET  /api/v1/workspace/bootstrap             — Role-adaptive KPIs, layout & profile
  POST /api/v1/workspace/confirm-parental-rider — Employee confirms NovaShield parental rider
  POST /api/v1/workspace/reset-demo-state      — Reset all mutations for judge re-demo
"""
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db, get_security_context, SecurityContext
from app.models import (
    User, OrgLayer, Department, EmployeeEnrollment, InsuranceClaim,
    WorkflowTask, DecisionMatrixLog, VendorPolicy
)
from app.schemas import (
    UserContext, PersonasResponse, BootstrapResponse, LayoutConfig,
    LayoutModuleBlock, EnrollmentRecord, WorkflowTaskItem, ClaimItem,
    ConflictAlert, UpperKPIs, MiddleKPIs, LowerKPIs,
    ConfirmParentalRiderResponse, ResetDemoStateResponse,
)
from app.firestore_sync import firestore_service

router = APIRouter()

# ── Showcase persona IDs for the Judge Sandbox Mode ──────────────────────────
SHOWCASE_PERSONA_IDS = [
    "USR-UPPER-FIN-001",
    "USR-UPPER-HR-002",
    "USR-MID-HR-003",
    "USR-MID-IT-004",
    "USR-LOW-ENG-005",
    "USR-LOW-OPS-006",
]


def _user_to_context(user: User, org_layer: OrgLayer, department: Department) -> UserContext:
    """Helper: map ORM objects → UserContext schema."""
    try:
        ui_prefs = json.loads(user.ui_preferences_json) if user.ui_preferences_json else {}
    except (json.JSONDecodeError, TypeError):
        ui_prefs = {}
    return UserContext(
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        job_title=user.job_title,
        grade_tier=user.grade_tier,
        dept_id=user.dept_id,
        dept_name=department.dept_name,
        layer_id=org_layer.layer_id,
        layer_code=org_layer.layer_code,
        clearance_level=org_layer.clearance_level,
        ui_preferences=ui_prefs,
    )


def _build_layout_config(ctx: SecurityContext) -> LayoutConfig:
    """
    Build the dynamic JSON module array based on (layer_code, dept_id).
    Merges with ui_preferences_json from the database for personalization.
    """
    default_view = ctx.ui_preferences.get("default_view", "")

    if ctx.layer_code == "UPPER":
        modules = [
            LayoutModuleBlock(module_id="executive_decision_matrix",
                              title="Executive Decision Matrix",
                              component="DecisionMatrixPanel",
                              props={"show_approve_button": True,
                                     "highlighted": default_view == "financial_decision_matrix"}),
            LayoutModuleBlock(module_id="financial_kpi_dashboard",
                              title="Financial KPI Dashboard",
                              component="FinancialKPIGrid",
                              props={"show_sql_tables": ctx.ui_preferences.get("show_sql_tables", False)}),
            LayoutModuleBlock(module_id="cross_dept_conflict_alert",
                              title="Cross-Department Conflict Alerts",
                              component="ConflictAlertBanner",
                              props={}),
            LayoutModuleBlock(module_id="document_vault",
                              title="Full Document Vault (Clearance 3)",
                              component="DocumentVaultPanel",
                              props={"clearance_level": ctx.clearance_level}),
        ]

    elif ctx.layer_code == "MIDDLE" and ctx.dept_id == "DEPT-HR":
        modules = [
            LayoutModuleBlock(module_id="migration_escalation_warroom",
                              title="Migration Escalation War-Room",
                              component="EscalationWarRoom",
                              props={"highlighted": default_view == "migration_escalation_warroom"}),
            LayoutModuleBlock(module_id="cross_silo_conflict_detector",
                              title="Cross-Silo Schedule Conflict Detector",
                              component="ConflictDetectorPanel",
                              props={}),
            LayoutModuleBlock(module_id="claims_triage_panel",
                              title="Transition Claims Triage",
                              component="ClaimsTriagePanel",
                              props={}),
            LayoutModuleBlock(module_id="document_vault",
                              title="Document Vault (Clearance 2)",
                              component="DocumentVaultPanel",
                              props={"clearance_level": ctx.clearance_level}),
            LayoutModuleBlock(module_id="task_checklist",
                              title="My Task Checklist",
                              component="TaskChecklist",
                              props={}),
        ]

    elif ctx.layer_code == "MIDDLE" and ctx.dept_id == "DEPT-IT":
        modules = [
            LayoutModuleBlock(module_id="sso_portal_status",
                              title="SSO Portal Launch Status",
                              component="SSOPortalStatus",
                              props={}),
            LayoutModuleBlock(module_id="it_task_checklist",
                              title="IT Task Checklist",
                              component="TaskChecklist",
                              props={}),
            LayoutModuleBlock(module_id="document_vault",
                              title="Document Vault (Clearance 2)",
                              component="DocumentVaultPanel",
                              props={"clearance_level": ctx.clearance_level}),
        ]

    elif ctx.layer_code == "MIDDLE":
        # Other middle-layer departments
        modules = [
            LayoutModuleBlock(module_id="task_checklist",
                              title="My Task Checklist",
                              component="TaskChecklist",
                              props={}),
            LayoutModuleBlock(module_id="document_vault",
                              title="Document Vault (Clearance 2)",
                              component="DocumentVaultPanel",
                              props={"clearance_level": ctx.clearance_level}),
        ]

    else:
        # LOWER layer — all departments
        modules = [
            LayoutModuleBlock(module_id="personal_benefits_card",
                              title="My Health Benefits Card",
                              component="PersonalBenefitsCard",
                              props={"highlight_parental_opt_in": True}),
            LayoutModuleBlock(module_id="voice_doc_studio",
                              title="Talk with Your Documents",
                              component="VoiceDocStudio",
                              props={"voice_speed": ctx.ui_preferences.get("voice_speed", 1.0)}),
            LayoutModuleBlock(module_id="task_checklist",
                              title="My Task Checklist",
                              component="TaskChecklist",
                              props={}),
            LayoutModuleBlock(module_id="personal_claim_tracker",
                              title="My Claims & Pre-Auth Tracker",
                              component="ClaimTracker",
                              props={}),
        ]

    return LayoutConfig(
        layer_code=ctx.layer_code,
        dept_id=ctx.dept_id,
        modules=modules,
    )


def _compute_upper_kpis(db: Session) -> dict[str, Any]:
    """Live SQL KPIs for UPPER layer (Clearance 3)."""
    # NovaShield annual premium
    nova = db.query(VendorPolicy).filter(
        VendorPolicy.policy_id == "POL-NOVASHIELD-2026"
    ).first()
    premium = float(nova.annual_premium) if nova else 0.0

    # Legacy pro-rata refund = (legacy premium / 12) * 10 months remaining ≈ stored in decision log
    dec = db.query(DecisionMatrixLog).filter(
        DecisionMatrixLog.decision_id == "DEC-2026-001"
    ).first()
    parental_variance = float(dec.financial_impact) if dec else 0.0

    # LegacyCare refund = 19.2L (documented in decision options OPTION_B_RECOMMENDED)
    legacycare_refund = 1_920_000.0

    # Pending decisions
    pending_decisions = db.query(func.count(DecisionMatrixLog.decision_id)).filter(
        DecisionMatrixLog.status == "PENDING_EXECUTIVE_APPROVAL"
    ).scalar() or 0

    # Cross-department conflicts from workflow_tasks
    conflicts = db.query(func.count(WorkflowTask.task_id)).filter(
        WorkflowTask.status == "CONFLICT_FLAGGED"
    ).scalar() or 0

    return UpperKPIs(
        novashield_annual_premium_inr=premium,
        parental_premium_variance_inr=parental_variance,
        legacycare_prorata_refund_inr=legacycare_refund,
        pending_executive_decisions=pending_decisions,
        cross_dept_conflicts=conflicts,
    ).model_dump()


def _compute_middle_kpis(db: Session) -> dict[str, Any]:
    """Live SQL KPIs for MIDDLE layer (Clearance 2)."""
    # Count employees with PENDING_CONFIRMATION parental opt-in
    blocked = db.query(func.count(EmployeeEnrollment.enrollment_id)).filter(
        EmployeeEnrollment.parental_opt_in == "PENDING_CONFIRMATION"
    ).scalar() or 0

    # Stuck transition claims (across all stages except CLOSED/SETTLED)
    stuck_stages = ["STUCK_IN_TRANSITION", "PRE_AUTH_DRAFT", "AWAITING_TPA_RESPONSE",
                    "PENDING_DOCUMENTS", "ESCALATED_TO_INSURER"]
    stuck_claims = db.query(InsuranceClaim).filter(
        InsuranceClaim.claim_stage.in_(stuck_stages)
    ).all()
    stuck_count = len(stuck_claims)
    stuck_amount = sum(float(c.claim_amount) for c in stuck_claims)

    # P0/P1 escalations (claims above INR 1 lakh in STUCK_IN_TRANSITION)
    p0_p1 = sum(1 for c in stuck_claims if float(c.claim_amount) >= 100_000)

    # TSK-03 vs TSK-05 conflict alert
    tsk03 = db.query(WorkflowTask).filter(WorkflowTask.task_id == "TSK-03").first()
    tsk05 = db.query(WorkflowTask).filter(WorkflowTask.task_id == "TSK-05").first()

    conflict_alert = None
    if tsk03 and tsk05 and tsk03.status == "CONFLICT_FLAGGED":
        conflict_alert = ConflictAlert(
            conflict_id="CONFLICT-TSK03-TSK05",
            description=(
                "Finance payroll lock (Oct 20) conflicts with IT SSO portal launch (Oct 23). "
                "142 employees cannot confirm parental rider until SSO is live, "
                "blocking INR 14.2L in transition claims."
            ),
            task_a_id=tsk03.task_id,
            task_a_title=tsk03.title,
            task_a_due=str(tsk03.due_date),
            task_b_id=tsk05.task_id,
            task_b_title=tsk05.title,
            task_b_due=str(tsk05.due_date),
            employees_blocked=blocked,
            claims_amount_inr=stuck_amount,
        )

    return MiddleKPIs(
        employees_blocked_parental_rider=blocked,
        stuck_transition_claims_count=stuck_count,
        stuck_transition_claims_amount_inr=stuck_amount,
        p0_p1_escalations=p0_p1,
        conflict_alert=conflict_alert,
    ).model_dump()


def _compute_lower_kpis(db: Session, ctx: SecurityContext) -> dict[str, Any]:
    """Live SQL KPIs scoped to the individual LOWER-layer employee."""
    # Personal enrollment record ONLY
    enrollment_row = db.query(EmployeeEnrollment).filter(
        EmployeeEnrollment.user_id == ctx.user_id
    ).first()

    enrollment = None
    if enrollment_row:
        enrollment = EnrollmentRecord(
            enrollment_id=enrollment_row.enrollment_id,
            user_id=enrollment_row.user_id,
            policy_id=enrollment_row.policy_id,
            sum_insured=enrollment_row.sum_insured,
            dependents_count=enrollment_row.dependents_count,
            parental_opt_in=enrollment_row.parental_opt_in,
            monthly_copay_deduction=enrollment_row.monthly_copay_deduction,
            migration_status=enrollment_row.migration_status,
        )

    # Tasks assigned to this user only
    tasks = db.query(WorkflowTask).filter(
        WorkflowTask.assigned_to_user_id == ctx.user_id
    ).all()
    task_items = [
        WorkflowTaskItem(
            task_id=t.task_id,
            dept_id=t.dept_id,
            assigned_to_user_id=t.assigned_to_user_id,
            layer_id=t.layer_id,
            title=t.title,
            due_date=str(t.due_date),
            status=t.status,
            dependency_task_id=t.dependency_task_id,
            blocker_note=t.blocker_note,
        )
        for t in tasks
    ]

    # Personal claims for this user only
    claims = db.query(InsuranceClaim).filter(
        InsuranceClaim.user_id == ctx.user_id
    ).all()
    claim_items = [
        ClaimItem(
            claim_id=c.claim_id,
            user_id=c.user_id,
            policy_id=c.policy_id,
            hospital_name=c.hospital_name,
            city=c.city,
            treatment_type=c.treatment_type,
            claim_amount=float(c.claim_amount),
            claim_stage=c.claim_stage,
            assigned_hr_id=c.assigned_hr_id,
            blocker_reason=c.blocker_reason,
        )
        for c in claims
    ]

    return LowerKPIs(
        enrollment=enrollment,
        assigned_tasks=task_items,
        personal_claims=claim_items,
    ).model_dump()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/personas", response_model=PersonasResponse, summary="Get 6 Judge Sandbox Personas")
def get_personas(db: Session = Depends(get_db)):
    """
    Returns the 6 showcase personas for the Judge Sandbox Mode switcher.
    No authentication required — this is the public entry point for judges.
    """
    rows = (
        db.query(User, OrgLayer, Department)
        .join(OrgLayer, User.layer_id == OrgLayer.layer_id)
        .join(Department, User.dept_id == Department.dept_id)
        .filter(User.user_id.in_(SHOWCASE_PERSONA_IDS))
        .all()
    )

    # Preserve the canonical ordering
    row_map = {user.user_id: (user, org, dept) for user, org, dept in rows}
    personas = [
        _user_to_context(*row_map[pid])
        for pid in SHOWCASE_PERSONA_IDS
        if pid in row_map
    ]
    return PersonasResponse(personas=personas)


@router.get("/bootstrap", response_model=BootstrapResponse, summary="Role-Adaptive Workspace Bootstrap")
def bootstrap_workspace(
    ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db),
):
    """
    Single endpoint that returns everything the frontend needs to render
    a fully personalized, role-adaptive workspace for the authenticated user.
    Enforces Zero-Trust RLS: KPIs are computed exclusively from SQL rows
    the requesting user is authorized to see.
    """
    user_profile = UserContext(
        user_id=ctx.user_id,
        full_name=ctx.full_name,
        email=ctx.email,
        job_title=ctx.job_title,
        grade_tier=ctx.grade_tier,
        dept_id=ctx.dept_id,
        dept_name=ctx.dept_name,
        layer_id=ctx.layer_id,
        layer_code=ctx.layer_code,
        clearance_level=ctx.clearance_level,
        ui_preferences=ctx.ui_preferences,
    )

    layout_config = _build_layout_config(ctx)

    if ctx.layer_code == "UPPER":
        kpis = _compute_upper_kpis(db)
    elif ctx.layer_code == "MIDDLE":
        kpis = _compute_middle_kpis(db)
    else:
        kpis = _compute_lower_kpis(db, ctx)

    return BootstrapResponse(
        user_profile=user_profile,
        layout_config=layout_config,
        role_scoped_kpis=kpis,
    )


@router.post(
    "/confirm-parental-rider",
    response_model=ConfirmParentalRiderResponse,
    summary="Confirm NovaShield Parental Rider Enrollment",
)
def confirm_parental_rider(
    ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db),
):
    """
    Allows the logged-in employee to confirm their NovaShield parental rider.
    Executes a real SQL UPDATE on employee_enrollments for the requesting user.
    """
    enrollment = db.query(EmployeeEnrollment).filter(
        EmployeeEnrollment.user_id == ctx.user_id
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No enrollment record found for user '{ctx.user_id}'.",
        )

    # Atomic update
    enrollment.parental_opt_in = "CONFIRMED"
    enrollment.migration_status = "MIGRATED_TO_NOVASHIELD"
    db.commit()
    db.refresh(enrollment)

    # Sync event to Google Cloud Firestore (graceful fallback if offline)
    firestore_service.sync_user_session_event(
        user_id=ctx.user_id,
        layer_code=ctx.layer_code,
        action="CONFIRM_PARENTAL_RIDER",
        metadata={
            "enrollment_id": enrollment.enrollment_id,
            "policy_id": enrollment.policy_id,
            "monthly_copay_deduction": enrollment.monthly_copay_deduction,
        },
    )

    return ConfirmParentalRiderResponse(
        message=(
            f"✅ Parental rider confirmed for {ctx.full_name}. "
            "You are now enrolled under NovaShield Health 2026."
        ),
        enrollment=EnrollmentRecord(
            enrollment_id=enrollment.enrollment_id,
            user_id=enrollment.user_id,
            policy_id=enrollment.policy_id,
            sum_insured=enrollment.sum_insured,
            dependents_count=enrollment.dependents_count,
            parental_opt_in=enrollment.parental_opt_in,
            monthly_copay_deduction=enrollment.monthly_copay_deduction,
            migration_status=enrollment.migration_status,
        ),
    )


@router.post(
    "/reset-demo-state",
    response_model=ResetDemoStateResponse,
    summary="[Judge Sandbox] Reset all demo mutations",
)
def reset_demo_state(db: Session = Depends(get_db)):
    """
    Resets all mutated rows back to their original seeded state.
    No authentication required — public endpoint for judge re-demo.
    """
    reset_log = []

    # 1. Reset USR-LOW-ENG-005 enrollment
    enr = db.query(EmployeeEnrollment).filter(
        EmployeeEnrollment.user_id == "USR-LOW-ENG-005"
    ).first()
    if enr:
        enr.parental_opt_in = "PENDING_CONFIRMATION"
        enr.migration_status = "BLOCKED_BY_SSO_PORTAL_DELAY"
        reset_log.append("employee_enrollments: USR-LOW-ENG-005 → PENDING_CONFIRMATION, BLOCKED_BY_SSO_PORTAL_DELAY")

    # 2. Reset DEC-2026-001 decision log
    dec = db.query(DecisionMatrixLog).filter(
        DecisionMatrixLog.decision_id == "DEC-2026-001"
    ).first()
    if dec:
        dec.status = "PENDING_EXECUTIVE_APPROVAL"
        dec.selected_option = "PENDING"
        dec.decided_at = None
        reset_log.append("decision_matrix_logs: DEC-2026-001 → PENDING_EXECUTIVE_APPROVAL, decided_at=NULL")

    # 3. Reset TSK-02 (CFO decision task)
    tsk02 = db.query(WorkflowTask).filter(WorkflowTask.task_id == "TSK-02").first()
    if tsk02:
        tsk02.status = "PENDING_CFO_DECISION"
        reset_log.append("workflow_tasks: TSK-02 → PENDING_CFO_DECISION")

    # 4. Reset TSK-03 (payroll lock conflict)
    tsk03 = db.query(WorkflowTask).filter(WorkflowTask.task_id == "TSK-03").first()
    if tsk03:
        tsk03.status = "CONFLICT_FLAGGED"
        tsk03.due_date = "2026-10-20"
        tsk03.blocker_note = "CONFLICT: Scheduled for Oct 20, but IT SSO portal (TSK-05) isn't ready until Oct 23!"
        reset_log.append("workflow_tasks: TSK-03 → CONFLICT_FLAGGED, due_date=2026-10-20")

    db.commit()

    return ResetDemoStateResponse(
        message="✅ Demo state has been fully reset. All mutations reverted to original seed values.",
        reset_items=reset_log,
    )
