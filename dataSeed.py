import os
import csv
import json
import uuid
import random
import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF
from docx import Document

# Deterministic seed so IDs and numbers stay 100% consistent across runs
random.seed(2026)

BASE_DIR = os.path.join(os.getcwd(), "enterprise_data_vault")
FILES_DIR = os.path.join(BASE_DIR, "files")
RDBMS_DIR = os.path.join(BASE_DIR, "rdbms")

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(RDBMS_DIR, exist_ok=True)


def safe_pdf_text(text: str) -> str:
    """Ensures clean Latin-1 encoding for standard PDF fonts across all OS platforms."""
    replacements = {
        "\u20b9": "INR ",
        "\u2014": "--",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "*",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


class EnterprisePDF(FPDF):
    def __init__(self, doc_title, doc_code, classification):
        super().__init__()
        self.doc_title = safe_pdf_text(doc_title)
        self.doc_code = safe_pdf_text(doc_code)
        self.classification = safe_pdf_text(classification)
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f"{self.doc_code} | {self.classification}", new_x="LMARGIN", new_y="NEXT", align="R")
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(20, 35, 60)
        self.cell(0, 8, self.doc_title, new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_draw_color(20, 35, 60)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()} | Confidential Enterprise Record - Generated Oct 2026", align="C")


def create_pdf(filename, title, doc_code, classification, sections):
    """Generates a multi-section enterprise PDF and returns extracted chunks for RDBMS vector seeding."""
    filepath = os.path.join(FILES_DIR, filename)
    pdf = EnterprisePDF(title, doc_code, classification)
    chunks = []

    for idx, sec in enumerate(sections, start=1):
        if idx == 1 or sec.get("new_page", False):
            pdf.add_page()
        page_num = pdf.page_no()
        sec_title = safe_pdf_text(sec["heading"])
        sec_body = safe_pdf_text(sec["body"])

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 55, 110)
        pdf.cell(0, 8, sec_title, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 6, sec_body)
        pdf.ln(3)

        chunks.append({
            "page_number": page_num,
            "section_title": sec["heading"],
            "chunk_text": f"{sec['heading']}: {sec['body']}"
        })

    pdf.output(filepath)
    return filepath, chunks


def create_docx(filename, title, metadata_header, sections):
    """Generates a structured .docx file and returns extracted chunks for RDBMS vector seeding."""
    filepath = os.path.join(FILES_DIR, filename)
    doc = Document()
    doc.add_heading(title, level=0)
    p_meta = doc.add_paragraph(metadata_header)
    p_meta.italic = True

    chunks = []
    for idx, sec in enumerate(sections, start=1):
        doc.add_heading(sec["heading"], level=1)
        doc.add_paragraph(sec["body"])
        chunks.append({
            "page_number": idx,
            "section_title": sec["heading"],
            "chunk_text": f"{sec['heading']}: {sec['body']}"
        })

    doc.save(filepath)
    return filepath, chunks


def create_csv(filename, headers, rows, summary_chunks=None):
    """Generates a structured .csv file and returns summary chunks for hybrid RAG."""
    filepath = os.path.join(FILES_DIR, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    chunks = summary_chunks or []
    if not chunks:
        preview = "; ".join([", ".join(map(str, r)) for r in rows[:5]])
        chunks.append({
            "page_number": 1,
            "section_title": f"CSV Schema & Sample ({filename})",
            "chunk_text": f"Columns: {', '.join(headers)}. Sample records: {preview}"
        })
    return filepath, chunks


# ==============================================================================
# 1. DEFINE CORE RDBMS ENTITIES (LAYERS, DEPARTMENTS, USERS, POLICIES)
# ==============================================================================

ORG_LAYERS = [
    {"layer_id": 3, "layer_code": "UPPER", "layer_name": "Strategic Executive Layer", "clearance_level": 3},
    {"layer_id": 2, "layer_code": "MIDDLE", "layer_name": "Tactical Management Layer", "clearance_level": 2},
    {"layer_id": 1, "layer_code": "LOWER", "layer_name": "Operational Execution Layer", "clearance_level": 1},
]

DEPARTMENTS = [
    {"dept_id": "DEPT-FIN", "dept_name": "Finance", "cost_center_code": "CC-101"},
    {"dept_id": "DEPT-HR",  "dept_name": "Human Resources", "cost_center_code": "CC-102"},
    {"dept_id": "DEPT-ENG", "dept_name": "Engineering", "cost_center_code": "CC-201"},
    {"dept_id": "DEPT-LEG", "dept_name": "Legal & Compliance", "cost_center_code": "CC-104"},
    {"dept_id": "DEPT-OPS", "dept_name": "Operations & Delivery", "cost_center_code": "CC-301"},
    {"dept_id": "DEPT-IT",  "dept_name": "IT & InfoSec", "cost_center_code": "CC-205"},
]

# Key Showcase Persona Users (for Judge Sandbox Switcher) + 500 Generated Employees
SHOWCASE_USERS = [
    {
        "user_id": "USR-UPPER-FIN-001",
        "dept_id": "DEPT-FIN",
        "layer_id": 3,
        "email": "arvind.mehta@kpipulse.com",
        "full_name": "Arvind Mehta",
        "job_title": "Chief Financial Officer (CFO)",
        "grade_tier": "L6",
        "ui_preferences_json": json.dumps({"default_view": "financial_decision_matrix", "show_sql_tables": True, "voice_speed": 1.0})
    },
    {
        "user_id": "USR-UPPER-HR-002",
        "dept_id": "DEPT-HR",
        "layer_id": 3,
        "email": "kavita.nair@kpipulse.com",
        "full_name": "Kavita Nair",
        "job_title": "Chief Human Resources Officer (CHRO)",
        "grade_tier": "L6",
        "ui_preferences_json": json.dumps({"default_view": "executive_policy_summary", "show_sql_tables": False, "voice_speed": 1.0})
    },
    {
        "user_id": "USR-MID-HR-003",
        "dept_id": "DEPT-HR",
        "layer_id": 2,
        "email": "priya.kulkarni@kpipulse.com",
        "full_name": "Priya Kulkarni",
        "job_title": "HR Operations & Benefits Lead",
        "grade_tier": "L4",
        "ui_preferences_json": json.dumps({"default_view": "migration_escalation_warroom", "show_sql_tables": True, "voice_speed": 1.05})
    },
    {
        "user_id": "USR-MID-IT-004",
        "dept_id": "DEPT-IT",
        "layer_id": 2,
        "email": "rohan.deshmukh@kpipulse.com",
        "full_name": "Rohan Deshmukh",
        "job_title": "IT Security & IAM Manager",
        "grade_tier": "L4",
        "ui_preferences_json": json.dumps({"default_view": "sso_api_integration_tracker", "show_sql_tables": True, "voice_speed": 1.0})
    },
    {
        "user_id": "USR-LOW-ENG-005",
        "dept_id": "DEPT-ENG",
        "layer_id": 1,
        "email": "naman.goel@kpipulse.com",
        "full_name": "Naman Goel",
        "job_title": "Senior Data & Full-Stack Engineer",
        "grade_tier": "L3",
        "ui_preferences_json": json.dumps({"default_view": "personal_benefits_and_voice_doc", "show_sql_tables": True, "voice_speed": 1.0})
    },
    {
        "user_id": "USR-LOW-OPS-006",
        "dept_id": "DEPT-OPS",
        "layer_id": 1,
        "email": "sneha.patil@kpipulse.com",
        "full_name": "Sneha Patil",
        "job_title": "Operations Delivery Analyst",
        "grade_tier": "L2",
        "ui_preferences_json": json.dumps({"default_view": "personal_benefits_and_voice_doc", "show_sql_tables": False, "voice_speed": 1.0})
    }
]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Riya", "Ananya", "Diya", "Ishita", "Neha", "Siddharth", "vikram", "Pooja", "Rahul", "Karan", "Meera", "Tanvi", "Varun", "Nikhil"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Joshi", "Patel", "Kulkarni", "Reddy", "Iyer", "Chatterjee", "bansal", "Malhotra", "Kapoor", "Desai", "Jain", "Rao"]
CITIES = ["Pune", "Mumbai", "Bengaluru", "Hyderabad", "Delhi NCR", "Singapore"]

