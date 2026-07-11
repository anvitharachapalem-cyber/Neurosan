# Architecture

## Overview

This project is an AI-powered HR assistant for Cognizant associates, built on Cognizant's neuro-san framework. An associate types a question in natural language — about RTO compliance, office holidays, HR policies, IT support, transport, or benefits — and receives an accurate, real-time answer drawn from live databases and embedded domain knowledge.

The system is composed of an nsflow web frontend, a neuro-san agent server, a multi-agent network of nine cooperating agents, and a SQLite database containing associate, attendance, holiday, and policy data.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Associate (Browser)                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  HTTP / WebSocket
┌──────────────────────────────▼──────────────────────────────────────┐
│                  nsflow UI  (port 4173)                              │
│              FastAPI + React Chat Interface                          │
│  - Renders conversation history                                      │
│  - Maintains chat_context for multi-turn sessions                   │
│  - Sends each message to the neuro-san server                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  gRPC / HTTP  (port 8080)
┌──────────────────────────────▼──────────────────────────────────────┐
│              neuro-san Server  (port 8080)                           │
│  - Loads agent registry from registries/manifest.hocon              │
│  - Hot-reloads HOCON config every 5 seconds                         │
│  - Routes requests to the associate_hub agent network               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  neuro-san Agent Engine
┌──────────────────────────────▼──────────────────────────────────────┐
│              neuro-san Multi-Agent Network                           │
│        (defined in registries/hackathon/associate_hub.hocon)        │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   faq_agent  (Orchestrator)                     │ │
│  │   LLM: Azure OpenAI GPT-4o-mini                                │ │
│  │   - Classifies query: PERSONAL vs GENERIC                      │ │
│  │   - Collects Associate ID only for personal queries            │ │
│  │   - Greets associate with full profile after lookup            │ │
│  │   - Routes to correct coded tool or specialist agent           │ │
│  │   Tools available:                                             │ │
│  │    ├── associate_lookup   (CodedTool)                          │ │
│  │    ├── holiday_lookup     (CodedTool)                          │ │
│  │    ├── policy_search      (CodedTool)                          │ │
│  │    ├── compliance_check   (CodedTool)                          │ │
│  │    ├── it_support_agent                                        │ │
│  │    ├── goperform_agent                                         │ │
│  │    ├── transport_agent                                         │ │
│  │    ├── mediassist_agent                                        │ │
│  │    └── talent_marketplace_agent                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ associate_lookup │  │  holiday_lookup  │  │  policy_search   │  │
│  │  (CodedTool)     │  │  (CodedTool)     │  │  (CodedTool)     │  │
│  │  associates DB   │  │ office_holidays  │  │ policy_documents │  │
│  │  table           │  │  table           │  │  table (102 pgs) │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │compliance_check  │  │  it_support_agent│  │  goperform_agent │  │
│  │  (CodedTool)     │  │  LLM Agent       │  │  LLM Agent       │  │
│  │  attendance DB   │  │  ServiceNow /    │  │  Goal-setting /  │  │
│  │  RTO thresholds  │  │  GSD tickets     │  │  Ratings / PIP   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ transport_agent  │  │         mediassist_agent                 │ │
│  │  LLM Agent       │  │         LLM Agent                        │ │
│  │  Cab / MoveInSync│  │  MediBuddy / Insurance claims            │ │
│  └──────────────────┘  └──────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │             talent_marketplace_agent  (LLM Agent)            │   │
│  │         TMP roles / applications / manager approval          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                               │  SQL queries
┌──────────────────────────────▼──────────────────────────────────────┐
│                    SQLite Database  (hackathon.db)                   │
│   associates (50) │ attendance (4,213) │ office_holidays (267)       │
│                   policy_documents (102 pages)                       │
└─────────────────────────────────────────────────────────────────────┘
                               │  API calls
┌──────────────────────────────▼──────────────────────────────────────┐
│              Azure OpenAI API  (GPT-4o-mini)                        │
│         Endpoint: https://hr-mod-ai.openai.azure.com/               │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Frontend — nsflow UI (port 4173)

A FastAPI + React chat interface that:

- Renders a scrolling conversation history.
- Sends each associate message to the neuro-san server over gRPC/HTTP.
- Persists `chat_context` across turns so the agent remembers previous messages in the session.
- Displays the agent's response with full formatting.

### 2. neuro-san Server (port 8080)

The agent runtime that:

- Loads the active agent registry from `registries/manifest.hocon`.
- Hot-reloads HOCON configuration every 5 seconds — instruction updates take effect without a server restart.
- Routes each incoming request to the `associate_hub` agent network.
- Manages agent lifecycle, tool dispatch, and LLM API calls.

### 3. Agent Registry — registries/
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

HOCON configuration files that define the entire agent network:

| File | Purpose |
|---|---|
| `registries/manifest.hocon` | Lists which agent HOCON files are active |
| `registries/hackathon/associate_hub.hocon` | Defines all 9 agents/tools with LLM instructions |
| `registries/hackathon/manifest.hocon` | Registry entry pointing to associate_hub.hocon |

### 4. Multi-Agent Network — associate_hub.hocon

The agent network contains nine tools:

