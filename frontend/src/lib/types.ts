export interface UserContext {
  user_id: string
  full_name: string
  email: string
  job_title: string
  grade_tier: string
  dept_id: string
  dept_name: string
  layer_id: number
  layer_code: 'UPPER' | 'MIDDLE' | 'LOWER'
  clearance_level: number
  ui_preferences: {
    theme?: string
    recent_queries?: { query: string; intent?: string }[]
    [key: string]: any
  }
}

export interface UpperKPIs {
  parental_premium_variance_inr: number
  legacycare_prorata_refund_inr: number
  novashield_annual_premium_inr: number
  pending_executive_decisions: number
  [key: string]: any
}

export interface TaskNodeData {
  task_id: string
  title: string
  due_date: string
  status?: string
  blocker_note?: string
}

export interface ConflictAlert {
  conflict_id: string
  title: string
  description: string
  employees_blocked: number
  claims_amount_inr: number
  task_a_id: string
  task_a_title: string
  task_a_due: string
  task_b_id: string
  task_b_title: string
  task_b_due: string
  [key: string]: any
}

export interface MiddleKPIs {
  employees_blocked_parental_rider: number
  stuck_transition_claims_count: number
  stuck_transition_claims_amount_inr: number
  p0_p1_escalations: number
  payroll_lock_date?: string
  sso_launch_date?: string
  conflict_alert?: ConflictAlert
  [key: string]: any
}

export interface ClaimItem {
  claim_id: string
  user_id: string
  employee_name: string
  hospital_name: string
  city: string
  treatment_type: string
  claim_amount: number
  claim_stage: string
  blocker_reason?: string
  admitted_date?: string
  is_emergency?: boolean
  [key: string]: any
}

export interface LowerKPIs {
  enrollment?: {
    policy_id: string
    sum_insured: number
    dependents_count: number
    monthly_copay_deduction: number
    parental_opt_in: string
    migration_status: string
    [key: string]: any
  }
  assigned_tasks: TaskNodeData[]
  personal_claims: ClaimItem[]
  [key: string]: any
}

export interface DecisionOption {
  option_id: string
  label?: string
  title: string
  description: string
  financial_impact_inr?: number
  financial_impact?: number
  risk_assessment?: string
  recommended?: boolean
  [key: string]: any
}

export interface DecisionMatrixItem {
  decision_id: string
  title: string
  status: string
  approver_user_id: string
  selected_option?: string
  financial_impact: number
  eval_grounding_score: number
  decided_at?: string
  options: DecisionOption[]
  [key: string]: any
}

export interface BootstrapResponse {
  user_profile: UserContext
  role_scoped_kpis: UpperKPIs | MiddleKPIs | LowerKPIs
  recent_claims?: ClaimItem[]
  active_decision?: DecisionMatrixItem
  conflict_alert?: ConflictAlert
  [key: string]: any
}

export interface DocumentItem {
  doc_id: string
  file_name: string
  file_type: string
  min_layer_clearance: number
  version?: string
  chunk_count?: number
  summary?: string
  category?: string
  [key: string]: any
}

export interface DocumentsListResponse {
  total_documents: number
  user_clearance_level: number
  accessible_docs: DocumentItem[]
  locked_docs: DocumentItem[]
  [key: string]: any
}

export interface VoiceItem {
  voice_id: string
  display_name: string
  language_code: string
  gender: string
  tts_engine: string
  description?: string
  [key: string]: any
}

export interface VoiceCatalogResponse {
  total_voices: number
  default_voice: string
  voices: VoiceItem[]
  sample_voice_prompts?: {
    label: string
    spoken_text: string
    pointed_doc_ids: string[]
  }[]
  [key: string]: any
}

export interface VoicePrimaryCitation {
  doc_id: string
  file_name: string
  page_number: number
  section_title: string
  chunk_text: string
  highlight_snippet: string
  relevance_score: number
  [key: string]: any
}

export interface Citation {
  doc_id: string
  file_name: string
  page_number: number
  section_title: string
  relevance_score?: number
  snippet?: string
  chunk_text?: string
  highlight_snippet?: string
  [key: string]: any
}

export interface DocumentChunk {
  chunk_id: string
  doc_id: string
  page_number: number
  section_title: string
  chunk_text: string
  [key: string]: any
}

export interface DocumentContentResponse {
  doc_id: string
  file_name: string
  file_type: string
  min_layer_clearance: number
  total_chunks: number
  chunks: DocumentChunk[]
  [key: string]: any
}

export interface TalkToDocsResponse {
  query: string
  spoken_answer: string
  display_answer: string
  audio_base64?: string
  audio_content_type?: string
  duration_seconds?: number
  tts_engine?: string
  voice_name?: string
  language_code?: string
  language_lock_enforced?: boolean
  pointed_doc_ids?: string[]
  primary_citation?: VoicePrimaryCitation
  citations?: Citation[]
  groundedness_score?: number
  is_grounded?: boolean
  openui_lang?: string
  openui_telemetry?: any
  latency_breakdown_ms?: any
  user_context?: any
  [key: string]: any
}

export interface OpenUIBenchmark {
  query: string
  doc_id?: string
  openui_tokens: number
  legacy_tokens: number
  openui_latency_ms: number
  legacy_latency_ms: number
  speedup: number
  openui_source: string
  legacy_source: string
  [key: string]: any
}