ALL_USERS = list(SHOWCASE_USERS)
for i in range(7, 501):
    dept = random.choice(DEPARTMENTS)
    layer_roll = random.random()
    if layer_roll < 0.06:
        layer_id, grade = 3, "L6"
    elif layer_roll < 0.25:
        layer_id, grade = 2, random.choice(["L4", "L5"])
    else:
        layer_id, grade = 1, random.choice(["L1", "L2", "L3"])

    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    ALL_USERS.append({
        "user_id": f"USR-{i:04d}",
        "dept_id": dept["dept_id"],
        "layer_id": layer_id,
        "email": f"{fn.lower()}.{ln.lower()}{i}@kpipulse.com",
        "full_name": f"{fn.capitalize()} {ln.capitalize()}",
        "job_title": f"{dept['dept_name']} {'Director' if layer_id==3 else ('Manager' if layer_id==2 else 'Specialist')}",
        "grade_tier": grade,
        "ui_preferences_json": json.dumps({"default_view": "standard", "voice_speed": 1.0})
    })

VENDORS_POLICIES = [
    {
        "policy_id": "POL-LEGACY-2025",
        "vendor_name": "LegacyCare Assurance Ltd.",
        "policy_number": "LC-GMC-2025-8841",
        "status": "OLD_EXPIRING",
        "effective_date": "2025-10-20",
        "expiry_date": "2026-10-20",
        "annual_premium": 18500000.00,
        "tpa_contact": "claims-desk@legacycaretpa.in"
    },
    {
        "policy_id": "POL-NOVASHIELD-2026",
        "vendor_name": "NovaShield Health & General Insurance",
        "policy_number": "NS-CORP-2026-9920",
        "status": "NEW_ACTIVE",
        "effective_date": "2026-10-21",
        "expiry_date": "2027-10-20",
        "annual_premium": 22340000.00,
        "tpa_contact": "priority-corp@novashieldhealth.com"
    }
]

# ==============================================================================
# 2. GENERATE ALL 22 REALISTIC FILES
# ==============================================================================

DOCUMENTS_REGISTRY = []
ALL_DOCUMENT_CHUNKS = []


def register_doc(doc_id, filename, file_type, dept_id, min_layer, uploaded_by, chunks):
    DOCUMENTS_REGISTRY.append({
        "doc_id": doc_id,
        "uploaded_by": uploaded_by,
        "dept_id": dept_id,
        "min_layer_clearance": min_layer,
        "file_name": filename,
        "file_type": file_type,
        "gcs_uri": f"gs://kpipulse-enterprise-vault-2026/{filename}",
        "version": "v2.4-2026"
    })
    for c in chunks:
        ALL_DOCUMENT_CHUNKS.append({
            "chunk_id": f"CHK-{uuid.uuid4().hex[:10].upper()}",
            "doc_id": doc_id,
            "page_number": c["page_number"],
            "section_title": c["section_title"],
            "chunk_text": c["chunk_text"]
        })


print("Generating 22 Enterprise Files across PDFs, CSVs, and DOCX...")

# --- FILE 01 ---
_, chunks = create_pdf(
    "01_LegacyCare_Expiring_Master_Policy_2025.pdf",
    "LegacyCare Assurance Group Mediclaim Policy (2025-2026)",
    "DOC-01 | POL-LEGACY-2025",
    "Clearance: All Layers (L1-L3)",
    [
        {"heading": "Section 1: Policy Coverage & Expiry Notice",
         "body": "Policy Number LC-GMC-2025-8841 underwritten by LegacyCare Assurance Ltd. expires at 23:59 IST on October 20, 2026. Total covered lives: 500 employees + 920 dependents. Annual base premium: INR 1,85,00,000."},
        {"heading": "Section 4: Room Rent & ICU Sub-Limits (Legacy Terms)",
         "body": "Under LegacyCare 2025 terms, normal hospital room rent is strictly capped at 1% of Base Sum Insured per day (INR 5,000/day for a INR 5,00,000 policy). ICU charges are capped at 2% of Sum Insured per day. Proportionate deduction applies if the insured selects a higher room category."},
        {"heading": "Section 8: Disease-Wise Sub-Limits & Cataract Cap",
         "body": "8.1 Maternity Benefit: Normal delivery capped at INR 50,000; C-Section capped at INR 65,000.\n8.3 Cataract Surgery Limit: Strictly capped at INR 35,000 per eye inclusive of monofocal lens and surgeon fees.\n8.4 Parental Coverage: Co-pay of 20% mandatory on all parental claims at non-preferred hospitals."},
        {"heading": "Section 12: Mid-Term Termination & Pro-Rata Refund Clause",
         "body": "Upon policy transition and early closure of the OPD corporate buffer pool, LegacyCare shall issue a pro-rata unutilized buffer credit of INR 19,20,000 within 15 business days of final claim reconciliation.", "new_page": True}
    ]
)
register_doc("DOC-001", "01_LegacyCare_Expiring_Master_Policy_2025.pdf", "PDF", "DEPT-HR", 1, "USR-MID-HR-003", chunks)

# --- FILE 02 ---
_, chunks = create_pdf(
    "02_NovaShield_New_Master_Service_Agreement_2026.pdf",
    "NovaShield Health Master Group Insurance Agreement (2026-2027)",
    "DOC-02 | POL-NOVASHIELD-2026",
    "Clearance: Middle & Upper Layers (L2-L3)",
    [
        {"heading": "Section 1: Master Policy Activation & Premium",
         "body": "Policy Number NS-CORP-2026-9920 becomes effective October 21, 2026 at 00:00 IST. Total Annual Premium including enhanced parental rider stands at INR 2,23,40,000 (an increase of INR 38,40,000 driven by a 14% actuarial revision on parental dependency riders)."},
        {"heading": "Section 4.2: Zero Overtime & Portal Maintenance Clause",
         "body": "NovaShield TPA and technical integration teams shall provide 24x7 API and SAML 2.0 SSO maintenance at no additional cost. Weekend maintenance and migration support are included in the base administrative fee; overtime billing is strictly prohibited.", "new_page": True},
        {"heading": "Section 6: Enhanced Room Rent & Cashless Turnaround SLA",
         "body": "6.1 Room Rent Upgrade: Capped at Single Private AC Room (no 1% monetary ceiling for L1-L4 employees).\n6.2 Cashless Pre-Authorization SLA: Guaranteed approval within 120 minutes (2 hours) for planned and emergency admissions. SLA breaches beyond 180 minutes incur a penalty credit of INR 15,000 per incident."},
        {"heading": "Section 8.3: Upgraded Cataract, Maternity & Robotic Surgery Limits",
         "body": "8.1 Maternity Benefit: Upgraded to INR 1,00,000 for both normal and C-section deliveries with zero waiting period.\n8.3 Cataract Surgery Limit: Upgraded to INR 45,000 per eye (INR 10,000 higher than the outgoing 2025 policy), covering multifocal and toric intraocular lenses at all network hospitals including Sahyadri Hospital Pune and Apollo Hospitals.\n8.5 Parental Rider Co-Pay: Reduced from 20% to 10% across all Tier-1 network hospitals.", "new_page": True}
    ]
)
register_doc("DOC-002", "02_NovaShield_New_Master_Service_Agreement_2026.pdf", "PDF", "DEPT-LEG", 2, "USR-UPPER-HR-002", chunks)

# --- FILE 03 ---
_, chunks = create_docx(
    "03_Old_vs_New_Policy_Benefit_Comparison_Addendum.docx",
    "Legal Redline: LegacyCare (2025) vs. NovaShield Health (2026)",
    "Prepared by: Legal & HR Benefits Team | Effective Date: October 21, 2026 | Clearance: L1-L3",
    [
        {"heading": "1. Core Coverage Upgrades",
         "body": "Base Sum Insured remains INR 5,00,000 for L1-L3, INR 7,50,000 for L4-L5, and INR 10,00,000 for L6 executives. Employees may voluntarily top-up an additional INR 5,00,000 by October 22, 2026."},
        {"heading": "2. Side-by-Side Benefit Comparison",
         "body": "- Cataract Surgery: Increased from INR 35,000/eye (LegacyCare) to INR 45,000/eye (NovaShield).\n- Maternity Limit: Increased from INR 50,000 to INR 1,00,000.\n- Parental Co-pay: Reduced from 20% to 10%.\n- Pre-Existing Diseases (PED): 100% waived from Day 1 for both employees and enrolled parents provided parental opt-in is confirmed before the cutoff window."},
        {"heading": "3. Critical Transition Warning (Parental Rider Re-Confirmation)",
         "body": "Under Clause 9.4 of the NovaShield transition addendum, existing parental enrollments do NOT auto-renew without employee consent due to revised co-pay payroll structures. Every employee with enrolled parents must click 'Confirm Parental Rider' in the portal before the cutoff date."}
    ]
)
register_doc("DOC-003", "03_Old_vs_New_Policy_Benefit_Comparison_Addendum.docx", "DOCX", "DEPT-LEG", 1, "USR-MID-HR-003", chunks)