| Tool | Type | Role |
|---|---|---|
| `faq_agent` | LLM agent (orchestrator) | Top-level entry point. Classifies query as personal or generic, collects Associate ID when needed, greets with full profile, routes to correct specialist. |
| `associate_lookup` | CodedTool (Python) | Queries `associates` table. Returns name, level, account, supervisor, work model, city, office. Always called first for personal queries. |
| `holiday_lookup` | CodedTool (Python) | Queries `office_holidays` table. Returns full holiday list + office address for the associate's city. |
| `policy_search` | CodedTool (Python) | Keyword-scores all 102 HR policy pages in `policy_documents`. Returns top matches with document name, page number, and excerpt. |
| `compliance_check` | CodedTool (Python) | Computes RTO attendance % from `attendance` table. Applies correct threshold per work model and grade group. Returns compliant/non-compliant status. |
| `it_support_agent` | LLM agent | ServiceNow ticket procedures, GSD, software requests, accessories. |
| `goperform_agent` | LLM agent | GoPerform goal-setting, KPIs, ratings, mid-year review, PIP. |
| `transport_agent` | LLM agent | One Transport cab booking, MoveInSync app, missed cabs, reimbursement. |
| `mediassist_agent` | LLM agent | MediBuddy registration, cashless hospitalisation, insurance claims. |
| `talent_marketplace_agent` | LLM agent | TMP role browsing, applications, manager confirmation, feedback. |

### 5. CodedTools — coded_tools/hackathon/

Four custom Python classes extending neuro-san's `CodedTool` interface:

**associate_lookup_tool.py**
- Input: `associate_id` (int)
- Queries: `associates` table
- Returns: Full profile — name, level, account, supervisor, work model, office, city, country

**holiday_lookup_tool.py**
- Input: `location` (city name)
- Queries: `office_holidays` table — location-specific + national (`ALL`) holidays
- Returns: Holiday list, office name, full office address, total holiday count

**policy_search_tool.py**
- Input: `query` (string)
- Queries: `policy_documents` table — 102 pages across 13 HR PDFs
- Returns: Top 5 results with `document_name`, `page_number`, `relevance_score`, `excerpt`, `citation`

**compliance_tool.py**
- Input: `associate_id` (int), `month` (string)
- Queries: `associates` + `attendance` tables
- Returns: Attendance %, required %, compliance status, days attended, total business days
- Logic: Thresholds vary by work model × grade group

```
Compliance Thresholds:
──────────────────────────────────────────────────────
Work Model                 Senior (D+)   Junior (AD-)
──────────────────────────────────────────────────────
Cog hybrid 2/3 days          80%            70%
Cog office based 4/5 days    85%            80%
Cog remote 0/1 days           5%             0%
Cog CLT RMT                 100%            95%
──────────────────────────────────────────────────────
```

## Agentic System Highlights

This project showcases several key capabilities of the neuro-san agentic framework:

**LLM-driven routing:** No hard-coded `if/else` routing logic. The `faq_agent` orchestrator reads the user's natural language request and autonomously selects the appropriate tool — the LLM is the router.

**Flat architecture:** All coded tools and LLM agents are siblings under `faq_agent`. Nested sub-agent wrappers were deliberately avoided — they caused infinite tool-call loops in neuro-san's execution model.

**CodedTool integration:** Pure Python database logic is seamlessly plugged into the agent network as first-class tools via the `CodedTool` base class and `invoke(args, sly_data)` interface.

**Multi-turn conversation:** `chat_context` is threaded from one turn to the next, giving the agent memory of the Associate ID and prior answers without a separate session database.

**Declarative configuration:** The entire agent topology — instructions, tool wiring, LLM model, parameters — is declared in a HOCON file. No orchestration boilerplate is needed in application code.

**Hot-reload:** The server re-reads HOCON files every 5 seconds. Instruction changes take effect immediately without restarting the server.

## Data Flow

```
Associate types: "Am I RTO compliant for June?"
    │
    ▼
nsflow frontend sends message to neuro-san server (port 8080)
    │
    ▼
neuro-san routes message to faq_agent (orchestrator LLM)
    │
    ├─► faq_agent asks: "Please share your Associate ID"
    │
    ├─► Associate replies: "12345"
    │
    ├─► faq_agent calls associate_lookup(associate_id=12345)
    │       └─► Returns: Priya Sharma | Senior Associate | Hybrid 2/3 | Bangalore
    │
    └─► faq_agent calls compliance_check(associate_id=12345, month="June")
            └─► Queries attendance table → 14/22 days = 63.6%
                └─► Threshold for Hybrid Senior = 60% → COMPLIANT ✅
    │
    ▼
faq_agent composes: "Hello Priya Sharma! ... June compliance: ✅ Compliant (63.6%)"
    │
    ▼
Response returned to nsflow frontend → rendered in chat
```

## Technology Stack

| Layer | Technology |
|---|---|
| Agent Framework | neuro-san v0.6.71 |
| LLM | Azure OpenAI GPT-4o-mini |
| Frontend | nsflow v0.6.16 (FastAPI + React) |
| Agent Config | HOCON |
| Custom Tools | Python 3.10 (CodedTool interface) |
| Database | SQLite (hackathon.db) |
| LLM Adapters | LangChain (langchain-openai) |
