"""
StrataIQ SQLAlchemy ORM Models — 10-Table Enterprise Schema
Mapped exactly to local_enterprise.db column names (SQLite-compatible).
Note: document_chunks_vectors uses 'embedding_json' TEXT (not pgvector) in SQLite.
"""
from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class OrgLayer(Base):
    __tablename__ = "org_layers"

    layer_id = Column(Integer, primary_key=True)
    layer_code = Column(String(16), nullable=False, unique=True)
    layer_name = Column(String(100), nullable=False)
    clearance_level = Column(Integer, nullable=False)

    # Relationships
    users = relationship("User", back_populates="org_layer")
    workflow_tasks = relationship("WorkflowTask", back_populates="org_layer")


class Department(Base):
    __tablename__ = "departments"

    dept_id = Column(String(32), primary_key=True)
    dept_name = Column(String(100), nullable=False)
    cost_center_code = Column(String(32), nullable=False)

    # Relationships
    users = relationship("User", back_populates="department")
    documents = relationship("Document", back_populates="department")
    workflow_tasks = relationship("WorkflowTask", back_populates="department")


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True)
    dept_id = Column(String(32), ForeignKey("departments.dept_id"), nullable=False)
    layer_id = Column(Integer, ForeignKey("org_layers.layer_id"), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    full_name = Column(String(120), nullable=False)
    job_title = Column(String(120), nullable=False)
    grade_tier = Column(String(16), nullable=False)
    ui_preferences_json = Column(Text, nullable=False, default="{}")

    # Relationships
    department = relationship("Department", back_populates="users")
    org_layer = relationship("OrgLayer", back_populates="users")
    enrollments = relationship("EmployeeEnrollment", back_populates="user",
                               foreign_keys="EmployeeEnrollment.user_id")
    claims_as_employee = relationship("InsuranceClaim", back_populates="employee",
                                      foreign_keys="InsuranceClaim.user_id")
    claims_as_hr = relationship("InsuranceClaim", back_populates="assigned_hr",
                                foreign_keys="InsuranceClaim.assigned_hr_id")
    uploaded_documents = relationship("Document", back_populates="uploader")
    assigned_tasks = relationship("WorkflowTask", back_populates="assigned_user")
    decisions_to_approve = relationship("DecisionMatrixLog", back_populates="approver")


class VendorPolicy(Base):
    __tablename__ = "vendors_policies"

    policy_id = Column(String(64), primary_key=True)
    vendor_name = Column(String(150), nullable=False)
    policy_number = Column(String(64), nullable=False, unique=True)
    status = Column(String(32), nullable=False)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    annual_premium = Column(Numeric(14, 2), nullable=False)
    tpa_contact = Column(String(150), nullable=False)

    # Relationships
    enrollments = relationship("EmployeeEnrollment", back_populates="policy")
    claims = relationship("InsuranceClaim", back_populates="policy")


class EmployeeEnrollment(Base):
    __tablename__ = "employee_enrollments"

    enrollment_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    policy_id = Column(String(64), ForeignKey("vendors_policies.policy_id"), nullable=False)
    sum_insured = Column(Integer, nullable=False)
    dependents_count = Column(Integer, nullable=False)
    parental_opt_in = Column(String(64), nullable=False)
    monthly_copay_deduction = Column(Integer, nullable=False)
    migration_status = Column(String(64), nullable=False)

    # Relationships
    user = relationship("User", back_populates="enrollments", foreign_keys=[user_id])
    policy = relationship("VendorPolicy", back_populates="enrollments")


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims_escalations"

    claim_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    policy_id = Column(String(64), ForeignKey("vendors_policies.policy_id"), nullable=False)
    hospital_name = Column(String(150), nullable=False)
    city = Column(String(64), nullable=False)
    treatment_type = Column(String(150), nullable=False)
    claim_amount = Column(Numeric(12, 2), nullable=False)
    claim_stage = Column(String(64), nullable=False)
    assigned_hr_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    blocker_reason = Column(Text, nullable=False)

    # Relationships
    employee = relationship("User", back_populates="claims_as_employee", foreign_keys=[user_id])
    assigned_hr = relationship("User", back_populates="claims_as_hr", foreign_keys=[assigned_hr_id])
    policy = relationship("VendorPolicy", back_populates="claims")


class Document(Base):
    __tablename__ = "documents"

    doc_id = Column(String(64), primary_key=True)
    uploaded_by = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    dept_id = Column(String(32), ForeignKey("departments.dept_id"), nullable=False)
    min_layer_clearance = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=False, unique=True)
    file_type = Column(String(16), nullable=False)
    gcs_uri = Column(Text, nullable=False)
    version = Column(String(32), nullable=False)

    # Relationships
    uploader = relationship("User", back_populates="uploaded_documents")
    department = relationship("Department", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document",
                          cascade="all, delete-orphan")
    decision_logs = relationship("DecisionMatrixLog", back_populates="triggered_by_doc")


class DocumentChunk(Base):
    __tablename__ = "document_chunks_vectors"

    chunk_id = Column(String(64), primary_key=True)
    doc_id = Column(String(64), ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    section_title = Column(String(255), nullable=False)
    chunk_text = Column(Text, nullable=False)
    # SQLite stores this as a JSON TEXT field (empty list "[]" — embeddings generated in Phase 2)
    embedding_json = Column(Text, nullable=False, default="[]")

    # Relationships
    document = relationship("Document", back_populates="chunks")


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"

    task_id = Column(String(64), primary_key=True)
    dept_id = Column(String(32), ForeignKey("departments.dept_id"), nullable=False)
    assigned_to_user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    layer_id = Column(Integer, ForeignKey("org_layers.layer_id"), nullable=False)
    title = Column(String(255), nullable=False)
    due_date = Column(String(20), nullable=False)   # stored as text YYYY-MM-DD in SQLite
    status = Column(String(64), nullable=False)
    dependency_task_id = Column(String(64), nullable=True)
    blocker_note = Column(Text, nullable=True)

    # Relationships
    department = relationship("Department", back_populates="workflow_tasks")
    assigned_user = relationship("User", back_populates="assigned_tasks")
    org_layer = relationship("OrgLayer", back_populates="workflow_tasks")


class DecisionMatrixLog(Base):
    __tablename__ = "decision_matrix_logs"

    decision_id = Column(String(64), primary_key=True)
    triggered_by_doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False)
    approver_user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(64), nullable=False)
    options_json = Column(Text, nullable=False)          # JSON string in SQLite
    selected_option = Column(String(64), nullable=False)
    financial_impact = Column(Numeric(14, 2), nullable=False)
    eval_grounding_score = Column(Numeric(5, 4), nullable=False)
    decided_at = Column(DateTime, nullable=True)

    # Relationships
    triggered_by_doc = relationship("Document", back_populates="decision_logs")
    approver = relationship("User", back_populates="decisions_to_approve")
