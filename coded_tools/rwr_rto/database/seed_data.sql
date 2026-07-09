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

INSERT OR IGNORE INTO employees (employee_id, name, email, level, manager_id, department) VALUES
('CEO001', 'Alice Thompson',   'alice.thompson@company.com',   'C_LEVEL',   NULL,    'Executive'),
('SVP001', 'Bob Williams',     'bob.williams@company.com',     'SVP',       'CEO001','Operations'),
('VP001',  'Carol Martinez',   'carol.martinez@company.com',   'VP',        'SVP001','Technology'),
('DIR001', 'David Johnson',    'david.johnson@company.com',    'DIRECTOR',  'VP001', 'Engineering'),
('SM001',  'Emma Davis',       'emma.davis@company.com',       'SM',        'DIR001','Engineering'),
('MGR001', 'Frank Wilson',     'frank.wilson@company.com',     'MANAGER',   'SM001', 'Engineering'),
('MGR002', 'Grace Lee',        'grace.lee@company.com',        'MANAGER',   'SM001', 'Engineering'),
('EMP001', 'Henry Brown',      'henry.brown@company.com',      'ASSOCIATE', 'MGR001','Engineering'),
('EMP002', 'Isabella Garcia',  'isabella.garcia@company.com',  'ASSOCIATE', 'MGR001','Engineering'),
('EMP003', 'James Miller',     'james.miller@company.com',     'ANALYST',   'MGR001','Engineering'),
('EMP004', 'Karen Taylor',     'karen.taylor@company.com',     'ASSOCIATE', 'MGR002','Engineering');
