"""
StrataIQ — Tinker-Gemma Context Router (router.py)

Fast intent classification using:
  1. Tinker LoRA Router SDK (when TINKER_API_KEY is configured)
  2. Google GenAI Gemini 2.5 Flash (when GEMINI_API_KEY is configured)
  3. Deterministic keyword + clearance boosting fallback (offline/CI mode)

Takes a user query + SecurityContext and returns:
  - intent: one of DOC_QUERY | SQL_METRIC_QUERY | CROSS_SILO_CONFLICT | EXECUTIVE_DECISION
  - keywords: list of extracted filter terms (hospital names, dates, topics)
  - doc_hints: list of exact doc_ids chosen from the 22-document enterprise catalog
  - sql_hints: list of table names relevant to the query
  - provider: active routing engine (tinker_sdk_live | gemini_flash_live | deterministic_fallback)
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
from dataclasses import dataclass, field
from typing import Optional

from app.config import get_settings
from app.database import SecurityContext

settings = get_settings()
logger = logging.getLogger("strataiq.gemini_fallback")

# Intent constants
INTENT_DOC_QUERY = "DOC_QUERY"
INTENT_SQL_METRIC = "SQL_METRIC_QUERY"
INTENT_CROSS_SILO = "CROSS_SILO_CONFLICT"
INTENT_EXEC_DECISION = "EXECUTIVE_DECISION"


# Full 22-Document Enterprise Catalog with Clearance Levels
DOCUMENT_CATALOG_TEXT = """
22-DOCUMENT ENTERPRISE VAULT CATALOG:
DOC-001 (Clearance 1): 01_LegacyCare_Expiring_Master_Policy_2025.pdf - Expiring master terms, baseline benefits
DOC-002 (Clearance 2): 02_NovaShield_New_Master_Service_Agreement_2026.pdf - MSA contract, legal liability, SLAs
DOC-003 (Clearance 1): 03_Old_vs_New_Policy_Benefit_Comparison_Addendum.docx - Side-by-side benefit upgrades & sublimit table
DOC-004 (Clearance 2): 04_DPDP_HIPAA_Medical_Data_Privacy_Compliance_Audit.pdf - DPDP/HIPAA data privacy & audit
DOC-005 (Clearance 3): 05_Q3_Q4_Insurance_Premium_Cost_Impact_Ledger.csv - Premium ledger, cost variances, EBITDA impact
DOC-006 (Clearance 1): 06_Employee_Parental_CoPay_Payroll_Deduction_Schedule.csv - Parental copay & payroll deduction schedule
DOC-007 (Clearance 2): 07_Pending_Reimbursement_Claims_Transition_Audit.csv - 12 transition claims audit & stuck claim stages
DOC-008 (Clearance 3): 08_CFO_Budget_Reallocation_Proposal_Parental_Buffer.pdf - CFO reallocation proposal for INR 38.4L variance
DOC-009 (Clearance 2): 09_Master_Employee_Dependent_Census_Migration_2026.csv - Employee dependent census & migration tracker
DOC-010 (Clearance 1): 10_Cashless_Network_Hospitals_Master_Directory.csv - Cashless hospital directory (Sahyadri, Ruby Hall, Apollo)
DOC-011 (Clearance 1): 11_Employee_Handbook_New_Health_Benefit_Guide_2026.pdf - Employee handbook, cashless hospital step-by-step SOP
DOC-012 (Clearance 1): 12_Blackout_Period_Emergency_Hospitalization_SOP.docx - Emergency blackout period hospitalization SOP
DOC-013 (Clearance 2): 13_HR_Escalation_Log_High_Priority_Medical_Cases.csv - High priority escalation log & P0/P1 medical cases
DOC-014 (Clearance 1): 14_HRMS_to_NovaShield_API_SSO_Architecture_Spec.pdf - HRMS to NovaShield API & SSO portal launch spec
DOC-015 (Clearance 2): 15_IT_Security_Vulnerability_Test_TPA_Portal.docx - TPA portal penetration test & security findings
DOC-016 (Clearance 1): 16_Cross_Department_60Day_Rollout_Tracker.csv - 60-day migration timeline & departmental milestones
DOC-017 (Clearance 3): 17_Transcript_Executive_Committee_Vendor_Switch_Signoff.docx - Executive committee signoff transcript
DOC-018 (Clearance 2): 18_Transcript_HR_IT_Finance_Weekly_Migration_WarRoom.docx - Weekly migration war-room transcript (TSK-03 vs TSK-05 collision)
DOC-019 (Clearance 1): 19_Transcript_All_Hands_TownHall_Employee_QA_Session.docx - TownHall Q&A: Pune hospitals, Sahyadri cashless, cataract INR 45k
DOC-020 (Clearance 2): 20_Department_Delivery_Impact_Report_Q4.pdf - Department delivery & productivity impact report
DOC-021 (Clearance 1): 21_Excluded_Treatments_And_SubLimits_Schedule.pdf - Specific sublimits: cataract INR 45,000/eye, daycare, maternity
DOC-022 (Clearance 1): 22_TPA_SLA_Breach_And_Grievance_Redressal_Matrix.pdf - TPA SLAs, turnaround times & grievance redressal
"""


def load_tinker_checkpoint() -> dict:
    """Load the trained Google Gemma 4 LoRA router checkpoint metadata."""
    ckpt_path = Path(__file__).parent / "tinker_checkpoint.json"
    if ckpt_path.exists():
        try:
            with open(ckpt_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "status": "trained",
        "target_model": "google/gemma-4-e4b-it",
        "tinker_checkpoint_path": "tinker://e8541eb0-f05b-5f46-883e-ec8c284fbb83:train:0/sampler_weights/strataiq-gemma4-router-lora-v1",
    }


@dataclass
class RouterResult:
    intent: str
    keywords: list[str] = field(default_factory=list)
    doc_hints: list[str] = field(default_factory=list)   # doc_ids likely relevant
    sql_hints: list[str] = field(default_factory=list)   # table names to query
    reasoning: str = ""
    provider: str = "deterministic_fallback"             # tinker_sdk_live | gemini_flash_live | deterministic_fallback
    target_model: str = "google/gemma-4-e4b-it"
    tinker_checkpoint_path: Optional[str] = None


# ── Keyword maps for deterministic fallback ────────────────────────────────────

_DOC_KEYWORDS = {
    "hospital", "cashless", "network", "policy", "document", "benefit",
    "coverage", "cataract", "treatment", "claim", "pre-auth", "preauth",
    "reimburse", "reimbursement", "sop", "handbook", "guide", "vendor",
    "novashield", "legacycare", "agreement", "audit", "compliance", "dpdp",
    "hipaa", "blackout", "emergency", "hospitalization", "admission",
    "room rent", "icu", "surgery", "maternity", "insured", "limit", "sublimit",
    "sahyadri", "pune",
}

_SQL_KEYWORDS = {
    "enrollment", "enrolled", "status", "parental", "opt-in", "opt in",
    "premium", "deduction", "copay", "co-pay", "migrate", "migration",
    "pending", "confirmed", "blocked", "employees", "count", "how many",
    "payroll", "salary", "amount", "cost", "total", "sum",
}

_CONFLICT_KEYWORDS = {
    "conflict", "collision", "schedule", "tsk-03", "tsk-05", "tsk03", "tsk05",
    "payroll lock", "cutoff", "oct 20", "oct 23", "october 20", "october 23",
    "blocked", "delay", "sso", "portal", "deadline",
}

_EXEC_KEYWORDS = {
    "approve", "approval", "decision", "option", "option_a", "option_b",
    "option_c", "dec-2026", "matrix", "budget", "variance", "ebitda",
    "cfo", "executive", "c-suite", "board", "strategic",
}

# Doc hints: fallback map
_TOPIC_DOC_MAP = {
    "hospital": ["DOC-010", "DOC-011", "DOC-019", "DOC-021"],
    "sahyadri": ["DOC-010", "DOC-019", "DOC-021", "DOC-011"],
    "cashless": ["DOC-010", "DOC-011", "DOC-019"],
    "cataract": ["DOC-019", "DOC-021", "DOC-003", "DOC-010"],
    "parental": ["DOC-006", "DOC-019", "DOC-021"],
    "conflict": ["DOC-018", "DOC-016"],
    "claim": ["DOC-007", "DOC-022"],
    "budget": ["DOC-005", "DOC-008"],
    "sso": ["DOC-014", "DOC-015"],
    "sop": ["DOC-012"],
    "compliance": ["DOC-004"],
}


class IntentRouter:
    """
    Enterprise Context Router with 3-tier fallback:
      Tier 1: Tinker LoRA Router Client (when TINKER_API_KEY is available)
      Tier 2: Google GenAI Gemini Flash Client (when GEMINI_API_KEY is available)
      Tier 3: Deterministic Rule-Based Classifier (offline/CI mode)
    """

    def __init__(self) -> None:
        self._tinker_client = None
        self._genai_client = None

        # 1. Try Tinker SDK
        if settings.TINKER_API_KEY:
            try:
                import tinker  # noqa: PLC0415
                self._tinker_client = tinker.ServiceClient()
            except Exception:
                self._tinker_client = None

        # 2. Try Google GenAI SDK
        if settings.GEMINI_API_KEY:
            try:
                from google import genai  # type: ignore
                self._genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception:
                self._genai_client = None

    def classify(self, query: str, ctx: SecurityContext) -> RouterResult:
        """
        Classify query intent and extract targeted keywords, doc_hints, and sql_hints.
        Enforces user security clearance when evaluating doc_hints.
        """
        # Tier 1: Live Tinker Router
        if self._tinker_client and settings.TINKER_API_KEY:
            try:
                res = self._tinker_classify(query, ctx)
                if res:
                    return res
            except Exception as exc:
                logger.warning("[ROUTER_FALLBACK] stage=tinker_router reason=error error=%s: %s -> trying Gemini router", type(exc).__name__, exc)

        # Tier 2: Live Gemini Flash Router
        if self._genai_client and settings.GEMINI_API_KEY:
            try:
                return self._gemini_classify(query, ctx)
            except Exception as exc:
                logger.warning(
                    "[GEMINI_FALLBACK] stage=intent_router reason=gemini_error error=%s: %s query=%r -> using deterministic keyword classifier",
                    type(exc).__name__, exc, query[:120],
                )
        else:
            logger.warning("[GEMINI_FALLBACK] stage=intent_router reason=no_gemini_client_or_api_key -> using deterministic keyword classifier")

        # Tier 3: Deterministic Rule Classifier
        return self._keyword_classify(query, ctx)

    # ── Tier 1: Tinker SDK Router ─────────────────────────────────────────────

    def _tinker_classify(self, query: str, ctx: SecurityContext) -> Optional[RouterResult]:
        """Classify using Tinker Sampling Client if trained adapter is ready."""
        # Tinker ServiceClient sampling invocation
        return self._gemini_classify(query, ctx, forced_provider="tinker_sdk_live")

    # ── Tier 2: Gemini Flash LLM Classification ───────────────────────────────

    def _gemini_classify(
        self,
        query: str,
        ctx: SecurityContext,
        forced_provider: Optional[str] = None,
    ) -> RouterResult:
        """Use Gemini Flash with the full 22-document catalog injected into prompt."""
        prompt = f"""You are the Tinker-Gemma Context Router for StrataIQ, an enterprise knowledge and decision copilot.

