# Project Summary

## What We Built

Cognizant associates spend significant time navigating multiple portals to get answers to everyday workplace questions — RTO compliance status lives in one system, office holiday calendars in another, IT support tickets in a third, and HR policy documents somewhere else entirely. Switching between OneCognizant, ServiceNow, GoPerform, MediBuddy, and One Transport for routine queries is a daily friction point.

We built **Associate Hub** — an AI-powered conversational assistant that gives every Cognizant associate a single interface for all their workplace queries. An associate can ask about their RTO compliance, look up office holidays, raise an IT issue, check transport cab rules, or search HR policy documents — all in one chat window, in natural language. The system knows when a query is personal (and asks for an Associate ID) and when it is generic (and answers immediately without any ID).

## The Problem

Associates face two recurring frustrations:

**Information fragmentation:** Every HR, IT, and operations function has its own portal with its own login and navigation model. Finding the answer to "Am I RTO compliant this month?" requires knowing which portal tracks attendance, locating the correct work-model threshold, and doing the arithmetic manually.

**Policy discoverability:** HR policy documents are long PDFs spread across Be.Cognizant. Associates rarely know which document contains the answer they need, and keyword search across portals is unreliable.

Our system eliminates both problems through a single conversational interface backed by a multi-agent AI system with real data.

## How It Works

The application is structured as a conversational web app. Associates interact through **nsflow** (a FastAPI + React chat interface) and the backend is powered by a multi-agent system built on Cognizant's open-source **neuro-san** framework.

### The Agentic System

The core of the project is a network of nine cooperating AI agents and tools, all configured declaratively in a HOCON file and orchestrated by neuro-san at runtime:

**faq_agent (Orchestrator)** — The top-level agent that receives every user message. It classifies the query as personal or generic, collects the Associate ID only when the query requires personal data, greets the associate by name with their full profile, and routes the request to the correct specialist agent or coded tool.

**associate_lookup (CodedTool)** — Queries the `associates` SQLite table and returns the associate's full profile: name, level, account, supervisor, office, city, country, and work model. Always called first for any personal query.

**holiday_lookup (CodedTool)** — Queries the `office_holidays` table for location-specific and national holidays. Returns the full holiday list for the associate's city along with the office name and address.

**policy_search (CodedTool)** — Performs keyword-scored search across 102 pages of official HR policy PDFs stored in the `policy_documents` table. Returns the top matching excerpts with document name, page number, and citation.

**compliance_check (CodedTool)** — Computes RTO compliance for a given associate and month from 4,213 attendance records. Applies the correct threshold based on work model and grade level, and returns attendance percentage, required percentage, and compliance status.

**it_support_agent, goperform_agent, transport_agent, mediassist_agent, talent_marketplace_agent** — Five specialist LLM agents, each with embedded domain knowledge covering ServiceNow ticket procedures, GoPerform goal-setting cycles, One Transport cab booking, MediBuddy health insurance claims, and Talent Marketplace project applications respectively.

The key architectural insight is that no routing logic is hard-coded in Python. The orchestrator agent reads the user's natural language request and autonomously selects the right tool — the LLM is the router. Adding a new domain requires only a new tool entry in the HOCON file.

### Multi-Turn Conversations

neuro-san's `chat_context` mechanism threads conversation state across turns. An associate can say "What are my holidays in Bangalore?" and follow up with "Am I compliant this month?" — providing their ID only once. The framework manages context persistence automatically.

## Technology Choices

| Concern | Choice | Reason |
|---|---|---|
| Agent orchestration | neuro-san v0.6.71 | Declarative HOCON-based agent config; no orchestration boilerplate; built-in multi-turn context; CodedTool interface for Python extensions |
| LLM | Azure OpenAI GPT-4o-mini | Strong instruction-following; low latency; enterprise-grade Azure deployment |
| Frontend | nsflow v0.6.16 | FastAPI + React chat UI purpose-built for neuro-san agent networks |
| Database | SQLite | Zero-infrastructure local DB; 4 tables, 4,500+ rows of real associate and HR data |
| Agent config | HOCON | Supports comments and includes; readable hierarchical structure ideal for multi-agent topologies |

## Project Structure

```
neuro-san-studio/
├── registries/
│   └── hackathon/
│       ├── associate_hub.hocon         # Full agent network definition (9 agents + tools)
│       └── manifest.hocon              # Registry entry for neuro-san server
├── coded_tools/
│   └── hackathon/
│       ├── associate_lookup_tool.py    # Associate profile lookup from SQLite
│       ├── holiday_lookup_tool.py      # Office holiday lookup by location
│       ├── policy_search_tool.py       # Keyword-scored HR policy search
│       └── compliance_tool.py          # RTO attendance compliance calculator
├── database/
│   └── hackathon/
│       └── hackathon.db               # SQLite: associates, attendance, holidays, policies
├── requirements.txt                    # Python dependencies
├── architecture.md                     # System architecture documentation
├── summary.md                          # This file
└── README.md                           # Setup and run instructions
```

## What Makes This Interesting for a Hackathon

**Zero routing boilerplate:** The entire multi-agent routing logic is expressed in natural language inside the `faq_agent` instructions. The LLM decides which tool to call — no `if/elif` chains, no intent classifiers.

**Real enterprise data:** The system runs against a realistic dataset — 50 associates, 4,213 attendance records, 267 office holiday entries across 30+ global locations, and 102 pages of official HR policy documents.

**Correct compliance logic:** RTO thresholds vary by work model (hybrid/office-based/remote/CLT-RMT) and grade group (Senior: D and above vs Junior: AD and below). The compliance tool applies the right threshold per associate automatically.

**Policy citations:** Every HR policy answer includes a `[Document Name, Page X]` citation so associates know exactly where to verify the information.

**Extensible by design:** Adding a new HR domain (payroll, learning, travel) requires only a new tool block in the HOCON file — no Python changes to the routing logic.

## Example Interaction

```
User:   What are the holidays in my office this year?

Agent:  Could you please share your Associate ID?

User:   12345

Agent:  Hello Priya Sharma! 👋
        Senior Associate | Cognizant Digital Engineering | Bangalore
        Supervisor: Ramesh Kumar | Work Model: Cog hybrid 2/3 days

        Here are the upcoming holidays for Cognizant Bangalore (RMZ Ecoworld):

        • 15 Aug 2026 — Independence Day
        • 02 Oct 2026 — Gandhi Jayanti
        • 02 Nov 2026 — Kannada Rajyotsava
        ...and 12 more holidays this year.

User:   Am I RTO compliant for June?

Agent:  June 2026 Compliance for Priya Sharma:
        ✅ Compliant — Attended 14/22 business days (63.6%)
        Required for Hybrid 2/3 days (Senior): 60% minimum.
```

## Future Work

- Support for payroll and leave balance queries via additional coded tools.
- Voice interface integration for hands-free query resolution on mobile.
- Proactive compliance alerts — notify associates approaching non-compliance before month end.
- Multi-language support for associates across global delivery centres.
- Manager view — supervisors can query compliance status for their entire team.
