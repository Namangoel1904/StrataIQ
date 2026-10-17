"""
StrataIQ Decisions Router — ACID Executive Decision Matrix API

Endpoints:
  GET  /api/v1/decisions                          — List decisions (Clearance >= 2)
  POST /api/v1/decisions/{decision_id}/approve    — ACID approval (Clearance == 3 only)
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db, get_security_context, SecurityContext
from app.database import assert_upper_only, assert_at_least_middle
from app.models import DecisionMatrixLog, WorkflowTask
from app.schemas import (
    DecisionsListResponse, DecisionMatrixItem, DecisionOption,
    ApproveDecisionRequest, ApproveDecisionResponse, MutatedTask,
)

router = APIRouter()


def _parse_options(options_json: str) -> list[DecisionOption]:
    """Parse the options_json TEXT column (stored as JSON string in SQLite)."""
    try:
        raw = json.loads(options_json) if options_json else []
    except (json.JSONDecodeError, TypeError):
        raw = []
    return [
        DecisionOption(
            option_code=o.get("option_code", ""),
            label=o.get("label", ""),
            net_company_cost_inr=int(o.get("net_company_cost_inr", 0)),
            employee_monthly_impact_inr=int(o.get("employee_monthly_impact_inr", 0)),
            cutoff_resolution=o.get("cutoff_resolution", ""),
            risk_level=o.get("risk_level", ""),
        )
        for o in raw
    ]


def _decision_to_schema(dec: DecisionMatrixLog) -> DecisionMatrixItem:
    return DecisionMatrixItem(
        decision_id=dec.decision_id,
        triggered_by_doc_id=dec.triggered_by_doc_id,
        approver_user_id=dec.approver_user_id,
        title=dec.title,
        status=dec.status,
        options=_parse_options(dec.options_json),
        selected_option=dec.selected_option,
        financial_impact=float(dec.financial_impact),
        eval_grounding_score=float(dec.eval_grounding_score),
        decided_at=dec.decided_at.isoformat() if dec.decided_at else None,
    )


@router.get(
    "",
    response_model=DecisionsListResponse,
    summary="List Executive Decision Matrix (Clearance >= 2)",
)
def list_decisions(
    ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db),
):
    """
    Returns all rows from decision_matrix_logs with parsed options.
    Zero-Trust RLS: LOWER layer (clearance_level < 2) receives 403 Forbidden.
    """
    assert_at_least_middle(ctx)

    decisions = db.query(DecisionMatrixLog).all()
    return DecisionsListResponse(
        decisions=[_decision_to_schema(d) for d in decisions]
    )


@router.post(
    "/{decision_id}/approve",
    response_model=ApproveDecisionResponse,
    summary="Approve Executive Decision (UPPER Layer Only — ACID Transaction)",
)
def approve_decision(
    decision_id: str,
    body: ApproveDecisionRequest,
    ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db),
):
    """
    Executes an ACID SQL transaction to approve an executive decision.

    Zero-Trust RLS:
    - LOWER layer → 403 Forbidden
    - MIDDLE layer → 403 Forbidden
    - UPPER layer (clearance 3) → Proceeds

    For DEC-2026-001 + OPTION_B_RECOMMENDED:
    1. Updates decision_matrix_logs (status=APPROVED, selected_option, decided_at)
    2. Resolves TSK-02 → COMPLETED
    3. Resolves TSK-03 → SCHEDULE_ALIGNED, due_date=2026-10-25

    All three updates execute atomically in a single transaction.
    """
    # Zero-Trust RLS gate — UPPER ONLY
    assert_upper_only(ctx)

    # Fetch the decision record
    dec = db.query(DecisionMatrixLog).filter(
        DecisionMatrixLog.decision_id == decision_id
    ).first()
    if not dec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision '{decision_id}' not found.",
        )

    # Validate selected_option is one of the declared option codes
    valid_options = [o["option_code"] for o in json.loads(dec.options_json or "[]")]
    if body.selected_option not in valid_options:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid option '{body.selected_option}'. "
                f"Valid options: {valid_options}"
            ),
        )

    now_utc = datetime.now(timezone.utc)
    tasks_mutated: list[MutatedTask] = []

    try:
        # ── ACID Transaction ──────────────────────────────────────────────────
        # Step 1: Update the decision log
        dec.status = "APPROVED"
        dec.selected_option = body.selected_option
        dec.decided_at = now_utc

        # Step 2: Cascade task mutations for the flagship OPTION_B scenario
        if decision_id == "DEC-2026-001" and body.selected_option == "OPTION_B_RECOMMENDED":
            # Resolve TSK-02 (CFO variance approval task)
            tsk02 = db.query(WorkflowTask).filter(
                WorkflowTask.task_id == "TSK-02"
            ).first()
            if tsk02:
                tsk02.status = "COMPLETED"
                tasks_mutated.append(MutatedTask(
                    task_id="TSK-02",
                    new_status="COMPLETED",
                    new_due_date=str(tsk02.due_date),
                    blocker_note="Resolved via CFO Decision DEC-2026-001",
                ))

            # Resolve TSK-03 (payroll lock conflict → extended cutoff)
            tsk03 = db.query(WorkflowTask).filter(
                WorkflowTask.task_id == "TSK-03"
            ).first()
            if tsk03:
                tsk03.due_date = "2026-10-25"
                tsk03.status = "SCHEDULE_ALIGNED"
                tsk03.blocker_note = (
                    "Resolved via CFO Decision DEC-2026-001: "
                    "Cutoff extended to Oct 25"
                )
                tasks_mutated.append(MutatedTask(
                    task_id="TSK-03",
                    new_status="SCHEDULE_ALIGNED",
                    new_due_date="2026-10-25",
                    blocker_note=tsk03.blocker_note,
                ))

        db.commit()
        db.refresh(dec)
        # ─────────────────────────────────────────────────────────────────────

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction failed and was rolled back: {str(exc)}",
        ) from exc

    return ApproveDecisionResponse(
        decision_id=dec.decision_id,
        status=dec.status,
        selected_option=dec.selected_option,
        decided_at=dec.decided_at.isoformat() if dec.decided_at else now_utc.isoformat(),
        tasks_mutated=tasks_mutated,
    )
