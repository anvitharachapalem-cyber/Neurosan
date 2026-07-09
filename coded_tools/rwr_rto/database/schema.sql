-- RWR-RTO Database Schema
-- Remote Work Requester - Return To Office

CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL,
    level       TEXT NOT NULL,   -- C_LEVEL, SVP, EVP, VP, DIRECTOR, SM, MANAGER, ASSOCIATE, ANALYST
    manager_id  TEXT,
    department  TEXT,
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS wfh_requests (
    request_id              TEXT PRIMARY KEY,
    employee_id             TEXT NOT NULL,
    requester_id            TEXT NOT NULL,   -- may differ if raised on behalf of
    category                TEXT NOT NULL,   -- MEDICAL_SELF | DEPENDENT_CARE | LOCALIZED_EXIGENCY | OFFICE_TRAVEL | MATERNITY_RETURNEE | EXTRAORDINARY
    days_requested          INTEGER NOT NULL,
    start_date              TEXT NOT NULL,
    end_date                TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING | APPROVED | REJECTED | AUTO_REJECTED | ESCALATED | SEEKING_CLARIFICATION
    rejection_reason        TEXT,            -- MANAGER_REJECTED
    auto_reject_reason      TEXT,            -- MANAGER_INACTION | SKIP_LEVEL_INACTION | ASSOCIATE_NO_CLARIFICATION
    can_resubmit            INTEGER DEFAULT 0,
    approver_id             TEXT,
    skip_level_manager_id   TEXT,
    escalated_at            TEXT,
    notes                   TEXT,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    request_id  TEXT NOT NULL,
    approver_id TEXT NOT NULL,
    action      TEXT NOT NULL,   -- APPROVED | REJECTED | SEEK_CLARIFICATION | ESCALATED
    action_date TEXT,
    comments    TEXT,
    deadline    TEXT,
    FOREIGN KEY (request_id) REFERENCES wfh_requests(request_id)
);

CREATE TABLE IF NOT EXISTS clarifications (
    clarification_id TEXT PRIMARY KEY,
    request_id       TEXT NOT NULL,
    approver_id      TEXT NOT NULL,
    question         TEXT NOT NULL,
    required_docs    TEXT,
    response         TEXT,
    responded_at     TEXT,
    due_date         TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'PENDING',   -- PENDING | RESPONDED | EXPIRED
    FOREIGN KEY (request_id) REFERENCES wfh_requests(request_id)
);

CREATE TABLE IF NOT EXISTS days_balance (
    balance_id   TEXT PRIMARY KEY,
    employee_id  TEXT NOT NULL,
    category     TEXT NOT NULL,
    days_used    INTEGER DEFAULT 0,
    days_limit   INTEGER NOT NULL,
    is_unlimited INTEGER DEFAULT 0,
    fiscal_year  INTEGER NOT NULL,
    UNIQUE (employee_id, category, fiscal_year),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
