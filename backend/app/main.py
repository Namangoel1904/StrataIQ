"""
StrataIQ FastAPI Application Entry Point

Mounts all Phase 1 routers under /api/v1 with CORS enabled for frontend dev.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import workspace, documents, decisions, agent, voice

app = FastAPI(
    title="StrataIQ Enterprise API",
    description=(
        "Role-Adaptive Enterprise Knowledge, Voice & Decision Copilot — "
        "Google Cloud AI Builder Cup 2026. "
        "Enforces Zero-Trust Row-Level Security on every endpoint."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — Allow all origins in dev; restrict in production via env ───────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(
    workspace.router,
    prefix="/api/v1/workspace",
    tags=["Workspace"],
)
app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["Documents"],
)
app.include_router(
    decisions.router,
    prefix="/api/v1/decisions",
    tags=["Decisions"],
)
app.include_router(
    agent.router,
    prefix="/api/v1/agent",
    tags=["Agent Multi-Agent Engine"],
)
app.include_router(
    voice.router,
    prefix="/api/v1/voice",
    tags=["Voice Studio & Citations"],
)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe for Cloud Run / load balancer."""
    return {
        "status": "ok",
        "service": "StrataIQ Phase 1",
        "version": "1.0.0",
    }


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "StrataIQ Enterprise API is running. Visit /docs for the interactive API explorer.",
        "phase": "Phase 1 — Backend Core & Zero-Trust RLS Engine",
    }