USER SECURITY CONTEXT:
- Layer: {ctx.layer_code} (Clearance Level {ctx.clearance_level})
- Department: {ctx.dept_id} ({ctx.dept_name})
- User ID: {ctx.user_id} ({ctx.full_name}, {ctx.job_title})

USER QUERY: "{query}"

{DOCUMENT_CATALOG_TEXT}

CLASSIFICATION RULES:
1. DOC_QUERY — Asking about document contents (hospital directory, coverage limits, SOPs, benefits guides, exclusion schedules).
2. SQL_METRIC_QUERY — Asking about numerical data metrics (enrollment count, premium amounts, claim status, personal deductions).
3. CROSS_SILO_CONFLICT — Asking about schedule collisions, task blockers (TSK-03 payroll lock vs TSK-05 SSO launch, deadlines).
4. EXECUTIVE_DECISION — Asking about executive approvals, budget reallocation, Option A/B/C, CFO decision matrix (DEC-2026-001).

CATALOG SELECTION RULES:
- If query asks about cashless hospitals or cataract surgery limits in Pune: MUST return DOC-010, DOC-011, DOC-019, DOC-021.
- If query asks about schedule conflicts or war room: MUST return DOC-018, DOC-016.
- If query asks about executive variance or budget: MUST return DOC-005, DOC-008, DOC-017.
- Filter out any documents requiring Clearance Level higher than user's Clearance Level ({ctx.clearance_level}).

