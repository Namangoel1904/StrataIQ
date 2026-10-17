"""
StrataIQ Phase 1 Pytest Fixtures

Uses the real local_enterprise.db (Zero-Mock policy).
Provides make_client() helper to create TestClient instances
with a pre-set X-User-Id header for any persona.
"""
import sys
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure the backend/app package is importable from the tests directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


@pytest.fixture(scope="session")
def client():
    """Base TestClient — uses default X-User-Id (USR-LOW-ENG-005)."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def make_client(user_id: str) -> TestClient:
    """
    Factory: returns a TestClient whose every request carries
    the given X-User-Id header, simulating that persona's session.
    """
    return TestClient(
        app,
        headers={"X-User-Id": user_id},
        raise_server_exceptions=True,
    )


# ── Persona-specific fixtures ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def lower_client():
    """USR-LOW-ENG-005 — Naman Goel, Senior Engineer, Clearance 1."""
    return make_client("USR-LOW-ENG-005")


@pytest.fixture(scope="session")
def middle_hr_client():
    """USR-MID-HR-003 — Priya Kulkarni, HR Lead, Clearance 2."""
    return make_client("USR-MID-HR-003")


@pytest.fixture(scope="session")
def upper_cfo_client():
    """USR-UPPER-FIN-001 — Arvind Mehta, CFO, Clearance 3."""
    return make_client("USR-UPPER-FIN-001")


@pytest.fixture(scope="session")
def no_auth_client():
    """No X-User-Id header — used for public endpoints (reset, personas)."""
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture(autouse=True, scope="session")
def ensure_clean_demo_state(no_auth_client):
    """
    Session-scoped fixture that resets demo state BEFORE the test session starts,
    ensuring a deterministic baseline regardless of previous runs.
    """
    resp = no_auth_client.post("/api/v1/workspace/reset-demo-state")
    assert resp.status_code == 200, f"Pre-test reset failed: {resp.text}"
    yield
    # Reset again after session so the DB is clean for future runs
    no_auth_client.post("/api/v1/workspace/reset-demo-state")
