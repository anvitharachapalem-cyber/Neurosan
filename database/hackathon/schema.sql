CREATE TABLE IF NOT EXISTS associates (
    associate_id                  INTEGER PRIMARY KEY,
    associate_name                TEXT    NOT NULL,
    account                       TEXT,
    supervisor_name               TEXT,
    supervisor_id                 INTEGER,
    project_id                    INTEGER,
    level                         TEXT,
    country                       TEXT,
    city                          TEXT,
    office_name                   TEXT,
    odc_seats                     TEXT,
    non_odc_seats                 INTEGER,
    total_seats                   INTEGER,
    work_model                    TEXT,
    cog_work_model                TEXT,
    required_office_days_per_week INTEGER,
    jan_working_days              INTEGER,
    feb_working_days              INTEGER,
    days_in_month                 INTEGER,
    week1_work_days               INTEGER,
    week1_office_days             INTEGER,
    week1_status                  TEXT,
    week2_work_days               INTEGER,
    week2_office_days             INTEGER,
    week2_status                  TEXT,
    week3_work_days               INTEGER,
    week3_office_days             INTEGER,
    week3_status                  TEXT,
    week4_work_days               INTEGER,
    week4_office_days             INTEGER,
    week4_status                  TEXT,
    week5_work_days               INTEGER,
    week5_office_days             INTEGER,
    week5_status                  TEXT,
    expected_office_days          INTEGER,
    total_office_days             INTEGER,
    compliant_status              TEXT,
    compliance_score              REAL
);

-- ============================================================
-- Table 3: policy_documents
-- Source: PDF policy documents (extracted text per page)
-- ============================================================
CREATE TABLE IF NOT EXISTS policy_documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_name   TEXT NOT NULL,
    page_number     INTEGER NOT NULL,
    page_text       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_policy_doc ON policy_documents(document_name);

CREATE TABLE IF NOT EXISTS attendance (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    associate_name    TEXT,
    associate_id      INTEGER,
    account           TEXT,
    supervisor_name   TEXT,
    supervisor_id     INTEGER,
    project_id        INTEGER,
    project_name      TEXT,
    date              TEXT,
    checkin           TEXT,
    checkout          TEXT,
    duration_hours    REAL,
    remarks           TEXT,
    reason            TEXT,
    month_label       TEXT,
    compliance_pct    REAL,
    cog_work_model    TEXT,
    FOREIGN KEY (associate_id) REFERENCES associates(associate_id)
);
