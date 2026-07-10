-- ============================================================
-- Table 1: associates
-- Source: "Associate Details" sheet
-- ============================================================
CREATE TABLE IF NOT EXISTS associates (
    associate_id            INTEGER PRIMARY KEY,
    associate_name          TEXT    NOT NULL,
    account                 TEXT,
    supervisor_name         TEXT,
    supervisor_id           INTEGER,
    project_id              INTEGER,
    level                   TEXT,
    country                 TEXT,
    city                    TEXT,
    office_name             TEXT,
    odc_seats               TEXT,
    non_odc_seats           INTEGER,
    total_seats             INTEGER,
    work_model              TEXT,
    required_office_days_per_week INTEGER,
    jan_working_days        INTEGER,
    feb_working_days        INTEGER,
    days_in_month           INTEGER,
    week1_work_days         INTEGER,
    week1_office_days       INTEGER,
    week1_status            TEXT,
    week2_work_days         INTEGER,
    week2_office_days       INTEGER,
    week2_status            TEXT,
    week3_work_days         INTEGER,
    week3_office_days       INTEGER,
    week3_status            TEXT,
    week4_work_days         INTEGER,
    week4_office_days       INTEGER,
    week4_status            TEXT,
    week5_work_days         INTEGER,
    week5_office_days       INTEGER,
    week5_status            TEXT,
    expected_office_days    INTEGER,
    total_office_days       INTEGER,
    compliant_status        TEXT,
    compliance_score        REAL
);

-- ============================================================
-- Table 2: attendance
-- Source: "Sheet1" (daily check-in / check-out records)
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    associate_name      TEXT,
    associate_id        INTEGER,
    account             TEXT,
    supervisor_name     TEXT,
    supervisor_id       INTEGER,
    project_id          INTEGER,
    project_name        TEXT,
    date                TEXT,       -- stored as YYYY-MM-DD
    checkin             TEXT,       -- stored as HH:MM:SS
    checkout            TEXT,       -- stored as HH:MM:SS
    duration_hours      REAL,
    remarks             TEXT,       -- Full Day / Half Day / Early Departure
    reason              TEXT,
    months_feb          INTEGER,
    compliance_pct      REAL,
    FOREIGN KEY (associate_id) REFERENCES associates(associate_id)
);