# --- FILE 04 ---
_, chunks = create_pdf(
    "04_DPDP_HIPAA_Medical_Data_Privacy_Compliance_Audit.pdf",
    "DPDP Act 2023 & HIPAA Medical Data Privacy Audit Report",
    "DOC-04 | INFOSEC-AUDIT-2026",
    "Clearance: Middle & Upper Layers (L2-L3)",
    [
        {"heading": "1. Executive Compliance Summary",
         "body": "Audit conducted by IT Security & Legal on the data migration pipeline from LegacyCare to NovaShield Health. Employee medical history, diagnosis codes (ICD-10), and dependent Aadhaar/DOB details classify as Sensitive Personal Data under India's DPDP Act and HIPAA standards."},
        {"heading": "2. Mandatory Zero-Trust & Row-Level Security Controls",
         "body": "1. Raw dependent medical claim reasons must never be exposed to Department Managers outside HR Benefits.\n2. AI assistants querying company databases must enforce PostgreSQL Row-Level Security (RLS) so Lower-layer employees can only query their own `user_id` enrollment records.\n3. Nightly census sync CSVs must mask Aadhaar digits (XXXX-XXXX-1234) prior to SFTP/API transmission."}
    ]
)
register_doc("DOC-004", "04_DPDP_HIPAA_Medical_Data_Privacy_Compliance_Audit.pdf", "PDF", "DEPT-IT", 2, "USR-MID-IT-004", chunks)

# --- FILE 05 ---
cost_headers = ["dept_id", "department_name", "headcount", "legacy_2025_premium_inr", "novashield_2026_premium_inr", "parental_rider_variance_inr", "legacy_pro_rata_refund_inr", "net_budget_gap_inr"]
cost_rows = [
    ["DEPT-ENG", "Engineering", 210, 7770000, 9382800, 1612800, 806400, 806400],
    ["DEPT-OPS", "Operations & Delivery", 130, 4810000, 5808400, 998400, 499200, 499200],
    ["DEPT-FIN", "Finance", 45, 1665000, 2010600, 345600, 172800, 172800],
    ["DEPT-HR",  "Human Resources", 40, 1480000, 1787200, 307200, 153600, 153600],
    ["DEPT-IT",  "IT & InfoSec", 45, 1665000, 2010600, 345600, 172800, 172800],
    ["DEPT-LEG", "Legal & Compliance", 30, 1110000, 1340400, 230400, 115200, 115200],
    ["TOTAL",    "All Departments", 500, 18500000, 22340000, 3840000, 1920000, 1920000]
]
_, chunks = create_csv(
    "05_Q3_Q4_Insurance_Premium_Cost_Impact_Ledger.csv",
    cost_headers,
    cost_rows,
    [{"page_number": 1, "section_title": "Q3-Q4 Insurance Cost Variance Summary",
      "chunk_text": "Total 2025 LegacyCare Premium: INR 1,85,00,000. Total 2026 NovaShield Premium: INR 2,23,40,000. Gross Parental Rider Variance: INR 38,40,000 (INR 38.4 Lakhs). Unutilized LegacyCare Pro-Rata Refund available: INR 19,20,000 (INR 19.2 Lakhs). Net unfunded budget gap if split 50/50: INR 19,20,000."}]
)
register_doc("DOC-005", "05_Q3_Q4_Insurance_Premium_Cost_Impact_Ledger.csv", "CSV", "DEPT-FIN", 3, "USR-UPPER-FIN-001", chunks)

# --- FILE 06 ---
copay_headers = ["employee_id", "full_name", "grade_tier", "base_sum_insured_inr", "parents_enrolled_count", "old_monthly_deduction_inr", "new_monthly_deduction_full_pass_inr", "new_monthly_deduction_hybrid_option_b_inr", "topup_5l_monthly_cost_inr"]
copay_rows = []
for u in ALL_USERS:
    p_count = 2 if u["user_id"] == "USR-LOW-ENG-005" else random.choice([0, 1, 2])
    base_si = 500000 if u["grade_tier"] in ["L1", "L2", "L3"] else (750000 if u["grade_tier"] in ["L4", "L5"] else 1000000)
    old_ded = p_count * 600
    full_pass = p_count * 920
    hybrid_b = p_count * 600  # Option B keeps employee monthly deduction unchanged by applying refund + company buffer
    copay_rows.append([u["user_id"], u["full_name"], u["grade_tier"], base_si, p_count, old_ded, full_pass, hybrid_b, 450])

_, chunks = create_csv(
    "06_Employee_Parental_CoPay_Payroll_Deduction_Schedule.csv",
    copay_headers,
    copay_rows,
    [{"page_number": 1, "section_title": "Parental Co-Pay & Top-Up Payroll Schedule",
      "chunk_text": "For Grade L1-L3 employees (Base Sum Insured INR 5,00,000), current parental monthly salary deduction is INR 600 per parent (INR 1,200/month for 2 parents). Under full hike pass-through (Option C), it rises to INR 920/parent (INR 1,840/month). Under Executive Option B (Hybrid), monthly deduction stays INR 600/parent. Optional INR 5,00,000 Sum Insured upgrade costs INR 450/month deducted from October payslip."}]
)
register_doc("DOC-006", "06_Employee_Parental_CoPay_Payroll_Deduction_Schedule.csv", "CSV", "DEPT-FIN", 1, "USR-UPPER-FIN-001", chunks)

# --- FILE 07 ---
claims_headers = ["claim_id", "user_id", "employee_name", "department", "hospital_name", "city", "treatment_type", "claim_amount_inr", "claim_stage", "blocker_reason"]
claims_rows = [
    ["CLM-2026-901", "USR-LOW-ENG-005", "Naman Goel", "Engineering", "Sahyadri Hospital", "Pune", "Parental Cataract Pre-Auth Inquiry", 45000, "PRE_AUTH_DRAFT", "Awaiting Parental Rider Re-confirmation before Oct 22"],
    ["CLM-2026-902", "USR-LOW-OPS-006", "Sneha Patil", "Operations & Delivery", "Ruby Hall Clinic", "Pune", "Maternity Admission", 95000, "STUCK_IN_TRANSITION", "Admitted Oct 19 under LegacyCare; discharge Oct 22 falls in NovaShield window"],
    ["CLM-2026-903", "USR-0014", "Vivaan Sharma", "Engineering", "Apollo Hospital", "Bengaluru", "Cardiac Angioplasty", 285000, "STUCK_IN_TRANSITION", "LegacyCare TPA froze cashless approval 48h prior to policy expiry"],
    ["CLM-2026-904", "USR-0029", "Ananya Joshi", "Finance", "Fortis Hospital", "Mumbai", "Orthopedic ACL Repair", 165000, "STUCK_IN_TRANSITION", "Split billing required between LegacyCare and NovaShield TPA"],
    ["CLM-2026-905", "USR-0042", "Siddharth Iyer", "IT & InfoSec", "Manipal Hospital", "Bengaluru", "Chemotherapy Daycare Cycle 4", 110000, "STUCK_IN_TRANSITION", "Pre-existing continuity certificate pending from LegacyCare"],
    ["CLM-2026-906", "USR-0088", "Meera Kulkarni", "Engineering", "Sahyadri Hospital", "Pune", "Gallbladder Laparoscopy", 125000, "STUCK_IN_TRANSITION", "TPA portal blackout window Oct 20-21"],
    ["CLM-2026-907", "USR-0104", "Rahul Verma", "Operations & Delivery", "Apollo Hospital", "Hyderabad", "Dialysis Package", 78000, "STUCK_IN_TRANSITION", "Awaiting new NovaShield E-Card generation"],
    ["CLM-2026-908", "USR-0119", "Diya Patel", "Human Resources", "Kokilaben Hospital", "Mumbai", "Maternity C-Section", 98000, "STUCK_IN_TRANSITION", "Transition overlap admission"],
    ["CLM-2026-909", "USR-0155", "Karan Malhotra", "Engineering", "Max Super Speciality", "Delhi NCR", "Appendectomy Emergency", 142000, "STUCK_IN_TRANSITION", "Cashless desk awaiting NovaShield policy activation code"],
    ["CLM-2026-910", "USR-0201", "Pooja Reddy", "Finance", "Mount Elizabeth Hospital", "Singapore", "Diagnostic MRI & Specialist", 155000, "STUCK_IN_TRANSITION", "APAC cross-border reimbursement currency conversion hold"],
    ["CLM-2026-911", "USR-0244", "Vikram Kapoor", "Legal & Compliance", "Ruby Hall Clinic", "Pune", "Parental Bilateral Cataract", 82000, "STUCK_IN_TRANSITION", "Pending LegacyCare NOC"],
    ["CLM-2026-912", "USR-0310", "Tanvi Bansal", "Engineering", "Apollo Hospital", "Mumbai", "Renal Calculus Laser", 85000, "STUCK_IN_TRANSITION", "Discharge summary pending TPA verification"]
]
_, chunks = create_csv(
    "07_Pending_Reimbursement_Claims_Transition_Audit.csv",
    claims_headers,
    claims_rows,
    [{"page_number": 1, "section_title": "In-Flight Transition Claims Audit",
      "chunk_text": "There are 11 active high-priority hospital claims (plus 1 pre-auth draft for USR-LOW-ENG-005 Naman Goel at Sahyadri Hospital Pune for INR 45,000 cataract surgery) totaling INR 14,20,000 (INR 14.2 Lakhs) caught between the LegacyCare Oct 20 cutoff and NovaShield Oct 21 activation."}]
)
register_doc("DOC-007", "07_Pending_Reimbursement_Claims_Transition_Audit.csv", "CSV", "DEPT-HR", 2, "USR-MID-HR-003", chunks)

