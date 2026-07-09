-- RWR-RTO Seed Data
-- Demo Org Hierarchy:
--
--   CEO001  (C_LEVEL)
--     └── SVP001  (SVP)
--           └── VP001  (VP)
--                 └── DIR001  (DIRECTOR)   ← has app access
--                       └── SM001  (SM)    ← can approve
--                             ├── MGR001  (MANAGER)
--                             │     ├── EMP001  (ASSOCIATE)
--                             │     ├── EMP002  (ASSOCIATE)
--                             │     └── EMP003  (ANALYST)
--                             └── MGR002  (MANAGER)
--                                   └── EMP004  (ASSOCIATE)

INSERT OR IGNORE INTO employees (employee_id, name, email, level, manager_id, department, country) VALUES
('CEO001', 'Alice Thompson',   'alice.thompson@company.com',   'C_LEVEL',   NULL,    'Executive',   'USA'),
('SVP001', 'Bob Williams',     'bob.williams@company.com',     'SVP',       'CEO001','Operations',  'USA'),
('VP001',  'Carol Martinez',   'carol.martinez@company.com',   'VP',        'SVP001','Technology',  'USA'),
('DIR001', 'David Johnson',    'david.johnson@company.com',    'DIRECTOR',  'VP001', 'Engineering', 'USA'),
('SM001',  'Emma Davis',       'emma.davis@company.com',       'SM',        'DIR001','Engineering', 'USA'),
('MGR001', 'Frank Wilson',     'frank.wilson@company.com',     'MANAGER',   'SM001', 'Engineering', 'USA'),
('MGR002', 'Grace Lee',        'grace.lee@company.com',        'MANAGER',   'SM001', 'Engineering', 'USA'),
('EMP001', 'Henry Brown',      'henry.brown@company.com',      'ASSOCIATE', 'MGR001','Engineering', 'USA'),
('EMP002', 'Isabella Garcia',  'isabella.garcia@company.com',  'ASSOCIATE', 'MGR001','Engineering', 'USA'),
('EMP003', 'James Miller',     'james.miller@company.com',     'ANALYST',   'MGR001','Engineering', 'USA'),
('EMP004', 'Karen Taylor',     'karen.taylor@company.com',     'ASSOCIATE', 'MGR002','Engineering', 'USA');

-- USA Federal Holidays 2025
INSERT OR IGNORE INTO usa_holidays (holiday_id, holiday_date, name, year) VALUES
('HOL2025-01', '2025-01-01', 'New Year''s Day',                              2025),
('HOL2025-02', '2025-01-20', 'Martin Luther King Jr. Day',                   2025),
('HOL2025-03', '2025-02-17', 'Presidents'' Day',                             2025),
('HOL2025-04', '2025-05-26', 'Memorial Day',                                 2025),
('HOL2025-05', '2025-06-19', 'Juneteenth National Independence Day',         2025),
('HOL2025-06', '2025-07-04', 'Independence Day',                             2025),
('HOL2025-07', '2025-09-01', 'Labor Day',                                    2025),
('HOL2025-08', '2025-10-13', 'Columbus Day',                                 2025),
('HOL2025-09', '2025-11-11', 'Veterans Day',                                 2025),
('HOL2025-10', '2025-11-27', 'Thanksgiving Day',                             2025),
('HOL2025-11', '2025-12-25', 'Christmas Day',                                2025);

-- USA Federal Holidays 2026
INSERT OR IGNORE INTO usa_holidays (holiday_id, holiday_date, name, year) VALUES
('HOL2026-01', '2026-01-01', 'New Year''s Day',                              2026),
('HOL2026-02', '2026-01-19', 'Martin Luther King Jr. Day',                   2026),
('HOL2026-03', '2026-02-16', 'Presidents'' Day',                             2026),
('HOL2026-04', '2026-05-25', 'Memorial Day',                                 2026),
('HOL2026-05', '2026-06-19', 'Juneteenth National Independence Day',         2026),
('HOL2026-06', '2026-07-03', 'Independence Day (observed)',                  2026),
('HOL2026-07', '2026-09-07', 'Labor Day',                                    2026),
('HOL2026-08', '2026-10-12', 'Columbus Day',                                 2026),
('HOL2026-09', '2026-11-11', 'Veterans Day',                                 2026),
('HOL2026-10', '2026-11-26', 'Thanksgiving Day',                             2026),
('HOL2026-11', '2026-12-25', 'Christmas Day',                                2026);

-- USA Federal Holidays 2027
INSERT OR IGNORE INTO usa_holidays (holiday_id, holiday_date, name, year) VALUES
('HOL2027-01', '2027-01-01', 'New Year''s Day',                              2027),
('HOL2027-02', '2027-01-18', 'Martin Luther King Jr. Day',                   2027),
('HOL2027-03', '2027-02-15', 'Presidents'' Day',                             2027),
('HOL2027-04', '2027-05-31', 'Memorial Day',                                 2027),
('HOL2027-05', '2027-06-18', 'Juneteenth National Independence Day (observed)', 2027),
('HOL2027-06', '2027-07-05', 'Independence Day (observed)',                  2027),
('HOL2027-07', '2027-09-06', 'Labor Day',                                    2027),
('HOL2027-08', '2027-10-11', 'Columbus Day',                                 2027),
('HOL2027-09', '2027-11-11', 'Veterans Day',                                 2027),
('HOL2027-10', '2027-11-25', 'Thanksgiving Day',                             2027),
('HOL2027-11', '2027-12-24', 'Christmas Day (observed)',                     2027);
