# Cognizant Associate Hub — Architecture

## Overview

```
User (Browser / CLI)
        │
        ▼
   nsflow UI (port 4173)
        │  WebSocket / HTTP
        ▼
 Neuro-SAN Server (port 8080)
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │              faq_agent  (Front Man)           │
 │  - Classifies: PERSONAL vs GENERIC query     │
 │  - Routes to correct tool or sub-agent       │
 └──────┬───────────────────────────────────────┘
        │
   ┌────┴──────────────────────────────────────────────────────┐
   │                                                           │
   ▼                                                           ▼
CODED TOOLS (DB)                                    LLM KNOWLEDGE AGENTS
──────────────────                                  ────────────────────────
associate_lookup ──► associates table               it_support_agent
holiday_lookup   ──► office_holidays table          goperform_agent
policy_search    ──► policy_documents table         transport_agent
compliance_check ──► attendance + associates        mediassist_agent
                                                    talent_marketplace_agent
        │
        ▼
 SQLite Database
 (hackathon.db)
 ┌────────────────────┐
 │ associates (50)    │
 │ attendance (4,213) │
 │ office_holidays    │
 │   (267)            │
 │ policy_documents   │
 │   (102 pages)      │
 └────────────────────┘
```

---

## Component Details

### 1. faq_agent (Entry Point / Router)
- **Type:** LLM Agent (GPT-4o-mini) with tool access
- **Role:** Classifies every query, collects Associate ID only when needed, routes to correct tool or sub-agent
- **Config:** `registries/hackathon/associate_hub.hocon`

**Query Classification Logic:**

```
Query received
    │
    ├── PERSONAL? (compliance / profile / supervisor / work model)
    │       └── Ask for Associate ID if not provided
    │           └── Call associate_lookup → greet with profile
    │               └── Then call compliance_check if RTO query
    │
    └── GENERIC?
            ├── Holidays / Office address   → holiday_lookup (coded tool)
            ├── HR Policy                  → policy_search (coded tool)
            ├── IT Support                 → it_support_agent
            ├── GoPerform                  → goperform_agent
            ├── Transport / Cab            → transport_agent
            ├── MediBuddy / Insurance      → mediassist_agent
            ├── Talent Marketplace         → talent_marketplace_agent
            └── Workplace / Desk / Access  → answer from faq_agent knowledge
```

---

### 2. Coded Tools (DB-backed)

#### associate_lookup_tool.py
- **Input:** `associate_id` (int)
- **DB Table:** `associates`
- **Returns:** `associate_name`, `level`, `cog_work_model`, `account`, `city`, `country`, `supervisor_name`, `office_name`

#### holiday_lookup_tool.py
- **Input:** `location` (city name) or `associate_id`
- **DB Table:** `office_holidays`
- **Returns:** Full holiday list + office name + full address for the location
- **Logic:** Fetches location-specific + national (ALL) holidays, merges and deduplicates

#### policy_search_tool.py
- **Input:** `query` (string)
- **DB Table:** `policy_documents`
- **Returns:** Top 5 matching pages with `document_name`, `page_number`, `excerpt`, `citation`
- **Logic:** Keyword scoring across all 102 pages, ranked by relevance

#### compliance_tool.py
- **Input:** `associate_id` (int), `month` (string)
- **DB Tables:** `associates`, `attendance`
- **Returns:** Attendance %, required %, compliance status, days attended, total business days
- **Logic:** Threshold varies by `cog_work_model` and grade group (Senior vs Junior)

```
Compliance Thresholds:
─────────────────────────────────────────────────────
Work Model               Senior (D+)   Junior (AD and below)
─────────────────────────────────────────────────────
Cog hybrid 2/3 days      80%           70%
Cog office based 4/5 days 85%          80%
Cog remote 0/1 days       5%            0%
Cog CLT RMT              100%          95%
─────────────────────────────────────────────────────
```

---

### 3. LLM Knowledge Agents

Each agent is a GPT-4o-mini instance with embedded Q&A knowledge:

| Agent | Topics Covered | Contact / Portal |
|---|---|---|
| `it_support_agent` | GSD tickets, ServiceNow, software requests, admin rights, accessories | ServiceNow via OneCognizant |
| `goperform_agent` | Goal setting, KPIs, ratings, PIP, mid-year review, TMP eligibility | AskHR, HR Business Partner |
| `transport_agent` | Cab scheduling, missed cabs, tracking, reimbursement, MoveInSync | ACT helpline: 1800-258-2345 |
| `mediassist_agent` | MediBuddy registration, claims, cashless hospitalisation, Onam health check | MediAssist: 1800-425-9449 |
| `talent_marketplace_agent` | TMP access, role applications, manager confirmation, project-end feedback | OneCognizant TMP portal |

---

### 4. Database Schema

```sql
-- Associate profiles
CREATE TABLE associates (
    associate_id INTEGER PRIMARY KEY,
    associate_name TEXT,
    account TEXT,
    supervisor_name TEXT,
    level TEXT,               -- PA, A, SA, M, SM, AD, D, AVP, VP, SVP
    country TEXT,
    city TEXT,
    office_name TEXT,
    cog_work_model TEXT,      -- "Cog hybrid 2/3 days", "Cog office based 4/5 days", etc.
    compliant_status TEXT,
    compliance_score REAL
);

-- Daily attendance records
CREATE TABLE attendance (
    associate_id INTEGER,
    date TEXT,                -- YYYY-MM-DD
    month_label TEXT,         -- "Jan", "Feb", etc.
    cog_work_model TEXT,
    compliance_pct REAL
);

-- Office holidays per location
CREATE TABLE office_holidays (
    location_code TEXT,       -- "Bangalore", "ALL", "Atlanta_GA", etc.
    country TEXT,
    holiday_date TEXT,        -- YYYY-MM-DD
    holiday_name TEXT,
    office_name TEXT,
    office_address TEXT,
    city TEXT,
    is_active INTEGER
);

-- HR policy document pages
CREATE TABLE policy_documents (
    document_name TEXT,       -- "Leave Policy", "Dress Code Policy - India", etc.
    page_number INTEGER,
    page_text TEXT            -- Full extracted text of the page
);
```

---

### 5. HOCON Agent Network Structure

```
associate_hub.hocon
├── metadata (description, tags, sample_queries)
├── llm_config (azure-openai, gpt-4o-mini)
├── max_execution_seconds: 300
└── tools[]
    ├── faq_agent               (front man, LLM, has all tools in scope)
    ├── associate_lookup        (CodedTool, class: AssociateLookupTool)
    ├── holiday_lookup          (CodedTool, class: HolidayLookupTool)
    ├── policy_search           (CodedTool, class: PolicySearchTool)
    ├── compliance_check        (CodedTool, class: ComplianceTool)
    ├── it_support_agent        (LLM agent, instructions embedded)
    ├── goperform_agent         (LLM agent, instructions embedded)
    ├── transport_agent         (LLM agent, instructions embedded)
    ├── mediassist_agent        (LLM agent, instructions embedded)
    └── talent_marketplace_agent (LLM agent, instructions embedded)
```

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| Flat architecture (no nested sub-agents for DB tools) | Sub-agent wrappers caused infinite tool-call loops in Neuro-SAN |
| Parameters inside `function{}` in HOCON | Neuro-SAN only reads `function.parameters` for LLM tool calling |
| compliance_tool returns full profile fields | Prevents N/A in greeting when ID + compliance asked together |
| HOCON hot-reload (5s interval) | Allows instruction updates without server restart |
| CodedTool base class + `invoke(args, sly_data)` | Required by Neuro-SAN framework for coded tools |