# --- FILE 08 ---
_, chunks = create_pdf(
    "08_CFO_Budget_Reallocation_Proposal_Parental_Buffer.pdf",
    "CFO Executive Decision Memo: Resolving the INR 38.4L Parental Premium & Cutoff Conflict",
    "DOC-08 | FIN-EXEC-MEMO-2026",
    "Clearance: Upper Layer Only (L3 Executive)",
    [
        {"heading": "1. Executive Problem Statement",
         "body": "Switching from LegacyCare to NovaShield Health introduces an annual premium increase of INR 38,40,000 (14% hike on parental coverage). Simultaneously, Finance scheduled the October payroll deduction lock for October 20, while IT's SAML SSO portal goes live on October 23, creating a 3-day gap where 142 employees cannot confirm their parental riders."},
        {"heading": "2. Quantified Decision Matrix (3 Options for CFO/CEO Approval)",
         "body": "OPTION A (100% Company Absorption): Company absorbs all INR 38.4 Lakhs from Q4 operating margin. Zero increase to employee deductions. Direct EBITDA impact: -INR 19.2 Lakhs after applying the INR 19.2L LegacyCare refund.\n\nOPTION B (Recommended Hybrid Buffer + 5-Day Grace Window): Apply the INR 19,20,000 LegacyCare pro-rata refund to cover 50% of the hike, fund the remaining INR 19,20,000 from the unallocated Q4 Staff Welfare Reserve (CC-102), freeze employee monthly parental co-pay at INR 600/parent for FY26-27, and instruct Finance & NovaShield to extend the payroll/portal opt-in cutoff to October 25, 2026.\n\nOPTION C (100% Employee Pass-Through): Pass the entire INR 38.4L hike to employees (increasing deduction from INR 600 to INR 920/parent). High attrition risk flagged in Engineering and Operations."}
    ]
)
register_doc("DOC-008", "08_CFO_Budget_Reallocation_Proposal_Parental_Buffer.pdf", "PDF", "DEPT-FIN", 3, "USR-UPPER-FIN-001", chunks)

# --- FILE 09 ---
census_headers = ["enrollment_id", "user_id", "full_name", "dept_id", "layer_id", "policy_id", "sum_insured_inr", "dependents_count", "parental_opt_in_status", "monthly_copay_inr", "migration_status"]
census_rows = []
pending_count = 0
for idx, u in enumerate(ALL_USERS, start=1):
    if u["user_id"] == "USR-LOW-ENG-005":
        opt_status = "PENDING_CONFIRMATION"
        mig_status = "ACTION_REQUIRED_BY_OCT_22"
        dep_cnt,si, copay = 2, 500000, 1200
        pending_count += 1
    elif pending_count < 142 and idx % 3 == 0:
        opt_status = "PENDING_CONFIRMATION"
        mig_status = "BLOCKED_BY_SSO_PORTAL_DELAY"
        dep_cnt, si, copay = 2, 500000, 1200
        pending_count += 1
    else:
        opt_status = "CONFIRMED"
        mig_status = "MIGRATED_TO_NOVASHIELD"
        dep_cnt, si, copay = random.choice([1, 2, 3]), 500000, 600

    census_rows.append([
        f"ENR-{idx:04d}", u["user_id"], u["full_name"], u["dept_id"], u["layer_id"],
        "POL-NOVASHIELD-2026", si, dep_cnt, opt_status, copay, mig_status
    ])

_, chunks = create_csv(
    "09_Master_Employee_Dependent_Census_Migration_2026.csv",
    census_headers,
    census_rows,
    [{"page_number": 1, "section_title": "Master Census Migration Status",
      "chunk_text": "Out of 500 employees, 358 are fully migrated to POL-NOVASHIELD-2026, while exactly 142 employees (including USR-LOW-ENG-005 Naman Goel) have status PENDING_CONFIRMATION for parental riders due to the SSO portal rollout gap."}]
)
register_doc("DOC-009", "09_Master_Employee_Dependent_Census_Migration_2026.csv", "CSV", "DEPT-HR", 2, "USR-MID-HR-003", chunks)

# --- FILE 10 ---
hosp_headers = ["hospital_id", "hospital_name", "city", "specialty_tier", "legacycare_status", "novashield_2026_status", "cashless_desk_phone", "direct_admission_sla_mins"]
base_hospitals = [
    ["HOSP-001", "Sahyadri Super Speciality Hospital", "Pune", "Tier-1 Multi-Specialty & Ophthalmology", "ACTIVE", "ACTIVE_PREFERRED", "+91-20-67213000", 90],
    ["HOSP-002", "Ruby Hall Clinic", "Pune", "Tier-1 Multi-Specialty & Maternity", "ACTIVE", "ACTIVE_PREFERRED", "+91-20-66455100", 120],
    ["HOSP-003", "Jehangir Hospital", "Pune", "Tier-1 General & Orthopedics", "ACTIVE", "ACTIVE", "+91-20-66819999", 120],
    ["HOSP-004", "LifeCare Annex Clinic", "Pune", "Tier-3 Nursing Home", "ACTIVE", "BLACKLISTED_BILLING_FRAUD", "N/A", 0],
    ["HOSP-005", "Apollo Hospitals", "Mumbai", "Tier-1 Quaternary Care", "ACTIVE", "ACTIVE_PREFERRED", "+91-22-33503350", 90],
    ["HOSP-006", "Fortis Hospital Mulund", "Mumbai", "Tier-1 Cardiac & Ortho", "ACTIVE", "ACTIVE_PREFERRED", "+91-22-41114111", 120],
    ["HOSP-007", "Kokilaben Dhirubhai Ambani Hospital", "Mumbai", "Tier-1 Multi-Specialty", "ACTIVE", "ACTIVE_PREFERRED", "+91-22-42696969", 90],
    ["HOSP-008", "Apollo Hospitals Bannerghatta", "Bengaluru", "Tier-1 Multi-Specialty", "ACTIVE", "ACTIVE_PREFERRED", "+91-80-26304050", 90],
    ["HOSP-009", "Manipal Hospital Old Airport Rd", "Bengaluru", "Tier-1 Oncology & Surgery", "ACTIVE", "ACTIVE_PREFERRED", "+91-80-25024444", 120],
    ["HOSP-010", "Apollo Health City Jubilee Hills", "Hyderabad", "Tier-1 Multi-Specialty", "ACTIVE", "ACTIVE_PREFERRED", "+91-40-23607777", 90],
    ["HOSP-011", "Max Super Speciality Hospital Saket", "Delhi NCR", "Tier-1 Multi-Specialty", "ACTIVE", "ACTIVE_PREFERRED", "+91-11-26515050", 120],
    ["HOSP-012", "Mount Elizabeth Hospital", "Singapore", "APAC International Partner", "REIMBURSEMENT_ONLY", "ACTIVE_CASHLESS_APAC", "+65-67372666", 120]
]
hosp_rows = list(base_hospitals)
for h_i in range(13, 151):
    c = random.choice(CITIES)
    hosp_rows.append([
        f"HOSP-{h_i:03d}", f"{c} Care Medical Center #{h_i}", c, "Tier-2 General Hospital",
        "ACTIVE", random.choice(["ACTIVE", "ACTIVE_PREFERRED"]), "+91-1800-102-9920", 120
    ])

_, chunks = create_csv(
    "10_Cashless_Network_Hospitals_Master_Directory.csv",
    hosp_headers,
    hosp_rows,
    [{"page_number": 1, "section_title": "Verified Cashless Hospital Network Directory (2026)",
      "chunk_text": "Sahyadri Super Speciality Hospital (Pune) and Ruby Hall Clinic (Pune) are ACTIVE_PREFERRED on the NovaShield 2026 cashless network with 90-120 min pre-auth SLA. Apollo Hospitals (Mumbai, Bengaluru, Hyderabad), Fortis, Manipal, Max Delhi, and Mount Elizabeth Hospital (Singapore) are ACTIVE_PREFERRED. Note: LifeCare Annex Clinic (Pune) was BLACKLISTED due to billing irregularities."}]
)
register_doc("DOC-010", "10_Cashless_Network_Hospitals_Master_Directory.csv", "CSV", "DEPT-HR", 1, "USR-MID-HR-003", chunks)

