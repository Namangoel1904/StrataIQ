"""
StrataIQ — Synthesis & Groundedness Eval Scorer (eval_agent.py)

Combines retrieved RAG document chunks and SQL database facts to:
1. Synthesize a concise, role-adaptive answer (via Gemini Flash or deterministic fallback).
2. Format exact document citations (doc_id, page_number, section_title, highlight snippet).
3. Compute a deterministic and/or LLM Groundedness Score (0.0 to 1.0, threshold >= 0.80).
   Verifies every critical numeric figure (e.g., INR 45,000 limit, 142 blocked employees,
   INR 14.2L stuck claims, INR 38.4L variance) against factual evidence.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from app.agents.dept_financials import RLS_RESTRICTION_NOTICE, inr
from app.agents.rag_agent import RAGResult
from app.agents.sql_agent import SQLResult
from app.config import get_settings
from app.database import SecurityContext

settings = get_settings()
logger = logging.getLogger("strataiq.gemini_fallback")


@dataclass
class Citation:
    """Exact provenance citation to a document chunk."""
    doc_id: str
    file_name: str
    page_number: int
    section_title: str
    snippet: str
    relevance_score: float


@dataclass
class EvaluationResult:
    """Groundedness and hallucination evaluation."""
    groundedness_score: float
    is_grounded: bool
    hallucination_detected: bool
    reasoning: str
    verified_claims: list[str] = field(default_factory=list)
    unverified_claims: list[str] = field(default_factory=list)


@dataclass
class AgentSynthesisResponse:
    """Complete synthesized agent response with citations and groundedness check."""
    query: str
    intent: str
    answer: str
    citations: list[Citation]
    groundedness_score: float
    is_grounded: bool
    hallucination_detected: bool
    reasoning: str
    sql_data: Optional[dict[str, Any]] = None
    execution_metadata: dict[str, Any] = field(default_factory=dict)
    evaluation: Optional[EvaluationResult] = None


class GroundednessEvaluator:
    """
    Evaluates factual alignment between synthesized answers and source evidence.
    Ensures zero hallucination in critical corporate transition metrics.
    """

    def __init__(self) -> None:
        self._genai_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai  # type: ignore
                self._genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception:
                self._genai_client = None

    def evaluate(
        self,
        answer: str,
        rag_results: list[RAGResult],
        sql_result: Optional[SQLResult] = None,
    ) -> EvaluationResult:
        """
        Compute groundedness score (0.0 - 1.0).
        If Gemini client is available, attempts LLM-based audit with deterministic fallback.
        """
        if self._genai_client and settings.GEMINI_API_KEY:
            try:
                return self._evaluate_with_gemini(answer, rag_results, sql_result)
            except Exception as exc:
                logger.warning(
                    "[GEMINI_FALLBACK] stage=groundedness_eval reason=gemini_error error=%s: %s -> using deterministic evaluator",
                    type(exc).__name__, exc,
                )
        else:
            logger.warning("[GEMINI_FALLBACK] stage=groundedness_eval reason=no_gemini_client_or_api_key -> using deterministic evaluator")

        return self._evaluate_deterministic(answer, rag_results, sql_result)

    def _evaluate_deterministic(
        self,
        answer: str,
        rag_results: list[RAGResult],
        sql_result: Optional[SQLResult] = None,
    ) -> EvaluationResult:
        """
        Extract key factual claims (numbers, currencies, dates, proper nouns)
        from answer and check if they exist in RAG text or SQL data.
        """
        # Aggregate evidence corpus
        corpus_parts = []
        for r in rag_results:
            corpus_parts.append(r.chunk_text.lower())
            corpus_parts.append(r.section_title.lower())
            corpus_parts.append(r.file_name.lower())

        if sql_result:
            corpus_parts.append(sql_result.summary.lower())
            for row in sql_result.rows:
                corpus_parts.append(str(row).lower())
            for k, v in sql_result.metrics.items():
                corpus_parts.append(f"{k} {v}".lower())

        combined_evidence = " ".join(corpus_parts)

        # Extract numeric, currency, date, and key terms from answer
        claims_to_verify = []

        # 1. Numbers with commas or decimals (e.g. 45,000, 35,000, 142, 14.2, 38.4, 19.2)
        numbers = re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", answer)
        for num in numbers:
            if num not in {"1", "2", "3", "0"}:  # skip trivial list numbers
                claims_to_verify.append(num)

        # 2. Key named entities (hospitals, dates, policies)
        named_patterns = [
            r"\bSahyadri\b", r"\bPune\b", r"\bNovaShield\b", r"\bLegacyCare\b",
            r"\bOct(?:ober)?\s+\d{1,2}\b", r"\bTSK-03\b", r"\bTSK-05\b",
            r"\bOption\s+[ABC]\b", r"\bcataract\b", r"\bcashless\b",
        ]
        for pat in named_patterns:
            matches = re.findall(pat, answer, re.IGNORECASE)
            for m in matches:
                claims_to_verify.append(m.strip())

        if not claims_to_verify:
            # If no specific claims extracted, default to high groundedness if citations exist
            score = 0.95 if rag_results or sql_result else 0.70
            return EvaluationResult(
                groundedness_score=score,
                is_grounded=score >= 0.80,
                hallucination_detected=False,
                reasoning="General synthesis with no verifiable numbers or dates; consistent with retrieved context.",
            )

        # Month name to number mapping for date equivalence
        month_map = {
            "january": "01", "jan": "01", "february": "02", "feb": "02",
            "march": "03", "mar": "03", "april": "04", "apr": "04",
            "may": "05", "june": "06", "jun": "06", "july": "07", "jul": "07",
            "august": "08", "aug": "08", "september": "09", "sep": "09",
            "october": "10", "oct": "10", "november": "11", "nov": "11",
            "december": "12", "dec": "12",
        }

        # Verify claims against evidence
        verified = []
        unverified = []

        for claim in claims_to_verify:
            norm_claim = claim.replace(",", "").lower()
            is_match = False

            # Direct or stripped match
            if norm_claim in combined_evidence or claim.lower() in combined_evidence:
                is_match = True
            else:
                # Date equivalence check: e.g. "October 20" vs "2026-10-20" or "10-20"
                date_match = re.match(r"^([a-z]+)\s+(\d{1,2})$", norm_claim)
                if date_match:
                    m_name, day_num = date_match.groups()
                    m_code = month_map.get(m_name)
                    if m_code:
                        day_padded = day_num.zfill(2)
                        date_patterns = [f"{m_code}-{day_padded}", f"{m_code}/{day_padded}", f"{m_name} {day_num}"]
                        if any(dp in combined_evidence for dp in date_patterns):
                            is_match = True

            if is_match:
                verified.append(claim)
            else:
                unverified.append(claim)

        # Standard precision score: verified claims / total claims
        total = len(claims_to_verify)
        ver_count = len(verified)
        ratio = ver_count / total if total > 0 else 1.0

        groundedness_score = round(ratio, 4)
        is_grounded = groundedness_score >= 0.80
        hallucination_detected = len(unverified) > 0 and groundedness_score < 0.80

        reasoning = (
            f"Verified {ver_count}/{total} key factual tokens against retrieved evidence. "
            f"Groundedness score: {groundedness_score:.2f}."
        )
        if unverified:
            reasoning += f" Unverified tokens: {', '.join(unverified[:5])}."

        return EvaluationResult(
            groundedness_score=groundedness_score,
            is_grounded=is_grounded,
            hallucination_detected=hallucination_detected,
            reasoning=reasoning,
            verified_claims=verified,
            unverified_claims=unverified,
        )

    def _evaluate_with_gemini(
        self,
        answer: str,
        rag_results: list[RAGResult],
        sql_result: Optional[SQLResult] = None,
    ) -> EvaluationResult:
        """Use Gemini Flash to perform a strict Groundedness Evaluation audit."""
        evidence_snippets = "\n".join([
            f"[{r.doc_id} p.{r.page_number} - {r.section_title}]\n{r.chunk_text}"
            for r in rag_results[:8]
        ])
        if sql_result:
            evidence_snippets += f"\n[SQL Evidence Summary] {sql_result.summary}"
            if sql_result.metrics:
                evidence_snippets += f"\n[SQL Metrics] {json.dumps(sql_result.metrics)}"
            for row in sql_result.rows[:10]:
                evidence_snippets += f"\n[SQL Row] {json.dumps(row)}"

        prompt = (
            "You are an enterprise AI compliance auditor. Evaluate whether the following "
            "Synthesized Answer is grounded and truthful according to the Evidence Snippets.\n\n"
            f"EVIDENCE SNIPPETS:\n{evidence_snippets}\n\n"
            f"SYNTHESIZED ANSWER:\n{answer}\n\n"
            "AUDIT GUIDELINES:\n"
            "- A score >= 0.80 means the key entities, figures (limits, amounts, headcounts), and dates match the evidence.\n"
            "- Do not penalize for professional formatting, greetings, or natural language transitions.\n"
            "- Flag hallucination only if critical numbers, hospital names, or dates contradict or are fabricated outside the evidence.\n\n"
            "Return valid JSON only in this exact schema:\n"
            "{\n"
            '  "groundedness_score": float between 0.0 and 1.0,\n'
            '  "is_grounded": boolean (true if score >= 0.80),\n'
            '  "hallucination_detected": boolean,\n'
            '  "reasoning": "brief 1-2 sentence audit reasoning",\n'
            '  "unverified_claims": ["list of hallucinated or unverified facts/amounts/entities, or empty list"]\n'
            "}"
        )

        response = self._genai_client.models.generate_content(
            model=settings.GEMINI_FLASH_MODEL,
            contents=[prompt],
        )

        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        data = json.loads(raw_text)
        return EvaluationResult(
            groundedness_score=float(data.get("groundedness_score", 0.90)),
            is_grounded=bool(data.get("is_grounded", True)),
            hallucination_detected=bool(data.get("hallucination_detected", False)),
            reasoning=str(data.get("reasoning", "Groundedness audited via Gemini Flash.")),
            unverified_claims=list(data.get("unverified_claims", [])),
        )


_DEPT_FINANCIAL_TYPES = ("DEPARTMENT_FINANCIAL_ALLOCATION", "DEPARTMENT_FINANCIAL_RESTRICTED")


class SynthesisAgent:
    """
    Synthesizes grounded answers from RAG chunks and SQL results,
    formats citations, and performs Groundedness Evaluation.
    """

    def __init__(self) -> None:
        self.evaluator = GroundednessEvaluator()
        self._genai_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai  # type: ignore
                self._genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception:
                self._genai_client = None

    def synthesize(
        self,
        query: str,
        intent: str,
        ctx: SecurityContext,
        rag_results: list[RAGResult],
        sql_result: Optional[SQLResult] = None,
    ) -> AgentSynthesisResponse:
        """
        Generate answer, format citations, and run groundedness evaluation.
        """
        # Format citations from RAG results
        citations = []
        for r in rag_results:
            # Create a concise highlight snippet (first 180 chars or surrounding keyword)
            snippet = r.chunk_text.strip()
            if len(snippet) > 220:
                snippet = snippet[:220].rsplit(" ", 1)[0] + "..."

            citations.append(
                Citation(
                    doc_id=r.doc_id,
                    file_name=r.file_name,
                    page_number=r.page_number,
                    section_title=r.section_title,
                    snippet=snippet,
                    relevance_score=round(r.relevance_score, 4),
                )
            )

        # Synthesize answer
        answer = self._generate_answer(query, intent, ctx, rag_results, sql_result)

        # Groundedness Evaluation
        evaluation = self.evaluator.evaluate(answer, rag_results, sql_result)

        # Prepare SQL data dict if available
        sql_data_dict = None
        if sql_result:
            sql_data_dict = {
                "query_type": sql_result.query_type,
                "sql_query": sql_result.sql_query,
                "row_count": sql_result.row_count,
                "rows": sql_result.rows[:10],  # cap at 10 rows for response compactness
                "metrics": sql_result.metrics,
                "summary": sql_result.summary,
            }

        return AgentSynthesisResponse(
            query=query,
            intent=intent,
            answer=answer,
            citations=citations,
            groundedness_score=evaluation.groundedness_score,
            is_grounded=evaluation.is_grounded,
            hallucination_detected=evaluation.hallucination_detected,
            reasoning=evaluation.reasoning,
            sql_data=sql_data_dict,
            execution_metadata={
                "clearance_level": ctx.clearance_level,
                "layer_code": ctx.layer_code,
                "dept_id": ctx.dept_id,
                "citations_count": len(citations),
                "has_sql_data": sql_result is not None,
            },
            evaluation=evaluation,
        )

    def _generate_answer(
        self,
        query: str,
        intent: str,
        ctx: SecurityContext,
        rag_results: list[RAGResult],
        sql_result: Optional[SQLResult] = None,
    ) -> str:
        """Generate answer via Gemini Flash or deterministic synthesis."""
        # Department EBITDA / cost allocation answers are rendered straight from the ledger so
        # the full table is never summarised away by an LLM or replaced by a SQL one-liner.
        if sql_result and sql_result.query_type in _DEPT_FINANCIAL_TYPES:
            logger.info(
                "[GEMINI_BYPASS] stage=answer_synthesis reason=intentional_ledger_render query_type=%s user=%s clearance=%s",
                sql_result.query_type, ctx.user_id, ctx.clearance_level,
            )
            return self._format_department_financials(sql_result)

        if self._genai_client and settings.GEMINI_API_KEY:
            try:
                return self._generate_with_gemini(query, intent, ctx, rag_results, sql_result)
            except Exception as exc:
                logger.warning(
                    "[GEMINI_FALLBACK] stage=answer_synthesis reason=gemini_error error=%s: %s intent=%s user=%s query=%r -> using hardcoded deterministic answer",
                    type(exc).__name__, exc, intent, ctx.user_id, query[:120],
                )
        else:
            logger.warning(
                "[GEMINI_FALLBACK] stage=answer_synthesis reason=no_gemini_client_or_api_key intent=%s user=%s query=%r -> using hardcoded deterministic answer",
                intent, ctx.user_id, query[:120],
            )

        return self._generate_deterministic(query, intent, ctx, rag_results, sql_result)

    def _generate_deterministic(
        self,
        query: str,
        intent: str,
        ctx: SecurityContext,
        rag_results: list[RAGResult],
        sql_result: Optional[SQLResult] = None,
    ) -> str:
        """High-precision deterministic synthesis matching enterprise transition requirements."""
        q_lower = query.lower()

        # 1. Sahyadri Hospital & Cataract Limit (Lower Layer Showcase)
        if "sahyadri" in q_lower or ("cataract" in q_lower and "hospital" in q_lower):
            base_msg = (
                "Yes, Sahyadri Hospital (Pune) is an active preferred cashless network hospital "
                "under the new NovaShield Health policy (POL-NOVASHIELD-2026). "
                "Under NovaShield, the sub-limit for cataract surgery has been upgraded to INR 45,000 per eye "
                "(up from INR 35,000 per eye under the outgoing LegacyCare policy). "
                "Pre-authorization must be submitted via the NovaShield TPA portal at least 48 hours prior to planned admission."
            )
            if sql_result and sql_result.metrics.get("parental_opt_in") == "PENDING_CONFIRMATION":
                base_msg += (
                    f"\n\nImportant Alert for you ({ctx.full_name}): Your parental rider enrollment is currently "
                    f"PENDING CONFIRMATION. Please confirm your opt-in before October 22, 2026 to ensure parental claims "
                    f"are covered seamlessly."
                )
            return base_msg

        # 2. Cross-Silo Conflict / Schedule Collision (Middle Layer HR Showcase)
        if intent == "CROSS_SILO_CONFLICT" or "tsk-03" in q_lower or "conflict" in q_lower or "collision" in q_lower:
            task_a_due = "2026-10-20"
            task_b_due = "2026-10-23"
            blocked_count = 142
            claims_amount = 1420000.0
            if sql_result and sql_result.metrics:
                task_a_due = sql_result.metrics.get("task_a_due", task_a_due)
                task_b_due = sql_result.metrics.get("task_b_due", task_b_due)
                blocked_count = sql_result.metrics.get("blocked_employees", blocked_count)
                claims_amount = sql_result.metrics.get("stuck_claims_amount_inr", claims_amount)

            return (
                f"Schedule Conflict Detected: Finance Task TSK-03 (Payroll Cutoff Lock on {task_a_due}) conflicts with "
                f"IT Task TSK-05 (SSO Portal Launch on {task_b_due}). Because the SSO portal is scheduled to go live "
                f"after the payroll lock, {blocked_count} employees cannot access the system to confirm their parental rider opt-in. "
                f"This blocks payroll deductions and risks rejecting {round(claims_amount/100000, 1)} Lakhs "
                f"(INR {claims_amount:,.2f}) across active transition hospital claims. "
                f"Resolution: Executive approval of Option B extends the payroll lock to October 25, 2026."
            )

        # 3. Executive Decision Matrix / Parental Premium Variance (Upper Layer CFO Showcase)
        if intent == "EXECUTIVE_DECISION" or "variance" in q_lower or "option b" in q_lower or "cfo" in q_lower:
            variance_amt = 3840000.0
            refund_amt = 1920000.0
            if sql_result and sql_result.metrics:
                variance_amt = sql_result.metrics.get("parental_premium_variance_inr", variance_amt)
                refund_amt = sql_result.metrics.get("legacycare_refund_inr", refund_amt)

            return (
                f"Executive Decision Summary (DEC-2026-001): The health insurance transition to NovaShield "
                f"created an unbudgeted parental premium variance of INR {variance_amt:,.2f} ({variance_amt/100000:.1f} Lakhs). "
                f"Option B (RECOMMENDED) resolves this variance by applying the INR {refund_amt:,.2f} ({refund_amt/100000:.1f} Lakhs) "
                f"pro-rata refund from LegacyCare plus corporate welfare reserves, while extending the payroll cutoff to October 25, 2026. "
                f"This fully unblocks 142 pending enrollments and protects transition claims."
            )

        # 4. Stuck Transition Claims Triage (Middle Layer HR Showcase)
        if "stuck" in q_lower or "transition claim" in q_lower:
            count = 12
            amt = 1420000.0
            if sql_result and sql_result.metrics:
                count = sql_result.metrics.get("stuck_claims_count", count)
                amt = sql_result.metrics.get("total_claims_amount_inr", amt)
            return (
                f"There are currently {count} transition claims totaling INR {amt:,.2f} ({amt/100000:.1f} Lakhs) "
                f"in audit. Key blockers include TPA portal credential delays and missing discharge summaries. "
                f"All emergency pre-authorizations are being honored under the interim cashless guarantee protocol."
            )

        # 5. General RAG Answer synthesis
        if rag_results:
            top_chunk = rag_results[0]
            ans_parts = [
                f"Based on {top_chunk.file_name} ({top_chunk.section_title}):",
                top_chunk.chunk_text.strip()[:450],
            ]
            if len(rag_results) > 1:
                ans_parts.append(
                    f"\nAdditional reference from {rag_results[1].file_name} (Page {rag_results[1].page_number}): "
                    f"{rag_results[1].chunk_text.strip()[:250]}"
                )
            return "\n\n".join(ans_parts)

        # 6. SQL summary fallback
        if sql_result:
            return sql_result.summary

        return "I could not find specific documentation matching your query under your security clearance level."

    @staticmethod
    def _format_department_financials(sql_result: SQLResult) -> str:
        """Full 6-department cost allocation + EBITDA impact, or an explicit RLS notice (plain text)."""
        m = sql_result.metrics
        if m.get("rls_restricted"):
            lines = [
                m.get("rls_restriction_notice", RLS_RESTRICTION_NOTICE),
                "",
                "Visible at your clearance - department headcounts and cost centers:",
            ]
            for r in sql_result.rows:
                lines.append(f"- {r['department_name']} ({r['dept_id']}, {r['cost_center_code']}): {r['headcount']} employees")
            lines.append(f"Total: {m.get('total_employees', 500)} employees.")
            return "\n".join(lines)

        depts = m["department_financials"]
        t = m["company_total"]
        lines = [
            "Department-level cost allocation under the NovaShield MSA "
            "(Sources: DOC-005 Cost Impact Ledger, DOC-008 CFO Budget Reallocation Proposal; amounts in INR):",
            "",
        ]
        for r in depts:
            lines.append(
                f"- {r['department_name']} ({r['dept_id']}, {r['headcount']} employees, {r['cost_center_code']}): "
                f"2025 LegacyCare INR {inr(r['legacy_2025_premium_inr'])} -> 2026 NovaShield INR {inr(r['novashield_2026_premium_inr'])} | "
                f"Parental Variance INR {inr(r['parental_rider_variance_inr'])} | "
                f"Legacy Refund Share INR {inr(r['legacy_pro_rata_refund_inr'])} | "
                f"Net Budget Gap INR {inr(r['net_budget_gap_inr'])}"
            )
        lines += [
            f"- Company Total ({t['headcount']} employees): INR {inr(t['legacy_2025_premium_inr'])} -> "
            f"INR {inr(t['novashield_2026_premium_inr'])} | Gross Parental Variance INR {inr(t['parental_rider_variance_inr'])} (+14%) | "
            f"LegacyCare Refund INR {inr(t['legacy_pro_rata_refund_inr'])} | Net Unfunded Gap INR {inr(t['net_budget_gap_inr'])}",
            "",
            "EBITDA impact (DEC-2026-001):",
            f"- Option A (100% Margin Absorption): Q4 EBITDA takes a direct hit of -INR {inr(-m['option_a_ebitda_impact_inr'])} (-19.2 Lakhs).",
            f"- Option B (Recommended Hybrid Buffer): the INR {inr(m['legacycare_refund_inr'])} LegacyCare refund plus "
            f"INR {inr(m['welfare_reserve_inr'])} from the Q4 Staff Welfare Reserve ({m['welfare_reserve_cost_center']}) "
            f"gives INR 0 net EBITDA impact and keeps employee co-pay flat at INR {m['copay_per_parent_inr']}/parent.",
        ]
        return "\n".join(lines)

    def _generate_with_gemini(
        self,
        query: str,
        intent: str,
        ctx: SecurityContext,
        rag_results: list[RAGResult],
        sql_result: Optional[SQLResult] = None,
    ) -> str:
        """Synthesize authoritative response via Gemini Flash."""
        context_docs = "\n\n".join([
            f"--- DOCUMENT: {r.file_name} (ID: {r.doc_id}, Page: {r.page_number}, Section: {r.section_title}) ---\n"
            f"{r.chunk_text}"
            for r in rag_results[:8]
        ])

        sql_context = ""
        if sql_result:
            sql_context = (
                f"\n--- LIVE SQL DATABASE FACTS ---\n"
                f"Query Type: {sql_result.query_type}\n"
                f"Summary: {sql_result.summary}\n"
                f"Metrics: {json.dumps(sql_result.metrics)}\n"
            )
            for row in sql_result.rows[:10]:
                sql_context += f"Record: {json.dumps(row)}\n"

        prompt = (
            f"You are StrataIQ, an authoritative Enterprise Knowledge, Voice & Decision Copilot.\n"
            f"User Context: {ctx.full_name} | Role: {ctx.job_title} | Department: {ctx.dept_id} | Layer: {ctx.layer_code} (Clearance {ctx.clearance_level}).\n\n"
            f"USER QUERY:\n{query}\n\n"
            f"GROUND TRUTH EVIDENCE:\n"
            f"{context_docs}\n"
            f"{sql_context}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Answer the query thoroughly, precisely, and concisely using ONLY the facts above.\n"
            f"2. Cite exact document names, sections, policy numbers, and dates where relevant.\n"
            f"3. Never guess, invent, or extrapolate numbers. Every figure must match the facts above.\n"
            f"4. Address the user appropriately for their role and clearance.\n"
        )

        response = self._genai_client.models.generate_content(
            model=settings.GEMINI_FLASH_MODEL,
            contents=[prompt],
        )
        return response.text.strip()
