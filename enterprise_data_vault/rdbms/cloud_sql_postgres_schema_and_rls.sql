-- ============================================================================
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
