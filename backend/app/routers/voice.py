"""
StrataIQ Voice API Router (routers/voice.py)

Endpoints for Pointed Document Voice & Audio Citation Studio:
  - GET  /api/v1/voice/catalog       — Accessible documents & role-specific 1-click voice prompts
  - POST /api/v1/voice/talk-to-docs  — Pointed voice Q&A, TTS audio synthesis, visual citation coordinates
  - POST /api/v1/voice/transcribe    — Multimodal STT with strict Indian English normalization
"""
from __future__ import annotations

import base64
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import SecurityContext, get_db, get_security_context
from app.models import Document
from app.schemas import (
    DocumentItem,
    PointedDocVoiceRequest,
    PointedDocVoiceResponse,
    VoiceCatalogResponse,
    VoiceSamplePrompt,
    VoiceTranscribeRequest,
    VoiceTranscribeResponse,
)
from app.voice.pointed_doc_agent import PointedDocVoiceAgent
from app.voice.speech_service import SpeechService

router = APIRouter()
voice_agent = PointedDocVoiceAgent()
speech_service = SpeechService()


# ── Role-Specific 1-Click Sample Prompts ───────────────────────────────────────

ROLE_SAMPLE_PROMPTS = {
    "UPPER": [
        VoiceSamplePrompt(
            prompt_id="PRM-UPPER-01",
            title="Parental Premium Variance & Option B",
            spoken_text="What is the unbudgeted parental premium variance and how does Option B resolve it?",
            pointed_doc_ids=["DOC-008", "DOC-005"],
            category="Strategic Financial Decision",
        ),
        VoiceSamplePrompt(
            prompt_id="PRM-UPPER-02",
            title="Executive Committee Transition Sign-off",
            spoken_text="Review executive vendor transition sign-off transcript and actuarial assumptions.",
            pointed_doc_ids=["DOC-017", "DOC-015"],
            category="Actuarial & Legal Signoff",
        ),
        VoiceSamplePrompt(
            prompt_id="PRM-UPPER-03",
            title="Departmental Cost & EBITDA Allocation",
            spoken_text="What are the department-level EBITDA and cost allocations under NovaShield MSA?",
            pointed_doc_ids=["DOC-005", "DOC-002"],
            category="Department Cost Allocation",
        ),
    ],
    "MIDDLE": [
        VoiceSamplePrompt(
            prompt_id="PRM-MID-01",
            title="TSK-03 vs TSK-05 Schedule Collision",
            spoken_text="Detect cross-silo schedule collisions between Finance payroll cutoff and IT SSO launch.",
            pointed_doc_ids=["DOC-018", "DOC-016"],
            category="Cross-Department Schedule Collision",
        ),
        VoiceSamplePrompt(
            prompt_id="PRM-MID-02",
            title="Stuck Transition Hospital Claims",
            spoken_text="What is the audit status of the 12 stuck transition hospital reimbursement claims?",
            pointed_doc_ids=["DOC-007", "DOC-013"],
            category="Claims Audit War-Room",
        ),
        VoiceSamplePrompt(
            prompt_id="PRM-MID-03",
            title="Employee Census & Parental Opt-In Tracker",
            spoken_text="Review employee dependent census migration count and pending parental rider opt-ins.",
            pointed_doc_ids=["DOC-009", "DOC-006"],
            category="HR Operations & Census",
        ),
    ],
    "LOWER": [
        VoiceSamplePrompt(
            prompt_id="PRM-LOW-01",
            title="Sahyadri Hospital Cataract Surgery Cashless",
            spoken_text="Is Sahyadri Hospital in Pune network cashless for my father's cataract surgery under NovaShield?",
            pointed_doc_ids=["DOC-011", "DOC-010"],
            category="Personal Health Benefits",
        ),
        VoiceSamplePrompt(
            prompt_id="PRM-LOW-02",
            title="Emergency Blackout Hospitalization SOP",
            spoken_text="What is the emergency pre-authorization SLA during the transition blackout period?",
            pointed_doc_ids=["DOC-012"],
            category="Emergency Hospital SOP",
        ),
        VoiceSamplePrompt(
            prompt_id="PRM-LOW-03",
            title="Excluded Treatments & Cataract Sublimit",
            spoken_text="What are the specific excluded treatments and cataract sub-limits in NovaShield?",
            pointed_doc_ids=["DOC-021"],
            category="Policy Sublimits & Exclusions",
        ),
    ],
}


@router.get("/catalog", response_model=VoiceCatalogResponse)
def get_voice_catalog(
    ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db),
) -> VoiceCatalogResponse:
    """
    Get accessible documents for current user under Zero-Trust RLS,
    plus 3 tailored 1-click voice prompts matching the user's role layer.
    """
    docs = (
        db.query(Document)
        .filter(Document.min_layer_clearance <= ctx.clearance_level)
        .order_by(Document.doc_id.asc())
        .all()
    )

    doc_items = [
        DocumentItem(
            doc_id=d.doc_id,
            file_name=d.file_name,
            file_type=d.file_type,
            dept_id=d.dept_id,
            min_layer_clearance=d.min_layer_clearance,
            version=d.version,
            chunk_count=len(d.chunks),
            gcs_uri=d.gcs_uri,
            uploaded_by=d.uploaded_by,
        )
        for d in docs
    ]

    prompts = ROLE_SAMPLE_PROMPTS.get(ctx.layer_code, ROLE_SAMPLE_PROMPTS["LOWER"])

    return VoiceCatalogResponse(
        user_clearance_level=ctx.clearance_level,
        accessible_documents=doc_items,
        sample_voice_prompts=prompts,
    )


@router.post("/talk-to-docs", response_model=PointedDocVoiceResponse)
def talk_to_documents(
    body: PointedDocVoiceRequest,
    ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db),
) -> PointedDocVoiceResponse:
    """
    Pointed Document Voice Studio:
    1. Validates Zero-Trust clearance on pointed documents (403 if unauthorized)
    2. Runs hybrid vector + BM25 search across pointed docs
    3. Retrieves role-scoped SQL context
    4. Synthesizes spoken script and display answer with groundedness evaluation
    5. Formats declarative OpenUI (openui-lang) with live telemetry
    6. Generates high-definition audio via SpeechService (Gemini Native TTS Kore)
    7. Returns primary citation coordinates for yellow visual highlighting
    """
    return voice_agent.talk_to_docs(
        query=body.query,
        pointed_doc_ids=body.pointed_doc_ids,
        ctx=ctx,
        db=db,
        language_code=body.language_code,
        voice_speed=body.voice_speed,
        ui_mode=body.ui_mode,
    )


@router.post("/transcribe", response_model=VoiceTranscribeResponse)
def transcribe_audio_endpoint(
    body: VoiceTranscribeRequest,
    ctx: SecurityContext = Depends(get_security_context),
) -> VoiceTranscribeResponse:
    """
    Transcribe spoken voice audio or fallback prompt text with strict en-IN language normalization.
    """
    raw_audio = None
    if body.audio_base64:
        try:
            raw_audio = base64.b64decode(body.audio_base64)
        except Exception:
            raw_audio = None

    result = speech_service.transcribe_audio(
        audio_bytes=raw_audio,
        fallback_text=body.fallback_text,
        language_code=body.language_code,
    )

    return VoiceTranscribeResponse(
        transcription=result["transcription"],
        confidence=result.get("confidence", 0.95),
        language_code=result["language_code"],
        language_lock_enforced=result["language_lock_enforced"],
        transcription_engine=result["transcription_engine"],
    )