# --- FILE 11 ---
_, chunks = create_pdf(
    "11_Employee_Handbook_New_Health_Benefit_Guide_2026.pdf",
    "2026 Employee Health Benefits & Cashless Claim Handbook",
    "DOC-11 | HR-HANDBOOK-2026",
    "Clearance: All Employees (L1-L3)",
    [
        {"heading": "Section 1: Welcome to NovaShield Health (Effective Oct 21, 2026)",
         "body": "Starting October 21, 2026, our corporate group health insurance transitions from LegacyCare Assurance to NovaShield Health (Policy #NS-CORP-2026-9920). Your coverage continues seamlessly with zero waiting periods for pre-existing diseases."},
        {"heading": "Section 4: Step-by-Step Cashless Hospitalization Process",
         "body": "1. Visit any active NovaShield Cashless Network Hospital (such as Sahyadri Hospital or Ruby Hall Clinic in Pune, or Apollo Hospitals).\n2. Present your digital NovaShield E-Card at the hospital TPA desk at least 48 hours prior for planned surgeries (like cataract or maternity) or within 24 hours for emergency admission.\n3. NovaShield guarantees cashless pre-authorization within 120 minutes."},
        {"heading": "Section 8.3: Quick Reference Benefit Table (2026 Upgrades)",
         "body": "- Base Sum Insured: INR 5,00,000 (Grades L1-L3), upgradeable to INR 10,00,000 for INR 450/month.\n- Cataract Surgery Limit: Covered up to INR 45,000 per eye (increased by INR 10,000 over last year's INR 35,000 limit). Multifocal lenses included.\n- Maternity Coverage: INR 1,00,000 for normal or C-section delivery.\n- Annual Executive Health Checkup: Free cashless checkup for employee + spouse once per policy year.\n- Action Required: If you have parents enrolled, you must click 'Confirm Parental Rider' in your portal by October 22, 2026.", "new_page": True}
    ]
)
register_doc("DOC-011", "11_Employee_Handbook_New_Health_Benefit_Guide_2026.pdf", "PDF", "DEPT-HR", 1, "USR-MID-HR-003", chunks)

# --- FILE 12 ---
_, chunks = create_docx(
    "12_Blackout_Period_Emergency_Hospitalization_SOP.docx",
    "SOP: Handling Emergency Admissions During Oct 20-21 Vendor Cutover",
    "Document Owner: HR Operations | Clearance: L1-L3",
    [
        {"heading": "1. Cutover Blackout Window Definition",
         "body": "While policy coverage has zero gap between October 20 (23:59 IST) and October 21 (00:00 IST), the automated E-Card generation portal will undergo scheduled migration maintenance for 14 hours."},
        {"heading": "2. Emergency Admission Protocol (Green Channel)",
         "body": "If an employee or dependent is hospitalized during the migration window, show Corporate Policy Code 'NS-CORP-2026-9920' at the hospital desk and trigger an immediate Green Channel Provisional Approval via HR Escalation Lead Priya Kulkarni (+91-98200-11223). Hospital deposits are waived under our corporate guarantee."}
    ]
)
register_doc("DOC-012", "12_Blackout_Period_Emergency_Hospitalization_SOP.docx", "DOCX", "DEPT-HR", 1, "USR-MID-HR-003", chunks)

# --- FILE 13 ---
esc_headers = ["escalation_id", "claim_id", "user_id", "assigned_hr_id", "priority_level", "hospital_name", "issue_summary", "sla_deadline", "resolution_status"]
esc_rows = [
    ["ESC-101", "CLM-2026-902", "USR-LOW-OPS-006", "USR-MID-HR-003", "P0_CRITICAL", "Ruby Hall Clinic, Pune", "Maternity admission spans Oct 19-22 vendor cutover", "2026-10-20 18:00", "OPEN_NEEDS_TPA_BRIDGE"],
    ["ESC-102", "CLM-2026-903", "USR-0014", "USR-MID-HR-003", "P0_CRITICAL", "Apollo Hospital, Bengaluru", "Cardiac stent cashless hold of INR 2,85,000", "2026-10-20 14:00", "OPEN_NEEDS_CFO_GUARANTEE"],
    ["ESC-103", "CLM-2026-905", "USR-0042", "USR-MID-HR-003", "P1_HIGH", "Manipal Hospital, Bengaluru", "Daycare chemotherapy continuity waiver", "2026-10-21 10:00", "IN_PROGRESS"]
]
_, chunks = create_csv(
    "13_HR_Escalation_Log_High_Priority_Medical_Cases.csv",
    esc_headers,
    esc_rows,
    [{"page_number": 1, "section_title": "Active P0/P1 Medical Escalations",
      "chunk_text": "HR Lead Priya Kulkarni (USR-MID-HR-003) is tracking 3 critical escalations (ESC-101 Maternity at Ruby Hall Pune, ESC-102 Cardiac at Apollo Bengaluru, ESC-103 Chemo at Manipal) that require split-billing NOC between LegacyCare and NovaShield."}]
)
register_doc("DOC-013", "13_HR_Escalation_Log_High_Priority_Medical_Cases.csv", "CSV", "DEPT-HR", 2, "USR-MID-HR-003", chunks)

# --- FILE 14 ---
_, chunks = create_pdf(
    "14_HRMS_to_NovaShield_API_SSO_Architecture_Spec.pdf",
    "Technical Specification: HRMS to NovaShield SAML 2.0 SSO & Census Sync API",
    "DOC-14 | IT-ARCH-SPEC-2026",
    "Clearance: Engineering & IT (L1-L3)",
    [
        {"heading": "1. SAML 2.0 Single Sign-On Flow",
         "body": "Employees authenticate via corporate Google Workspace IdP. SAML assertions pass `user_id`, `grade_tier`, and `dept_id` to NovaShield's benefit portal endpoint (`https://sso.novashieldhealth.com/saml2/acs`)."},
        {"heading": "2. Deployment Timeline & Current Blocker",
         "body": "Scheduled production deployment of the SAML 2.0 SSO enrollment widget is pushed to October 23, 2026 at 16:00 IST because NovaShield's sandbox OAuth2 refresh token throws an `ERR_TOKEN_TTL_MISMATCH` after 300 seconds. Until October 23, employees cannot use self-service SSO on the vendor's external portal."}
    ]
)
register_doc("DOC-014", "14_HRMS_to_NovaShield_API_SSO_Architecture_Spec.pdf", "PDF", "DEPT-IT", 1, "USR-MID-IT-004", chunks)

# --- FILE 15 ---
_, chunks = create_docx(
    "15_IT_Security_Vulnerability_Test_TPA_Portal.docx",
    "Penetration Test & QA Report: NovaShield TPA Integration",
    "Prepared by: Rohan Deshmukh (IT Security Manager) | Date: October 15, 2026 | Clearance: L2-L3",
    [
        {"heading": "1. API Token Expiry Bug (Severity: High)",
         "body": "During load testing of 500 concurrent employee logins, the NovaShield mobile callback API dropped session state due to a 5-minute JWT clock skew. Vendor patch v2.1.4 arrives October 22; IT QA sign-off and production go-live will complete on October 23, 2026."},
        {"heading": "2. Mitigation via Internal Enterprise Copilot",
         "body": "While the external TPA SSO portal is delayed until October 23, employees CAN immediately confirm their parental rider and query their policy directly inside our internal Cloud Run Enterprise Workspace, which writes directly to our Cloud SQL database."}
    ]
)
register_doc("DOC-015", "15_IT_Security_Vulnerability_Test_TPA_Portal.docx", "DOCX", "DEPT-IT", 2, "USR-MID-IT-004", chunks)

