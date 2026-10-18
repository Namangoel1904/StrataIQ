"""
StrataIQ — Thesys OpenUI (openui-lang) Formatter & Telemetry Engine (openui_formatter.py)

Generates compact, declarative openui-lang syntax (identifier = Component(...))
with a live ON/OFF toggle (ui_mode="openui" | "legacy") and real-time token/latency telemetry.

Layer-Specific Declarative Templates:
  - UPPER Layer (EXECUTIVE_DECISION):
      root = Stack([callout, chart, table, followups])
      Executive Callout, Department Cost BarChart, 3-Option Decision Matrix Table, Action Pills
  - MIDDLE Layer (CROSS_SILO_CONFLICT / SQL_METRIC_QUERY):
      root = Stack([callout, steps, table, followups])
      Schedule Collision Callout, TSK-03 vs TSK-05 Timeline Steps, Stuck Claims Table
  - LOWER Layer (DOC_QUERY / Voice Studio):
      root = Stack([callout, table, steps, followups])
      Parental Rider Status Callout, Old vs New Comparison Table, Pre-Auth Steps SOP
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from app.database import SecurityContext


@dataclass
class OpenUITelemetry:
    active_ui_mode: str
    openui_lang_code: str
    legacy_verbose_payload: dict[str, Any]
    openui_char_count: int
    openui_token_est: int
    legacy_char_count: int
    legacy_token_est: int
    token_reduction_pct: float
    openui_serialization_ms: float
    legacy_serialization_ms: float
    estimated_llm_decode_saved_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_ui_mode": self.active_ui_mode,
            "openui_lang_code": self.openui_lang_code,
            "legacy_verbose_payload": self.legacy_verbose_payload,
            "openui_char_count": self.openui_char_count,
            "openui_token_est": self.openui_token_est,
            "legacy_char_count": self.legacy_char_count,
            "legacy_token_est": self.legacy_token_est,
            "token_reduction_pct": self.token_reduction_pct,
            "openui_serialization_ms": self.openui_serialization_ms,
            "legacy_serialization_ms": self.legacy_serialization_ms,
            "estimated_llm_decode_saved_ms": self.estimated_llm_decode_saved_ms,
        }


class OpenUILangFormatter:
    """
    Format authoritative enterprise copilot outputs into compact openui-lang
    or verbose legacy JSON UI schemas based on ui_mode.
    """

    def format_ui(
        self,
        intent: str,
        ctx: SecurityContext,
        query: str,
        answer: str,
        sql_metrics: Optional[dict[str, Any]] = None,
        pointed_doc_ids: Optional[list[str]] = None,
        ui_mode: str = "openui",
    ) -> tuple[str, OpenUITelemetry]:
        """
        Generate declarative UI and compute comparative telemetry between openui-lang and legacy JSON.
        """
        sql_metrics = sql_metrics or {}
        mode = "openui" if ui_mode.lower() == "openui" else "legacy"

        # ── 1. Measure OpenUI generation ──────────────────────────────────────
        t0 = time.perf_counter()
        openui_code = self._generate_openui_lang(intent, ctx, query, answer, sql_metrics, pointed_doc_ids)
        openui_time = round((time.perf_counter() - t0) * 1000, 3)

        # ── 2. Measure Legacy JSON generation ─────────────────────────────────
        t1 = time.perf_counter()
        legacy_payload = self._generate_legacy_json(intent, ctx, query, answer, sql_metrics, pointed_doc_ids)
        legacy_time = round((time.perf_counter() - t1) * 1000, 3)

        # ── 3. Token & Character Benchmarking ─────────────────────────────────
        legacy_str = json.dumps(legacy_payload, indent=2)
        openui_chars = len(openui_code)
        legacy_chars = len(legacy_str)

        openui_tokens = max(1, openui_chars // 4)
        legacy_tokens = max(1, legacy_chars // 4)

        reduction_pct = round((1.0 - (openui_tokens / legacy_tokens)) * 100, 1)
        # Approximate decode latency savings (at ~25ms per token on frontier models)
        tokens_saved = max(0, legacy_tokens - openui_tokens)
        saved_ms = round(tokens_saved * 22.5, 1)

        telemetry = OpenUITelemetry(
            active_ui_mode=mode,
            openui_lang_code=openui_code,
            legacy_verbose_payload=legacy_payload,
            openui_char_count=openui_chars,
            openui_token_est=openui_tokens,
            legacy_char_count=legacy_chars,
            legacy_token_est=legacy_tokens,
            token_reduction_pct=reduction_pct,
            openui_serialization_ms=openui_time,
            legacy_serialization_ms=legacy_time,
            estimated_llm_decode_saved_ms=saved_ms,
        )

        effective_code = openui_code if mode == "openui" else json.dumps(legacy_payload, indent=2)
        return effective_code, telemetry

    def _generate_openui_lang(
        self,
        intent: str,
        ctx: SecurityContext,
        query: str,
        answer: str,
        sql_metrics: dict[str, Any],
        pointed_doc_ids: Optional[list[str]],
    ) -> str:
        """Compact declarative openui-lang syntax tailored to layer & intent."""
        # 0. Department EBITDA / cost allocation (full table, or RLS notice below Clearance 3)
        if sql_metrics.get("rls_restricted"):
            notice = str(sql_metrics.get("rls_restriction_notice", "")).replace('"', "'")
            return (
                f'header = Header(title="Department EBITDA & Cost Allocation", badge="Clearance {ctx.clearance_level} ({ctx.layer_code})")\n'
                f'callout = Callout(type="danger", title="Zero-Trust RLS: Clearance Level 3 Required (DOC-005 / DOC-008)", text="{notice}")\n'
                f'root = Stack([header, callout], spacing=4)'
            )
        if sql_metrics.get("department_financials"):
            from app.agents.dept_financials import inr  # noqa: PLC0415
            depts = sql_metrics["department_financials"]
            tot = sql_metrics["company_total"]
            gap = inr(tot["net_budget_gap_inr"])
            rows = ",\n".join(
                f'  ["{r["department_name"]}", "{r["cost_center_code"]}", "{r["headcount"]}", "INR {inr(r["legacy_2025_premium_inr"])}", '
                f'"INR {inr(r["novashield_2026_premium_inr"])}", "INR {inr(r["parental_rider_variance_inr"])}", "INR {inr(r["net_budget_gap_inr"])}"]'
                for r in depts
            )
            return (
                f'header = Header(title="Department Cost Allocation & EBITDA: NovaShield MSA", badge="Clearance 3 (UPPER)")\n'
                f'callout = Callout(type="warning", title="Net Unfunded Gap: INR {gap}", text="Option A hits Q4 EBITDA by -INR {gap}; Option B (Recommended) nets INR 0 using the LegacyCare refund plus Q4 Staff Welfare Reserve (CC-102).")\n'
                f'dept_table = Table(headers=["Department", "Cost Center", "Employees", "2025 LegacyCare", "2026 NovaShield", "Parental Variance", "Net Budget Gap"], rows=[\n'
                f'{rows},\n'
                f'  ["Company Total", "-", "{tot["headcount"]}", "INR {inr(tot["legacy_2025_premium_inr"])}", "INR {inr(tot["novashield_2026_premium_inr"])}", "INR {inr(tot["parental_rider_variance_inr"])}", "INR {gap}"]\n'
                f'])\n'
                f'ebitda_table = Table(headers=["Option", "Q4 EBITDA Impact", "Funding"], rows=[\n'
                f'  ["Option A", "-INR {gap}", "100% margin absorption"],\n'
                f'  ["Option B (Recommended)", "INR 0", "INR {inr(tot["legacy_pro_rata_refund_inr"])} refund + INR {gap} welfare reserve (CC-102)"]\n'
                f'])\n'
                f'followups = FollowUpBlock(actions=[\n'
                f'  ActionPill(label="Inspect Cost Ledger DOC-005", doc_id="DOC-005", variant="outline"),\n'
                f'  ActionPill(label="Review CFO Proposal DOC-008", doc_id="DOC-008", variant="outline")\n'
                f'])\n'
                f'root = Stack([header, callout, dept_table, ebitda_table, followups], spacing=4)'
            )

        # A. UPPER LAYER (Executive Decision / CFO Variance)
        if ctx.layer_code == "UPPER" or intent == "EXECUTIVE_DECISION":
            variance_l = round(sql_metrics.get("parental_premium_variance_inr", 3840000.0) / 100000, 1)
            refund_l = round(sql_metrics.get("legacycare_refund_inr", 1920000.0) / 100000, 1)
            return (
                f'header = Header(title="Executive Decision Matrix: DEC-2026-001", badge="Clearance 3 (UPPER)")\n'
                f'callout = Callout(type="warning", title="Unbudgeted Variance: INR {variance_l}L", text="Vendor transition to NovaShield requires parental buffer reallocation before Oct 25 payroll cutoff.")\n'
                f'chart = BarChart(title="Department Parental Cost Variance (Lakhs INR)", data=[["Engineering", 14.8], ["Operations", 9.6], ["Finance", 4.8], ["HR", 3.6], ["IT", 3.2], ["Legal", 2.4]])\n'
                f'decision_table = Table(headers=["Option", "Financial Impact", "Operational Risk", "Action"], rows=[\n'
                f'  ["Option A", "INR 38.4L Unbudgeted", "High: EBITDA deduction hit", "Reject"],\n'
                f'  ["Option B (Recommended)", "INR 0 Net (INR {refund_l}L Refund + Welfare Reserve)", "Zero: Extends cutoff to Oct 25", "Approve"],\n'
                f'  ["Option C", "INR 38.4L Direct Co-Pay", "Severe: 142 employee escalations", "Reject"]\n'
                f'])\n'
                f'followups = FollowUpBlock(actions=[\n'
                f'  ActionPill(label="Approve Option B Recommended", endpoint="/api/v1/decisions/DEC-2026-001/approve?option=OPTION_B_RECOMMENDED", variant="primary"),\n'
                f'  ActionPill(label="Inspect Actuarial Ledger DOC-005", doc_id="DOC-005", variant="outline"),\n'
                f'  ActionPill(label="Review War-Room Transcript DOC-018", doc_id="DOC-018", variant="outline")\n'
                f'])\n'
                f'root = Stack([header, callout, chart, decision_table, followups], spacing=4)'
            )

        # B. MIDDLE LAYER (Cross-Silo Conflict / Claims War-Room)
        if ctx.layer_code == "MIDDLE" or intent == "CROSS_SILO_CONFLICT":
            task_a = sql_metrics.get("task_a_due", "2026-10-20")
            task_b = sql_metrics.get("task_b_due", "2026-10-23")
            blocked = sql_metrics.get("blocked_employees", 142)
            claims_l = round(sql_metrics.get("stuck_claims_amount_inr", 1420000.0) / 100000, 1)
            return (
                f'header = Header(title="Cross-Silo Schedule Collision Alert", badge="Clearance 2 (MIDDLE)")\n'
                f'callout = Callout(type="danger", title="Collision: TSK-03 (Finance) vs TSK-05 (IT)", text="Payroll Lock ({task_a}) precedes IT SSO Portal Launch ({task_b}), blocking {blocked} employees and risking INR {claims_l}L transition claims.")\n'
                f'steps = Steps(current=2, items=[\n'
                f'  StepItem(title="TSK-01 Vendor Selection", status="completed", date="2026-09-15"),\n'
                f'  StepItem(title="TSK-03 Finance Payroll Cutoff", status="blocked", date="{task_a}", alert="Needs Oct 25 extension"),\n'
                f'  StepItem(title="TSK-05 IT SSO Portal Launch", status="in_progress", date="{task_b}"),\n'
                f'  StepItem(title="Option B Cutoff Harmonization", status="pending", date="2026-10-25")\n'
                f'])\n'
                f'claims_table = Table(headers=["Claim ID", "Hospital", "Employee", "Amount (INR)", "Stage", "Blocker"], rows=[\n'
                f'  ["CLM-2026-001", "Sahyadri Hospital (Pune)", "EMP-104", "INR 1,45,000", "Under Audit", "TPA Portal Credential Delay"],\n'
                f'  ["CLM-2026-004", "Ruby Hall Clinic (Pune)", "EMP-218", "INR 2,10,000", "Pre-Auth Pending", "Missing Discharge Summary"],\n'
                f'  ["CLM-2026-007", "Apollo Hospital (Navi Mumbai)", "EMP-342", "INR 95,000", "Awaiting Review", "SSO Access Sync"]\n'
                f'])\n'
                f'followups = FollowUpBlock(actions=[\n'
                f'  ActionPill(label="Inspect War-Room Transcript DOC-018", doc_id="DOC-018", variant="primary"),\n'
                f'  ActionPill(label="View Migration Rollout Tracker DOC-016", doc_id="DOC-016", variant="outline"),\n'
                f'  ActionPill(label="Send SSO Emergency Notice to IT", action="escalate_it", variant="outline")\n'
                f'])\n'
                f'root = Stack([header, callout, steps, claims_table, followups], spacing=4)'
            )

        # C. LOWER LAYER (Document Voice Q&A / Personal Benefits & Sahyadri Cataract)
        status = sql_metrics.get("parental_opt_in", "PENDING_CONFIRMATION")
        alert_type = "warning" if status == "PENDING_CONFIRMATION" else "success"
        return (
            f'header = Header(title="Healthcare Benefits & Network Copilot", badge="Clearance 1 (LOWER)")\n'
            f'callout = Callout(type="{alert_type}", title="Personal Status: Parental Rider {status}", text="Action required before October 22, 2026 to ensure parental hospitalization is covered under cashless.")\n'
            f'benefit_table = Table(headers=["Benefit Item", "LegacyCare (Old 2025)", "NovaShield (New 2026)", "Status"], rows=[\n'
            f'  ["Sahyadri Hospital (Pune)", "Network Hospital", "Tier-1 Preferred Cashless Partner", "Cashless Active"],\n'
            f'  ["Cataract Surgery Limit", "INR 35,000 / eye", "INR 45,000 / eye (Upgraded)", "Upgraded +INR 10k"],\n'
            f'  ["Co-Pay Percentage", "20% Mandatory", "10% Copay (Preferred Hospitals)", "50% Savings"],\n'
            f'  ["Pre-Auth Approval SLA", "4-6 Hours", "90 Minutes Express Guarantee", "Express Active"]\n'
            f'])\n'
            f'sop_steps = Steps(current=1, items=[\n'
            f'  StepItem(title="Obtain Cataract Surgical Estimate", status="ready", detail="Ask Sahyadri TPA desk for ophthalmology pre-auth sheet"),\n'
            f'  StepItem(title="Submit NovaShield Pre-Auth", status="pending", detail="Submit online or via hospital desk at least 48 hours prior (DOC-011)"),\n'
            f'  StepItem(title="Confirm Parental Rider Opt-In", status="action_required", detail="Complete HRMS opt-in before Oct 22, 2026 deadline")\n'
            f'])\n'
            f'followups = FollowUpBlock(actions=[\n'
            f'  ActionPill(label="Confirm Parental Rider Opt-In", endpoint="/api/v1/workspace/confirm-parental-rider", variant="primary"),\n'
            f'  ActionPill(label="View Sahyadri Directory DOC-010", doc_id="DOC-010", variant="outline"),\n'
            f'  ActionPill(label="Open Pre-Auth Guide DOC-011", doc_id="DOC-011", variant="outline")\n'
            f'])\n'
            f'root = Stack([header, callout, benefit_table, sop_steps, followups], spacing=4)'
        )

    def _generate_legacy_json(
        self,
        intent: str,
        ctx: SecurityContext,
        query: str,
        answer: str,
        sql_metrics: dict[str, Any],
        pointed_doc_ids: Optional[list[str]],
    ) -> dict[str, Any]:
        """Verbose legacy JSON UI schema with deep nesting, explicit CSS, and schema noise."""
        return {
            "schema_version": "2.4.0-legacy-verbose",
            "ui_layout_type": "standard_vertical_grid_container",
            "metadata": {
                "user_id": ctx.user_id,
                "layer_code": ctx.layer_code,
                "clearance_level": ctx.clearance_level,
                "department": ctx.dept_id,
                "timestamp_epoch_ms": int(time.time() * 1000),
                "generated_by": "legacy_json_schema_generator_v2",
            },
            "container": {
                "type": "layout_root_view_group",
                "properties": {
                    "spacing": "16px",
                    "padding": "24px",
                    "background_color": "#0f172a",
                    "border_radius": "8px",
                    "elevation": 2,
                    "responsive_breakpoints": {
                        "mobile_max_px": 640,
                        "tablet_max_px": 1024,
                        "desktop_min_px": 1025,
                    },
                },
                "components": [
                    {
                        "component_id": "comp_header_001",
                        "component_type": "typography_header_view",
                        "attributes": {
                            "text_content": f"StrataIQ Enterprise Portal — {ctx.layer_code} Layer",
                            "font_family": "Inter, Roboto, sans-serif",
                            "font_size_px": 22,
                            "font_weight": 700,
                            "color_hex": "#f8fafc",
                            "margin_bottom_px": 12,
                        },
                    },
                    {
                        "component_id": "comp_callout_002",
                        "component_type": "status_banner_callout_view",
                        "attributes": {
                            "banner_level": "critical_warning",
                            "title_text": "System Alert & State Overview",
                            "body_description": answer[:300],
                            "border_left_width_px": 4,
                            "border_left_color_hex": "#f59e0b",
                            "background_color_hex": "rgba(245, 158, 11, 0.1)",
                            "icon_descriptor": {
                                "icon_family": "lucide_react",
                                "icon_name": "alert-triangle",
                                "icon_color_hex": "#f59e0b",
                            },
                        },
                    },
                    {
                        "component_id": "comp_data_table_003",
                        "component_type": "enterprise_data_grid_view",
                        "attributes": {
                            "table_caption": "Factual Transition Records & Audit Metrics",
                            "show_pagination_controls": True,
                            "rows_per_page_default": 10,
                            "allow_column_sorting": True,
                            "columns": [
                                {"field_key": "attribute", "display_name": "Transition Attribute", "width_pct": 35},
                                {"field_key": "previous_val", "display_name": "LegacyCare 2025 Value", "width_pct": 30},
                                {"field_key": "updated_val", "display_name": "NovaShield 2026 Value", "width_pct": 35},
                            ],
                            "row_data": [
                                {"attribute": "Sahyadri Hospital (Pune)", "previous_val": "Standard Network", "updated_val": "Tier-1 Preferred Cashless"},
                                {"attribute": "Cataract Surgery Limit", "previous_val": "INR 35,000 / eye", "updated_val": "INR 45,000 / eye"},
                                {"attribute": "Parental Deductions", "previous_val": "INR 2,200 / month", "updated_val": "INR 2,450 / month"},
                            ],
                        },
                    },
                    {
                        "component_id": "comp_actions_004",
                        "component_type": "horizontal_action_pill_container",
                        "attributes": {
                            "alignment": "flex-start",
                            "button_group": [
                                {
                                    "action_id": "act_01",
                                    "button_label": "Verify Coverage Details",
                                    "http_method": "POST",
                                    "api_target": "/api/v1/workspace/confirm-parental-rider",
                                    "style_variant": "filled_primary",
                                },
                                {
                                    "action_id": "act_02",
                                    "button_label": "Download Document 11 PDF",
                                    "http_method": "GET",
                                    "api_target": "/api/v1/documents/DOC-011/content",
                                    "style_variant": "outline_secondary",
                                },
                            ],
                        },
                    },
                ],
            },
        }
