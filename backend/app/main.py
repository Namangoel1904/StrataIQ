import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
        "service": "StrataIQ Enterprise",
        "version": "1.0.0",
        "cloud_run_ready": True,
    }


# ── Locate Compiled Frontend SPA (React + Vite) ──────────────────────────────
def _find_frontend_dist() -> Path | None:
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
        Path("/app/frontend/dist"),
        Path(__file__).resolve().parent.parent / "static_ui",
    ]
    for c in candidates:
        if c.exists() and (c / "index.html").exists():
            return c
    return None


frontend_dist = _find_frontend_dist()

if frontend_dist:
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", tags=["Frontend SPA"])
    def root_spa():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}", tags=["Frontend SPA"])
    def catchall_spa(full_path: str):
        if (
            full_path.startswith("api/")
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path == "openapi.json"
        ):
            raise HTTPException(status_code=404, detail="API route not found")
        # If requesting a specific file that exists in dist (e.g. favicon.ico, etc.)
        target = frontend_dist / full_path
        if target.is_file():
            return FileResponse(target)
        # Otherwise fallback to index.html for client-side routing
        return FileResponse(frontend_dist / "index.html")

else:
    @app.get("/", tags=["Health"])
    def root():
        return {
            "message": "StrataIQ Enterprise API is running. Visit /docs for the interactive API explorer.",
            "phase": "Production Ready (Frontend not built locally)",
        }