# --- FILE 16 ---
tracker_headers = ["task_id", "dept_id", "assigned_to_user_id", "layer_id", "task_title", "due_date", "status", "dependency_task_id", "blocker_note"]
tracker_rows = [
    ["TSK-01", "DEPT-LEG", "USR-UPPER-HR-002", 3, "Execute NovaShield Master Service Agreement", "2026-10-14", "COMPLETED", "NONE", "Signed and archived"],
    ["TSK-02", "DEPT-FIN", "USR-UPPER-FIN-001", 3, "Approve INR 38.4L Parental Premium Variance Option", "2026-10-18", "PENDING_CFO_DECISION", "TSK-01", "Awaiting CFO selection of Option A, B, or C"],
    ["TSK-03", "DEPT-FIN", "USR-UPPER-FIN-001", 2, "Lock October Payroll Co-Pay Deductions", "2026-10-20", "CONFLICT_FLAGGED", "TSK-05", "CONFLICT: Scheduled for Oct 20, but IT SSO portal (TSK-05) isn't ready until Oct 23!"],
    ["TSK-04", "DEPT-HR",  "USR-MID-HR-003",   2, "Migrate 142 Pending Employee Parental Riders", "2026-10-22", "AT_RISK", "TSK-02", "142 employees awaiting cutoff extension & portal access"],
    ["TSK-05", "DEPT-IT",  "USR-MID-IT-004",   2, "Deploy SAML 2.0 SSO & Patch JWT Bug", "2026-10-23", "IN_PROGRESS", "TSK-01", "Vendor patch v2.1.4 scheduled for Oct 22 night"],
    ["TSK-06", "DEPT-HR",  "USR-MID-HR-003",   2, "Clear 11 Stuck Transition Hospital Claims (INR 14.2L)", "2026-10-21", "IN_PROGRESS", "TSK-02", "Requires LegacyCare-NovaShield bridge sign-off"],
    ["TSK-07", "DEPT-ENG", "USR-LOW-ENG-005",  1, "Verify Webhook Sync for Nightly Census Delta", "2026-10-22", "IN_PROGRESS", "TSK-05", "Staging tests passing at 99.4%"]
]
_, chunks = create_csv(
    "16_Cross_Department_60Day_Rollout_Tracker.csv",
    tracker_headers,
    tracker_rows,
    [{"page_number": 1, "section_title": "Cross-Department Rollout Schedule & Conflict Alert",
      "chunk_text": "CRITICAL SCHEDULE CONFLICT: Task TSK-03 (Finance October Payroll Co-Pay Lock) has due_date 2026-10-20, which depends on TSK-05 (IT SAML SSO Portal Deployment) that does not finish until 2026-10-23. This 3-day mismatch blocks TSK-04 (142 employees with pending parental rider confirmations)."}]
)
register_doc("DOC-016", "16_Cross_Department_60Day_Rollout_Tracker.csv", "CSV", "DEPT-OPS", 1, "USR-MID-HR-003", chunks)

# --- FILE 17 ---
_, chunks = create_docx(
    "17_Transcript_Executive_Committee_Vendor_Switch_Signoff.docx",
    "Meeting Transcript: Executive Committee Insurance Vendor Sign-Off",
    "Date: October 13, 2026 | Attendees: CEO, Arvind Mehta (CFO), Kavita Nair (CHRO) | Clearance: L3 Upper Only",
    [
        {"heading": "00:04:12 - CHRO Kavita Nair on Employee Morale",
         "body": "Kavita Nair (CHRO): 'We switched to NovaShield because LegacyCare delayed 19 cashless claims last quarter. NovaShield gives us a 2-hour cashless SLA, INR 45,000 per eye for cataract, and INR 1 Lakh maternity. If we pass the 14% parental premium hike (INR 38.4 Lakhs) onto employees right before Diwali, we will face severe pushback from Engineering.'"},
        {"heading": "00:11:45 - CFO Arvind Mehta on Budget Options",
         "body": "Arvind Mehta (CFO): 'I agree we shouldn't shock employee payslips. LegacyCare owes us an INR 19.2 Lakh pro-rata refund on the old OPD buffer. If we apply that INR 19.2L refund and match the remaining INR 19.2L from our Q4 Staff Welfare Reserve (Option B), we can keep employee parental deductions completely flat at INR 600 per parent. Let's load the final numbers into the Decision Matrix for formal sign-off.'"}
    ]
)
register_doc("DOC-017", "17_Transcript_Executive_Committee_Vendor_Switch_Signoff.docx", "DOCX", "DEPT-FIN", 3, "USR-UPPER-FIN-001", chunks)

# --- FILE 18 ---
_, chunks = create_docx(
    "18_Transcript_HR_IT_Finance_Weekly_Migration_WarRoom.docx",
    "Meeting Transcript: HR, IT & Finance Weekly Migration War-Room",
    "Date: October 15, 2026 | Attendees: Priya Kulkarni (HR Lead), Rohan Deshmukh (IT Lead), Finance Payroll Team | Clearance: L2-L3",
    [
        {"heading": "00:02:10 - IT Portal Delay Disclosure",
         "body": "Rohan Deshmukh (IT Manager): 'Team, heads up—our security test found a JWT token expiry bug in NovaShield's external SSO portal. Their engineering team is patching it, so external SSO self-service won't go live until October 23.'"},
        {"heading": "00:05:30 - Payroll Cutoff Collision",
         "body": "Payroll Controller (Finance): 'Wait, October 23? Our payroll system locks October salary deductions on October 20! If 142 employees haven't confirmed their parental rider by October 20, the system will either drop their parents or charge the wrong default rate.'"},
        {"heading": "00:08:15 - HR Escalation Summary",
         "body": "Priya Kulkarni (HR Lead): 'We cannot drop 142 families! Plus I have 11 active hospital claims worth INR 14.2 Lakhs stuck in the transition window right now. We need the CFO to approve extending the payroll lock to October 25 and allowing employees to confirm directly through our internal AI workspace.'"}
    ]
)
register_doc("DOC-018", "18_Transcript_HR_IT_Finance_Weekly_Migration_WarRoom.docx", "DOCX", "DEPT-HR", 2, "USR-MID-HR-003", chunks)

# --- FILE 19 ---
_, chunks = create_docx(
    "19_Transcript_All_Hands_TownHall_Employee_QA_Session.docx",
    "Transcript: All-Hands Employee Town Hall Q&A on New Health Policy",
    "Date: October 14, 2026 | Open to All Employees | Clearance: L1-L3",
    [
        {"heading": "Q1: Pune Hospital Network & Parental Cataract Coverage",
         "body": "Employee Question (Engineering, Pune): 'Are Sahyadri Hospital and Ruby Hall Clinic still in the cashless network, and what is the cataract limit for parents?'\nHR Answer: 'Yes! Both Sahyadri Hospital and Ruby Hall Clinic in Pune are preferred cashless partners under NovaShield. Even better, cataract coverage has increased from INR 35,000 to INR 45,000 per eye, and parental co-pay is cut in half from 20% to 10%. Just make sure you re-confirm your parental rider in the portal!'"},
        {"heading": "Q2: Upgrading Sum Insured from INR 5 Lakhs to INR 10 Lakhs",
         "body": "Employee Question (Operations): 'How much gets deducted from my monthly salary if I upgrade my base sum insured from INR 5L to INR 10L?'\nHR Answer: 'The voluntary INR 5 Lakh top-up costs a flat INR 450 per month deducted from your payslip.'"}
    ]
)
register_doc("DOC-019", "19_Transcript_All_Hands_TownHall_Employee_QA_Session.docx", "DOCX", "DEPT-HR", 1, "USR-MID-HR-003", chunks)

# --- FILE 20 ---
_, chunks = create_pdf(
    "20_Department_Delivery_Impact_Report_Q4.pdf",
    "Q4 Operations Report: Productivity Loss from Unassisted Vendor Migration",
    "DOC-20 | OPS-IMPACT-2026",
    "Clearance: Middle & Upper Layers (L2-L3)",
    [
        {"heading": "1. Quantified Productivity Drain Across 500 Employees",
         "body": "During the first 10 days of the health insurance transition, employees across Engineering, Operations, and Finance spent an average of 3.4 hours per person reading 40-page policy PDFs, searching hospital lists, and messaging HR on Slack. Total lost engineering and delivery time: 1,700 person-hours in October alone."},
        {"heading": "2. Impact of Deploying Role-Adaptive AI Workspace",
         "body": "By deploying the Role-Adaptive Enterprise Copilot with Pointed Voice-to-Doc Q&A and automated cross-silo conflict detection, employee query resolution drops from 45 minutes to 12 seconds, recovering 94% of lost productivity."}
    ]
)
register_doc("DOC-020", "20_Department_Delivery_Impact_Report_Q4.pdf", "PDF", "DEPT-OPS", 2, "USR-LOW-OPS-006", chunks)

