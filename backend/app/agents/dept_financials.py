"""
StrataIQ — Department Cost Allocation & EBITDA ledger (dept_financials.py)

Single source of truth for the department-level premium ledger
(05_Q3_Q4_Insurance_Premium_Cost_Impact_Ledger.csv, DOC-005) joined with
departments.cost_center_code and the EBITDA options of DEC-2026-001 (DOC-008).
"""
from __future__ import annotations

import csv
import re
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Department

settings = get_settings()

LEDGER_FILE = "05_Q3_Q4_Insurance_Premium_Cost_Impact_Ledger.csv"

RLS_RESTRICTION_NOTICE = (
    "Zero-Trust RLS Notice: Granular department-level EBITDA and premium ledger figures "
    "(DOC-005 & DOC-008) require Upper-Layer Executive Clearance (Level 3). "
    "Switch persona to Arvind Mehta (CFO, CL:3) in the top sandbox bar to unlock full "
    "department financial allocations."
)

_FINANCE_WORDS = (
    "ebitda", "allocation", "budget", "premium", "variance", "cost", "financial",
)
_DEPT_WORDS = ("department", "dept")


def is_department_financial_query(query: str) -> bool:
    """True for EBITDA / cost-allocation / department-level financial questions."""
    q = query.lower()
    if "ebitda" in q or "cost allocation" in q:
        return True
    return any(w in q for w in _DEPT_WORDS) and any(w in q for w in _FINANCE_WORDS)


def inr(amount: float | int) -> str:
    """Indian digit grouping: 9382800 -> '93,82,800'."""
    n = int(round(float(amount)))
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = f"{head},{tail}"
    return f"{sign}{s}"


def load_department_ledger(db: Session) -> list[dict[str, Any]]:
    """Ledger rows (6 departments + TOTAL) with cost centers from the departments table."""
    cost_centers = {d.dept_id: d.cost_center_code for d in db.query(Department).all()}
    rows: list[dict[str, Any]] = []
    with open(settings.FILES_DIR / LEDGER_FILE, "r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append({
                "dept_id": r["dept_id"],
                "department_name": r["department_name"],
                "cost_center_code": cost_centers.get(r["dept_id"], "-"),
                "headcount": int(r["headcount"]),
                "legacy_2025_premium_inr": int(r["legacy_2025_premium_inr"]),
                "novashield_2026_premium_inr": int(r["novashield_2026_premium_inr"]),
                "parental_rider_variance_inr": int(r["parental_rider_variance_inr"]),
                "legacy_pro_rata_refund_inr": int(r["legacy_pro_rata_refund_inr"]),
                "net_budget_gap_inr": int(r["net_budget_gap_inr"]),
            })
    return rows


def ebitda_options(total_row: dict[str, Any]) -> dict[str, Any]:
    """EBITDA impact of DEC-2026-001 Option A / Option B (DOC-008)."""
    gap = total_row["net_budget_gap_inr"]
    return {
        "option_a_ebitda_impact_inr": -gap,
        "option_b_ebitda_impact_inr": 0,
        "legacycare_refund_inr": total_row["legacy_pro_rata_refund_inr"],
        "welfare_reserve_inr": gap,
        "welfare_reserve_cost_center": "CC-102",
        "copay_per_parent_inr": 600,
    }


def build_ledger_text(ledger: list[dict[str, Any]]) -> str:
    """Full department-level cost allocation + EBITDA text (used for the DOC-005 chunk)."""
    depts = [r for r in ledger if r["dept_id"] != "TOTAL"]
    total = next(r for r in ledger if r["dept_id"] == "TOTAL")
    eb = ebitda_options(total)
    lines = ["Department-level cost allocation under the NovaShield MSA (FY2026, INR):"]
    for r in depts:
        lines.append(
            f"{r['department_name']} ({r['dept_id']}, {r['headcount']} employees, {r['cost_center_code']}): "
            f"2025 LegacyCare INR {inr(r['legacy_2025_premium_inr'])} -> 2026 NovaShield INR {inr(r['novashield_2026_premium_inr'])} | "
            f"Parental Variance INR {inr(r['parental_rider_variance_inr'])} | "
            f"Legacy Refund Share INR {inr(r['legacy_pro_rata_refund_inr'])} | "
            f"Net Budget Gap INR {inr(r['net_budget_gap_inr'])}."
        )
    lines.append(
        f"Company Total ({total['headcount']} employees): 2025 Base INR {inr(total['legacy_2025_premium_inr'])} -> "
        f"2026 NovaShield MSA INR {inr(total['novashield_2026_premium_inr'])} | "
        f"Gross Parental Variance INR {inr(total['parental_rider_variance_inr'])} (+14%) | "
        f"LegacyCare Pro-Rata Refund INR {inr(total['legacy_pro_rata_refund_inr'])} | "
        f"Net Unfunded Gap INR {inr(total['net_budget_gap_inr'])}."
    )
    lines.append(
        f"EBITDA Impact (DOC-008): Option A (100% Margin Absorption) hits Q4 EBITDA by "
        f"-INR {inr(-eb['option_a_ebitda_impact_inr'])} (-19.2 Lakhs). Option B (Recommended Hybrid Buffer) applies the "
        f"INR {inr(eb['legacycare_refund_inr'])} LegacyCare refund plus INR {inr(eb['welfare_reserve_inr'])} "
        f"Q4 Staff Welfare Reserve ({eb['welfare_reserve_cost_center']}), giving INR 0 net EBITDA impact and keeping "
        f"employee co-pay flat at INR {eb['copay_per_parent_inr']}/parent."
    )
    return "\n".join(lines)
