-- ============================================================
-- Table: office_holidays
-- Stores Cognizant office holidays (India + Americas)
-- with office address details per location
-- ============================================================
CREATE TABLE IF NOT EXISTS office_holidays (
    id                INTEGER PRIMARY KEY,
    location_code     TEXT    NOT NULL,
    country           TEXT    NOT NULL,
    region            TEXT,                -- e.g. India, Americas
    holiday_date      TEXT    NOT NULL,    -- YYYY-MM-DD
    holiday_name      TEXT    NOT NULL,
    is_active         INTEGER NOT NULL DEFAULT 1,  -- 1=TRUE, 0=FALSE
    office_name       TEXT,
    office_address    TEXT,
    city              TEXT,
    state_province    TEXT
);

CREATE INDEX IF NOT EXISTS idx_holidays_date     ON office_holidays(holiday_date);
CREATE INDEX IF NOT EXISTS idx_holidays_location ON office_holidays(location_code);
