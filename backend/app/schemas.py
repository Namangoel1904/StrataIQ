"""
StrataIQ Pydantic v2 Schemas — Strict request/response models for all Phase 1 endpoints.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# User & Security Context
# ---------------------------------------------------------------------------

class UserContext(BaseModel):
    user_id: str
    full_name: str
    email: str
    job_title: str
    grade_tier: str
    dept_id: str
    dept_name: str
    layer_id: int
    layer_code: str        # UPPER | MIDDLE | LOWER
    clearance_level: int   # 3 | 2 | 1
    ui_preferences: dict


class PersonasResponse(BaseModel):
    personas: list[UserContext]


# ---------------------------------------------------------------------------
# Layout / Workspace Bootstrap
# ---------------------------------------------------------------------------

class LayoutModuleBlock(BaseModel):
    module_id: str
    title: str
    component: str
    props: dict = Field(default_factory=dict)


class LayoutConfig(BaseModel):
    layer_code: str
    dept_id: str
    modules: list[LayoutModuleBlock]


# ---------------------------------------------------------------------------
# Role-Scoped KPIs (typed per layer, returned as dict in BootstrapResponse)
# ---------------------------------------------------------------------------

class EnrollmentRecord(BaseModel):
    enrollment_id: str
    user_id: str
    policy_id: str
    sum_insured: int
    dependents_count: int
    parental_opt_in: str
    monthly_copay_deduction: int
    migration_status: str


class WorkflowTaskItem(BaseModel):
    task_id: str
    dept_id: str
    assigned_to_user_id: str
    layer_id: int
    title: str
    due_date: str
    status: str
    dependency_task_id: Optional[str] = None
    blocker_note: Optional[str] = None


class ClaimItem(BaseModel):
    claim_id: str
    user_id: str
    policy_id: str
    hospital_name: str
    city: str
    treatment_type: str
    claim_amount: float
    claim_stage: str
    assigned_hr_id: str
    blocker_reason: str


class ConflictAlert(BaseModel):
    conflict_id: str
    description: str
    task_a_id: str
    task_a_title: str
    task_a_due: str
    task_b_id: str
    task_b_title: str
    task_b_due: str
    employees_blocked: int
    claims_amount_inr: float


# Upper-layer KPIs
class UpperKPIs(BaseModel):
    novashield_annual_premium_inr: float
    parental_premium_variance_inr: float
    legacycare_prorata_refund_inr: float
    pending_executive_decisions: int
    cross_dept_conflicts: int


# Middle-layer KPIs
class MiddleKPIs(BaseModel):
    employees_blocked_parental_rider: int
    stuck_transition_claims_count: int
    stuck_transition_claims_amount_inr: float
    p0_p1_escalations: int
    conflict_alert: Optional[ConflictAlert]


# Lower-layer KPIs
class LowerKPIs(BaseModel):
    enrollment: Optional[EnrollmentRecord]
    assigned_tasks: list[WorkflowTaskItem]
    personal_claims: list[ClaimItem]


class BootstrapResponse(BaseModel):
    user_profile: UserContext
    layout_config: LayoutConfig
    role_scoped_kpis: dict[str, Any]   # UpperKPIs | MiddleKPIs | LowerKPIs serialized


# ---------------------------------------------------------------------------
# Parental Rider Confirmation
# ---------------------------------------------------------------------------

class ConfirmParentalRiderResponse(BaseModel):
    message: str
    enrollment: EnrollmentRecord


class ResetDemoStateResponse(BaseModel):
    message: str
    reset_items: list[str]


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

class DocumentItem(BaseModel):
    doc_id: str
    file_name: str
    file_type: str
    dept_id: str
    min_layer_clearance: int
    version: str
    chunk_count: int
    gcs_uri: str
    uploaded_by: str


class DocumentsListResponse(BaseModel):
    accessible_docs: list[DocumentItem]
    restricted_hidden_count: int
    total_docs: int
    clearance_level: int


class DocumentChunk(BaseModel):
    chunk_id: str
    page_number: int
    section_title: str
    chunk_text: str


class DocumentContentResponse(BaseModel):
    doc_id: str
    file_name: str
    file_type: str
    chunks: list[DocumentChunk]
    csv_rows: Optional[list[dict]] = None   # Only populated for CSV files


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------

class DecisionOption(BaseModel):
    option_code: str
    label: str
    net_company_cost_inr: int
    employee_monthly_impact_inr: int
    cutoff_resolution: str
    risk_level: str


class DecisionMatrixItem(BaseModel):
    decision_id: str
    triggered_by_doc_id: str
    approver_user_id: str
    title: str
    status: str
    options: list[DecisionOption]
    selected_option: str
    financial_impact: float
    eval_grounding_score: float
    decided_at: Optional[str] = None


class DecisionsListResponse(BaseModel):
    decisions: list[DecisionMatrixItem]


class ApproveDecisionRequest(BaseModel):
    selected_option: str = Field(
        ...,
        description="Option code to approve, e.g. OPTION_B_RECOMMENDED",
        examples=["OPTION_B_RECOMMENDED"],
    )


class MutatedTask(BaseModel):
    task_id: str
    new_status: str
    new_due_date: Optional[str]
    blocker_note: Optional[str]


class ApproveDecisionResponse(BaseModel):
    decision_id: str
    status: str
    selected_option: str
    decided_at: str
    tasks_mutated: list[MutatedTask]


# ---------------------------------------------------------------------------
# Phase 2: Multi-Agent Engine Schemas
# ---------------------------------------------------------------------------

class AgentQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question or request")
    doc_id: Optional[str] = Field(None, description="Optional target doc_id to narrow search")
    override_intent: Optional[str] = Field(None, description="Optional manual override of router intent")
    top_k: int = Field(default=5, ge=1, le=20, description="Max citation chunks to retrieve")
    ui_mode: str = Field(default="openui", description="UI rendering mode: 'openui' or 'legacy'")


class CitationResponse(BaseModel):
    doc_id: str
    file_name: str
    page_number: int
    section_title: str
    snippet: str
    relevance_score: float


class SQLDataResponse(BaseModel):
    query_type: str
    sql_query: str
    row_count: int
    rows: list[dict[str, Any]]
    metrics: dict[str, Any]
    summary: Optional[str] = None


class AgentQueryResponse(BaseModel):
    query: str
    intent: str
    answer: str
    citations: list[CitationResponse]
    groundedness_score: float
    is_grounded: bool
    hallucination_detected: bool
    reasoning: str
    sql_data: Optional[SQLDataResponse] = None
    user_context: dict[str, Any]
    execution_metadata: dict[str, Any]
    openui_lang: Optional[str] = None
    openui_telemetry: Optional[dict[str, Any]] = None


class AgentRouteRequest(BaseModel):
    query: str = Field(..., description="User query to classify")


class AgentRouteResponse(BaseModel):
    query: str
    intent: str
    keywords: list[str]
    doc_hints: list[str]
    sql_hints: list[str]
    reasoning: str


class SDKStatusResponse(BaseModel):
    status: str
    google_adk_version: str
    google_genai_version: str
    tinker_version: str
    backboard_sdk_version: str
    embedded_chunks_count: int
    total_chunks_count: int
    embedding_dimension: int
    embedding_model: str
    providers: dict[str, Any]


# ---------------------------------------------------------------------------
# Phase 3: Thesys OpenUI Benchmark Schemas
# ---------------------------------------------------------------------------

class OpenUIBenchmarkRequest(BaseModel):
    query: str = Field(..., description="Query to benchmark across OpenUI vs Legacy formats")
    doc_hints: Optional[list[str]] = Field(None, description="Optional doc hints")


class OpenUIBenchmarkResponse(BaseModel):
    query: str
    intent: str
    openui_latency_ms: float
    legacy_latency_ms: float
    speedup_multiplier: float
    openui_tokens: int
    legacy_tokens: int
    token_reduction_pct: float
    estimated_llm_decode_saved_ms: float
    openui_lang_code: str
    legacy_verbose_payload: dict[str, Any]
    user_context: dict[str, Any]


# ---------------------------------------------------------------------------
# Phase 3: Voice & Pointed Document Studio Schemas
# ---------------------------------------------------------------------------

class VoicePrimaryCitation(BaseModel):
    doc_id: str
    file_name: str
    page_number: int
    section_title: str
    chunk_text: str
    highlight_snippet: str
    relevance_score: float


class PointedDocVoiceRequest(BaseModel):
    query: str = Field(..., description="Spoken or typed query targeting specific documents")
    pointed_doc_ids: list[str] = Field(default_factory=list, description="Explicit document IDs to scope search to")
    language_code: str = Field(default="en-IN", description="Speech language ('en-IN' or 'en-US')")
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech playback speed")
    ui_mode: str = Field(default="openui", description="'openui' for declarative OpenUI lang, 'legacy' for verbose JSON")


class PointedDocVoiceResponse(BaseModel):
    query: str
    spoken_answer: str
    display_answer: str
    audio_base64: str
    audio_content_type: str
    duration_seconds: float
    tts_engine: str
    voice_name: str
    language_code: str
    language_lock_enforced: bool
    pointed_doc_ids: list[str]
    primary_citation: Optional[VoicePrimaryCitation] = None
    citations: list[CitationResponse]
    groundedness_score: float
    is_grounded: bool
    openui_lang: str
    openui_telemetry: dict[str, Any]
    latency_breakdown_ms: dict[str, float]
    user_context: dict[str, Any]


class VoiceSamplePrompt(BaseModel):
    prompt_id: str
    title: str
    spoken_text: str
    pointed_doc_ids: list[str]
    category: str


class VoiceCatalogResponse(BaseModel):
    user_clearance_level: int
    accessible_documents: list[DocumentItem]
    sample_voice_prompts: list[VoiceSamplePrompt]


class VoiceTranscribeRequest(BaseModel):
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio bytes (WAV/WEBM)")
    fallback_text: Optional[str] = Field(None, description="Fallback prompt text for test/demo")
    language_code: str = Field(default="en-IN", description="Input spoken language code")


class VoiceTranscribeResponse(BaseModel):
    transcription: str
    confidence: float
    language_code: str
    language_lock_enforced: bool
    transcription_engine: str