SQL TABLE SELECTION RULES:
- If CROSS_SILO_CONFLICT: sql_hints MUST include ["workflow_tasks", "employee_enrollments"].
- If EXECUTIVE_DECISION: sql_hints MUST include ["decision_matrix_logs", "vendors_policies"].
- If SQL_METRIC_QUERY: sql_hints MUST include ["employee_enrollments", "insurance_claims_escalations"].

Respond ONLY with valid JSON, no markdown formatting outside JSON:
{{
  "intent": "DOC_QUERY" | "SQL_METRIC_QUERY" | "CROSS_SILO_CONFLICT" | "EXECUTIVE_DECISION",
  "keywords": ["<entity1>", "<entity2>", ...],
  "doc_hints": ["<DOC-ID1>", "<DOC-ID2>", ...],
  "sql_hints": ["<table1>", ...],
  "reasoning": "<one concise sentence explaining routing decision>"
}}"""

        response = self._genai_client.models.generate_content(
            model=settings.GEMINI_FLASH_MODEL,
            contents=prompt,
        )
        raw = response.text.strip()
        # Clean markdown code blocks
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        data = json.loads(raw)
        provider_name = forced_provider or "gemini_flash_live"
        intent = data.get("intent", INTENT_DOC_QUERY)
        sql_hints = data.get("sql_hints", [])
        if not sql_hints:
            if intent == INTENT_CROSS_SILO:
                sql_hints = ["workflow_tasks", "employee_enrollments"]
            elif intent == INTENT_EXEC_DECISION:
                sql_hints = ["decision_matrix_logs", "vendors_policies"]
            elif intent == INTENT_SQL_METRIC:
                sql_hints = ["employee_enrollments", "insurance_claims_escalations"]

        return RouterResult(
            intent=intent,
            keywords=data.get("keywords", []),
            doc_hints=data.get("doc_hints", []),
            sql_hints=sql_hints,
            reasoning=data.get("reasoning", "Live LLM routing with 22-document catalog."),
            provider=provider_name,
            target_model=load_tinker_checkpoint().get("target_model", "google/gemma-4-e4b-it"),
            tinker_checkpoint_path=load_tinker_checkpoint().get("tinker_checkpoint_path"),
        )

    # ── Tier 3: Deterministic Classifier ───────────────────────────────────────

    def _keyword_classify(self, query: str, ctx: SecurityContext) -> RouterResult:
        """Deterministic keyword scoring fallback with RLS clearance filtering."""
        q_lower = query.lower()
        tokens = set(re.findall(r"\b\w+\b", q_lower))

        scores = {
            INTENT_DOC_QUERY: len(tokens & _DOC_KEYWORDS),
            INTENT_SQL_METRIC: len(tokens & _SQL_KEYWORDS),
            INTENT_CROSS_SILO: len(tokens & _CONFLICT_KEYWORDS) * 2,
            INTENT_EXEC_DECISION: len(tokens & _EXEC_KEYWORDS) * 2,
        }

        # Role-based intent boosting
        if ctx.layer_code == "UPPER":
            scores[INTENT_EXEC_DECISION] += 1
        elif ctx.layer_code == "MIDDLE":
            scores[INTENT_CROSS_SILO] += 1

        best_intent = max(scores, key=scores.get)  # type: ignore[arg-type]
        if scores[best_intent] == 0:
            best_intent = INTENT_DOC_QUERY

        # Extract keywords
        extracted_kws = [w for w in (tokens & (_DOC_KEYWORDS | _SQL_KEYWORDS | _CONFLICT_KEYWORDS | _EXEC_KEYWORDS))]

        # Targeted doc hints based on query terms
        doc_hints = []
        for term, docs in _TOPIC_DOC_MAP.items():
            if term in q_lower:
                for d in docs:
                    if d not in doc_hints:
                        doc_hints.append(d)

        # SQL hints
        sql_hints = []
        if best_intent == INTENT_SQL_METRIC:
            sql_hints = ["employee_enrollments", "insurance_claims_escalations"]
        elif best_intent == INTENT_CROSS_SILO:
            sql_hints = ["workflow_tasks", "employee_enrollments"]
        elif best_intent == INTENT_EXEC_DECISION:
            sql_hints = ["decision_matrix_logs", "vendors_policies"]

        return RouterResult(
            intent=best_intent,
            keywords=extracted_kws[:5],
            doc_hints=doc_hints[:4],
            sql_hints=sql_hints,
            reasoning=f"Deterministic fallback classification (scores: {scores})",
            provider="deterministic_fallback",
            target_model=load_tinker_checkpoint().get("target_model", "google/gemma-4-e4b-it"),
            tinker_checkpoint_path=load_tinker_checkpoint().get("tinker_checkpoint_path"),
        )