# --- FILE 21 ---
_, chunks = create_pdf(
    "21_Excluded_Treatments_And_SubLimits_Schedule.pdf",
    "Actuarial Annexure: Sub-Limits, Consumables & Excluded Procedures (2026)",
    "DOC-21 | ACTUARIAL-ANNEX-2026",
    "Clearance: All Employees (L1-L3)",
    [
        {"heading": "Section 1: Covered Sub-Limits Schedule",
         "body": "1. Cataract Surgery: INR 45,000 per eye (up to INR 90,000 bilateral).\n2. Maternity: INR 1,00,000 (Normal or Caesarean).\n3. Lasik / Refractive Eye Surgery: Covered up to INR 30,000 per eye if refractive error exceeds +/- 6.0 diopters.\n4. Robotic & Modern Treatments: Covered up to 50% of Sum Insured.\n5. OPD & Dental Wallet: INR 10,000 per family per year."},
        {"heading": "Section 2: Standard Exclusions",
         "body": "Cosmetic plastic surgery, non-prescribed dietary supplements, and experimental stem-cell procedures remain excluded unless reconstructing post-accident trauma."}
    ]
)
register_doc("DOC-021", "21_Excluded_Treatments_And_SubLimits_Schedule.pdf", "PDF", "DEPT-HR", 1, "USR-MID-HR-003", chunks)

# --- FILE 22 ---
_, chunks = create_pdf(
    "22_TPA_SLA_Breach_And_Grievance_Redressal_Matrix.pdf",
    "NovaShield TPA Escalation Matrix & SLA Penalty Schedule",
    "DOC-22 | TPA-SLA-MATRIX-2026",
    "Clearance: All Employees (L1-L3)",
    [
        {"heading": "1. Three-Tier Grievance Escalation Contacts",
         "body": "- Level 1 (Cashless Pre-Auth Desk - 0 to 120 mins): priority-corp@novashieldhealth.com | +91-1800-102-9920\n- Level 2 (Dedicated Account Nodal Officer - >120 mins): Viktor Sen, VP Corporate Claims | vikram.sen@novashieldhealth.com\n- Level 3 (Internal HR Benefits Lead): Priya Kulkarni | priya.kulkarni@kpipulse.com"},
        {"heading": "2. Penalty Enforcement Clause",
         "body": "If any cashless pre-authorization for an active employee or dependent exceeds 180 minutes without medical query justification, NovaShield credits INR 15,000 to the corporate buffer ledger automatically."}
    ]
)
register_doc("DOC-022", "22_TPA_SLA_Breach_And_Grievance_Redressal_Matrix.pdf", "PDF", "DEPT-LEG", 1, "USR-MID-HR-003", chunks)


# ==============================================================================
# 3. BUILD DECISION MATRIX LOGS FOR UPPER/MIDDLE LAYER
# ==============================================================================

DECISION_LOGS = [
    {
        "decision_id": "DEC-2026-001",
        "triggered_by_doc_id": "DOC-008",
        "approver_user_id": "USR-UPPER-FIN-001",
        "title": "Resolve INR 38.4L Parental Premium Hike & Oct 20 vs Oct 23 Cutoff Conflict",
        "status": "PENDING_EXECUTIVE_APPROVAL",
        "options_json": json.dumps([
            {
                "option_code": "OPTION_A",
                "label": "100% Company Absorption from Operating Margin",
                "net_company_cost_inr": 1920000,
                "employee_monthly_impact_inr": 0,
                "cutoff_resolution": "Extend payroll lock to Oct 25",
                "risk_level": "Medium (Hits Q4 EBITDA by INR 19.2L)"
            },
            {
                "option_code": "OPTION_B_RECOMMENDED",
                "label": "Hybrid Buffer: Apply INR 19.2L LegacyCare Refund + Welfare Reserve & Extend Cutoff to Oct 25",
                "net_company_cost_inr": 0,
                "employee_monthly_impact_inr": 0,
                "cutoff_resolution": "Auto-extend Finance payroll cutoff from Oct 20 to Oct 25; enable 1-click portal opt-in",
                "risk_level": "Low (Zero EBITDA hit, zero employee payslip hike, unblocks 142 families)"
            },
            {
                "option_code": "OPTION_C",
                "label": "100% Pass-Through of 14% Hike to Enrolled Employees",
                "net_company_cost_inr": 0,
                "employee_monthly_impact_inr": 640,
                "cutoff_resolution": "Enforce strict Oct 20 payroll cutoff",
                "risk_level": "High (Sparks employee dissatisfaction & drops 142 unconfirmed parents)"
            }
        ]),
        "selected_option": "PENDING",
        "financial_impact": 3840000.00,
        "eval_grounding_score": 0.992,
        "decided_at": None
    }
]


# ==============================================================================
# 4. GENERATE LOCAL SQLITE RDBMS + PRODUCTION CLOUD SQL POSTGRESQL DDL/SEED
# ==============================================================================

sqlite_path = os.path.join(RDBMS_DIR, "local_enterprise.db")
if os.path.exists(sqlite_path):
    os.remove(sqlite_path)

conn = sqlite3.connect(sqlite_path)
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys = ON;")

# Create 10 Normalized RDBMS Tables
cur.executescript("""
CREATE TABLE org_layers (
    layer_id INTEGER PRIMARY KEY,
    layer_code TEXT NOT NULL UNIQUE,
    layer_name TEXT NOT NULL,
    clearance_level INTEGER NOT NULL
);

CREATE TABLE departments (
    dept_id TEXT PRIMARY KEY,
    dept_name TEXT NOT NULL,
    cost_center_code TEXT NOT NULL
);

CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    dept_id TEXT NOT NULL REFERENCES departments(dept_id),
    layer_id INTEGER NOT NULL REFERENCES org_layers(layer_id),
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    job_title TEXT NOT NULL,
    grade_tier TEXT NOT NULL,
    ui_preferences_json TEXT NOT NULL
);

CREATE TABLE vendors_policies (
    policy_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    policy_number TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    annual_premium REAL NOT NULL,
    tpa_contact TEXT NOT NULL
);

CREATE TABLE employee_enrollments (
    enrollment_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    policy_id TEXT NOT NULL REFERENCES vendors_policies(policy_id),
    sum_insured INTEGER NOT NULL,
    dependents_count INTEGER NOT NULL,
    parental_opt_in TEXT NOT NULL,
    monthly_copay_deduction INTEGER NOT NULL,
    migration_status TEXT NOT NULL
);

CREATE TABLE insurance_claims_escalations (
    claim_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    policy_id TEXT NOT NULL REFERENCES vendors_policies(policy_id),
    hospital_name TEXT NOT NULL,
    city TEXT NOT NULL,
    treatment_type TEXT NOT NULL,
    claim_amount REAL NOT NULL,
    claim_stage TEXT NOT NULL,
    assigned_hr_id TEXT NOT NULL REFERENCES users(user_id),
    blocker_reason TEXT NOT NULL
);

CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    uploaded_by TEXT NOT NULL REFERENCES users(user_id),
    dept_id TEXT NOT NULL REFERENCES departments(dept_id),
    min_layer_clearance INTEGER NOT NULL REFERENCES org_layers(layer_id),
    file_name TEXT NOT NULL UNIQUE,
    file_type TEXT NOT NULL,
    gcs_uri TEXT NOT NULL,
    version TEXT NOT NULL
);

CREATE TABLE document_chunks_vectors (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    page_number INTEGER NOT NULL,
    section_title TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding_json TEXT
);

CREATE TABLE workflow_tasks (
    task_id TEXT PRIMARY KEY,
    dept_id TEXT NOT NULL REFERENCES departments(dept_id),
    assigned_to_user_id TEXT NOT NULL REFERENCES users(user_id),
    layer_id INTEGER NOT NULL REFERENCES org_layers(layer_id),
    title TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL,
    dependency_task_id TEXT,
    blocker_note TEXT
);

CREATE TABLE decision_matrix_logs (
    decision_id TEXT PRIMARY KEY,
    triggered_by_doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    approver_user_id TEXT NOT NULL REFERENCES users(user_id),
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    options_json TEXT NOT NULL,
    selected_option TEXT NOT NULL,
    financial_impact REAL NOT NULL,
    eval_grounding_score REAL NOT NULL,
    decided_at TEXT
);
""")

# Populate Tables
for l in ORG_LAYERS:
    cur.execute("INSERT INTO org_layers VALUES (?, ?, ?, ?)", (l["layer_id"], l["layer_code"], l["layer_name"], l["clearance_level"]))

for d in DEPARTMENTS:
    cur.execute("INSERT INTO departments VALUES (?, ?, ?)", (d["dept_id"], d["dept_name"], d["cost_center_code"]))

for u in ALL_USERS:
    cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (u["user_id"], u["dept_id"], u["layer_id"], u["email"], u["full_name"], u["job_title"], u["grade_tier"], u["ui_preferences_json"]))

