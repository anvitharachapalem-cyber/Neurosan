# Cognizant Associate Hub — Summary

## Project Name
**Associate Hub** — AI-Powered Multi-Agent HR Assistant for Cognizant Associates

## Problem Statement
Associates frequently need answers to HR, compliance, IT, transport, and policy queries. These are currently scattered across multiple portals (OneCognizant, ServiceNow, MediBuddy, GoPerform, One Transport), requiring associates to navigate different systems for each query type.

## Solution
A single conversational AI assistant that routes any associate query to the right specialist agent and responds with accurate, real-time data — reducing time spent navigating portals.

## Technology Stack
- **Framework:** Neuro-SAN (Cognizant AI Labs multi-agent framework)
- **LLM:** Azure OpenAI GPT-4o-mini
- **Agent Config:** HOCON (registries/hackathon/associate_hub.hocon)
- **Backend DB:** SQLite (associates, attendance, office holidays, policy documents)
- **UI:** nsflow (FastAPI + React web interface)
- **Language:** Python 3.10+

## Agents Built

| Agent | Type | Data Source |
|---|---|---|
| `faq_agent` | LLM Router (front man) | Instructions + sub-agents |
| `associate_lookup` | Coded Tool | SQLite DB |
| `holiday_lookup` | Coded Tool | SQLite DB |
| `policy_search` | Coded Tool | SQLite DB (PDF pages) |
| `compliance_check` | Coded Tool | SQLite DB (attendance) |
| `it_support_agent` | LLM Knowledge Agent | Embedded Q&A |
| `goperform_agent` | LLM Knowledge Agent | Embedded Q&A |
| `transport_agent` | LLM Knowledge Agent | Embedded Q&A |
| `mediassist_agent` | LLM Knowledge Agent | Embedded Q&A |
| `talent_marketplace_agent` | LLM Knowledge Agent | Embedded Q&A |

## Key Capabilities

### 1. Smart Query Classification
- Routes **generic queries** (holidays, policies, IT, transport) immediately — no ID required
- Routes **personal queries** (compliance, profile, supervisor) only after collecting Associate ID

### 2. Real-Time Data from Database
- **Holiday lookups** — 267 holiday records across 30+ global office locations with exact addresses
- **RTO Compliance** — 4,213 attendance records; calculates % attendance vs work-model threshold
- **Associate Profile** — 50 associates with level, work model, account, supervisor, location
- **Policy Search** — 102 pages across 13 official HR policy PDFs

### 3. Policy Citations
Every HR policy answer includes `[Document Name, Page X]` citation and ends with:
> *"For more information, please visit Be.Cognizant > People Policies in the People section."*

### 4. Accurate Greeting
When an Associate ID is provided, the system greets:
> *"Welcome, {Name}! | Level: {level} | Work Model: {work_model} | Account: {account} | Location: {city}, {country} | Supervisor: {supervisor_name}"*

## Database Schema

| Table | Records | Purpose |
|---|---|---|
| `associates` | 50 | Profile, level, work model, supervisor |
| `attendance` | 4,213 | Daily office attendance records (Jan–Jul 2026) |
| `office_holidays` | 267 | Holidays per location + office address |
| `policy_documents` | 102 | PDF pages with full text for search |

## Files
| File | Purpose |
|---|---|
| `registries/hackathon/associate_hub.hocon` | Full agent network definition |
| `coded_tools/hackathon/associate_lookup_tool.py` | Associate profile DB tool |
| `coded_tools/hackathon/holiday_lookup_tool.py` | Holiday & office address DB tool |
| `coded_tools/hackathon/policy_search_tool.py` | Policy full-text search DB tool |
| `coded_tools/hackathon/compliance_tool.py` | RTO compliance calculator DB tool |
| `database/hackathon/hackathon.db` | SQLite database |
| `database/hackathon/Policy_Documents/` | 13 HR policy PDFs |

## Results
- ✅ Holiday query answered in ~3 seconds with full list + office address
- ✅ Policy query answered with document + page citation
- ✅ Compliance check returns exact % with compliant/non-compliant status
- ✅ Profile greeting with all fields (name, level, account, location, supervisor)
- ✅ Zero N/A values in profile responses
- ✅ No infinite loops in tool calls
