"""
StrataIQ Database Engine, Session Factory & Zero-Trust SecurityContext Dependency

Dual-engine support:
- Local dev:    sqlite:///./enterprise_data_vault/rdbms/local_enterprise.db
- Production:   DATABASE_URL env var → Google Cloud SQL PostgreSQL / AlloyDB
"""
import json
from dataclasses import dataclass
from typing import Generator

from fastapi import Header, HTTPException, status, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings
from app.models import Base, User, OrgLayer, Department

# ---------------------------------------------------------------------------
# Engine & Session Factory
# ---------------------------------------------------------------------------

settings = get_settings()

_connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.effective_db_url,
    connect_args=_connect_args,
    # Pool settings suited for FastAPI async context
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Zero-Trust Security Context
# ---------------------------------------------------------------------------

@dataclass
class SecurityContext:
    """
    Resolved per-request security principal.
    Carries the authenticated user's full identity and clearance level
    that is used to enforce Row-Level Security throughout all routers.
    """
    user_id: str
    full_name: str
    email: str
    job_title: str
    grade_tier: str

    dept_id: str
    dept_name: str

    layer_id: int
    layer_code: str      # 'UPPER' | 'MIDDLE' | 'LOWER'
    clearance_level: int  # 3 | 2 | 1

    ui_preferences: dict  # parsed from ui_preferences_json


def get_security_context(
    x_user_id: str = Header(default="USR-LOW-ENG-005", alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> SecurityContext:
    """
    FastAPI dependency.
    Resolves X-User-Id header → SecurityContext by joining
    users ▷ org_layers ▷ departments from the real database.
    Raises 401 if the user_id is not found.
    """
    row = (
        db.query(User, OrgLayer, Department)
        .join(OrgLayer, User.layer_id == OrgLayer.layer_id)
        .join(Department, User.dept_id == Department.dept_id)
        .filter(User.user_id == x_user_id)
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User '{x_user_id}' not found in the enterprise directory.",
        )

    user, org_layer, department = row

    # Parse ui_preferences_json — stored as a JSON string in SQLite
    try:
        ui_prefs = json.loads(user.ui_preferences_json) if user.ui_preferences_json else {}
    except (json.JSONDecodeError, TypeError):
        ui_prefs = {}

    return SecurityContext(
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


# ---------------------------------------------------------------------------
# Zero-Trust RLS Assertion Helpers
# ---------------------------------------------------------------------------

def assert_document_clearance(doc_min_clearance: int, ctx: SecurityContext) -> None:
    """
    Raises HTTP 403 if the user's clearance level is below the
    document's minimum required clearance.
    """
    if doc_min_clearance > ctx.clearance_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. Document requires Clearance Level {doc_min_clearance}, "
                f"but '{ctx.user_id}' has Clearance Level {ctx.clearance_level} "
                f"({ctx.layer_code} layer)."
            ),
        )


def assert_upper_only(ctx: SecurityContext) -> None:
    """
    Raises HTTP 403 unless the user is UPPER layer (clearance_level == 3).
    Used for executive decision approvals.
    """
    if ctx.clearance_level < 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. This action requires UPPER layer (Clearance 3). "
                f"'{ctx.user_id}' has Clearance Level {ctx.clearance_level} ({ctx.layer_code})."
            ),
        )


def assert_at_least_middle(ctx: SecurityContext) -> None:
    """
    Raises HTTP 403 if the user is LOWER layer (clearance_level < 2).
    Used for viewing executive decision logs.
    """
    if ctx.clearance_level < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. This resource requires MIDDLE or UPPER layer access. "
                f"'{ctx.user_id}' has Clearance Level {ctx.clearance_level} ({ctx.layer_code})."
            ),
        )