for p in VENDORS_POLICIES:
    cur.execute("INSERT INTO vendors_policies VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (p["policy_id"], p["vendor_name"], p["policy_number"], p["status"], p["effective_date"], p["expiry_date"], p["annual_premium"], p["tpa_contact"]))

for row in census_rows:
    # row: [enrollment_id, user_id, full_name, dept_id, layer_id, policy_id, sum_insured_inr, dependents_count, parental_opt_in_status, monthly_copay_inr, migration_status]
    cur.execute("INSERT INTO employee_enrollments VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (row[0], row[1], row[5], row[6], row[7], row[8], row[9], row[10]))

for c_row in claims_rows:
    # c_row: [claim_id, user_id, employee_name, department, hospital_name, city, treatment_type, claim_amount_inr, claim_stage, blocker_reason]
    cur.execute("INSERT INTO insurance_claims_escalations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (c_row[0], c_row[1], "POL-NOVASHIELD-2026", c_row[4], c_row[5], c_row[6], c_row[7], c_row[8], "USR-MID-HR-003", c_row[9]))

for doc in DOCUMENTS_REGISTRY:
    cur.execute("INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (doc["doc_id"], doc["uploaded_by"], doc["dept_id"], doc["min_layer_clearance"], doc["file_name"], doc["file_type"], doc["gcs_uri"], doc["version"]))

for chk in ALL_DOCUMENT_CHUNKS:
    cur.execute("INSERT INTO document_chunks_vectors VALUES (?, ?, ?, ?, ?, ?)",
                (chk["chunk_id"], chk["doc_id"], chk["page_number"], chk["section_title"], chk["chunk_text"], "[]"))

for t_row in tracker_rows:
    cur.execute("INSERT INTO workflow_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (t_row[0], t_row[1], t_row[2], t_row[3], t_row[4], t_row[5], t_row[6], t_row[7], t_row[8]))

for dec in DECISION_LOGS:
    cur.execute("INSERT INTO decision_matrix_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (dec["decision_id"], dec["triggered_by_doc_id"], dec["approver_user_id"], dec["title"], dec["status"],
                 dec["options_json"], dec["selected_option"], dec["financial_impact"], dec["eval_grounding_score"], dec["decided_at"]))

conn.commit()
conn.close()

# Generate Production Google Cloud SQL for PostgreSQL (with pgvector + RLS) Script
postgres_sql_path = os.path.join(RDBMS_DIR, "cloud_sql_postgres_schema_and_rls.sql")
with open(postgres_sql_path, "w", encoding="utf-8") as pg_file:
    pg_file.write("""-- ============================================================================
-- GOOGLE CLOUD SQL FOR POSTGRESQL / ALLOYDB PRODUCTION SCHEMA
-- Includes pgvector extension & Enterprise Row-Level Security (RLS)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS google_ml_integration;

CREATE TABLE org_layers (
    layer_id INT PRIMARY KEY,
    layer_code VARCHAR(16) NOT NULL UNIQUE,
    layer_name VARCHAR(100) NOT NULL,
    clearance_level INT NOT NULL
);

CREATE TABLE departments (
    dept_id VARCHAR(32) PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    cost_center_code VARCHAR(32) NOT NULL
);

CREATE TABLE users (
    user_id VARCHAR(64) PRIMARY KEY,
    dept_id VARCHAR(32) NOT NULL REFERENCES departments(dept_id),
    layer_id INT NOT NULL REFERENCES org_layers(layer_id),
    email VARCHAR(150) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    job_title VARCHAR(120) NOT NULL,
    grade_tier VARCHAR(16) NOT NULL,
    ui_preferences_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE vendors_policies (
    policy_id VARCHAR(64) PRIMARY KEY,
    vendor_name VARCHAR(150) NOT NULL,
    policy_number VARCHAR(64) NOT NULL UNIQUE,
    status VARCHAR(32) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    annual_premium NUMERIC(14, 2) NOT NULL,
    tpa_contact VARCHAR(150) NOT NULL
);

CREATE TABLE employee_enrollments (
    enrollment_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    policy_id VARCHAR(64) NOT NULL REFERENCES vendors_policies(policy_id),
    sum_insured INT NOT NULL,
    dependents_count INT NOT NULL,
    parental_opt_in VARCHAR(64) NOT NULL,
    monthly_copay_deduction INT NOT NULL,
    migration_status VARCHAR(64) NOT NULL
);

CREATE TABLE insurance_claims_escalations (
    claim_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    policy_id VARCHAR(64) NOT NULL REFERENCES vendors_policies(policy_id),
    hospital_name VARCHAR(150) NOT NULL,
    city VARCHAR(64) NOT NULL,
    treatment_type VARCHAR(150) NOT NULL,
    claim_amount NUMERIC(12, 2) NOT NULL,
    claim_stage VARCHAR(64) NOT NULL,
    assigned_hr_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    blocker_reason TEXT NOT NULL
);

CREATE TABLE documents (
    doc_id VARCHAR(64) PRIMARY KEY,
    uploaded_by VARCHAR(64) NOT NULL REFERENCES users(user_id),
    dept_id VARCHAR(32) NOT NULL REFERENCES departments(dept_id),
    min_layer_clearance INT NOT NULL REFERENCES org_layers(layer_id),
    file_name VARCHAR(255) NOT NULL UNIQUE,
    file_type VARCHAR(16) NOT NULL,
    gcs_uri TEXT NOT NULL,
    version VARCHAR(32) NOT NULL
);

CREATE TABLE document_chunks_vectors (
    chunk_id VARCHAR(64) PRIMARY KEY,
    doc_id VARCHAR(64) NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    section_title VARCHAR(255) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768) -- Vertex AI text-embedding-004 dimension
);

CREATE INDEX idx_doc_chunks_hnsw ON document_chunks_vectors USING hnsw (embedding vector_cosine_ops);

CREATE TABLE workflow_tasks (
    task_id VARCHAR(64) PRIMARY KEY,
    dept_id VARCHAR(32) NOT NULL REFERENCES departments(dept_id),
    assigned_to_user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    layer_id INT NOT NULL REFERENCES org_layers(layer_id),
    title VARCHAR(255) NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(64) NOT NULL,
    dependency_task_id VARCHAR(64),
    blocker_note TEXT
);

CREATE TABLE decision_matrix_logs (
    decision_id VARCHAR(64) PRIMARY KEY,
    triggered_by_doc_id VARCHAR(64) NOT NULL REFERENCES documents(doc_id),
    approver_user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    title VARCHAR(255) NOT NULL,
    status VARCHAR(64) NOT NULL,
    options_json JSONB NOT NULL,
    selected_option VARCHAR(64) NOT NULL,
    financial_impact NUMERIC(14, 2) NOT NULL,
    eval_grounding_score NUMERIC(5, 4) NOT NULL,
    decided_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- ENTERPRISE ZERO-TRUST ROW-LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE decision_matrix_logs ENABLE ROW LEVEL SECURITY;

-- 1. Documents RLS: Users can only read documents at or below their layer clearance
CREATE POLICY documents_layer_clearance_policy ON documents
    FOR SELECT
    USING (min_layer_clearance <= current_setting('app.current_clearance', true)::int);

-- 2. Enrollments RLS: Lower layer sees only their own family record; HR/Upper sees all
CREATE POLICY enrollments_privacy_policy ON employee_enrollments
    FOR SELECT
    USING (
        user_id = current_setting('app.current_user_id', true)
        OR current_setting('app.current_dept_id', true) = 'DEPT-HR'
        OR current_setting('app.current_clearance', true)::int >= 3
    );

-- 3. Executive Decisions RLS: Only Upper Layer (Clearance 3) can view or approve C-Suite Decision Matrix
CREATE POLICY executive_decisions_rls_policy ON decision_matrix_logs
    FOR ALL
    USING (current_setting('app.current_clearance', true)::int >= 3);
""")

# Also export the chunk manifest as JSON for fast Vertex AI Vector Search / Embedding indexing
manifest_path = os.path.join(RDBMS_DIR, "chunks_seed_manifest.json")
with open(manifest_path, "w", encoding="utf-8") as mf:
    json.dump({
        "documents": DOCUMENTS_REGISTRY,
        "chunks": ALL_DOCUMENT_CHUNKS,
        "showcase_users": SHOWCASE_USERS
    }, mf, indent=2)

print(f"\nSUCCESS! Enterprise Data Vault generated at: {BASE_DIR}")
print(f" - 22 Realistic Files (.pdf, .csv, .docx) created in: {FILES_DIR}")
print(f" - Local 10-Table RDBMS populated (500 employees, 22 docs, 12 claims): {sqlite_path}")
print(f" - Cloud SQL PostgreSQL + pgvector + RLS DDL script ready: {postgres_sql_path}")
print(f" - Vector RAG Chunks Manifest exported: {manifest_path}")