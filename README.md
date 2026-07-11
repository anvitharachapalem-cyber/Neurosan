# Cognizant Associate Hub — AI Multi-Agent Assistant

An AI-powered multi-agent assistant built on the **Neuro-SAN** framework that acts as a single conversational entry point for all Cognizant associate queries — HR policies, RTO compliance, office holidays, IT support, transport, health insurance, GoPerform, and Talent Marketplace.

---

## Quick Start

### Prerequisites
- Python 3.10+
- Azure OpenAI access (GPT-4o-mini deployment)
- Corporate proxy configured

### Installation

```bash
# Clone the repo
git clone https://github.com/anvitharachapalem-cyber/Neurosan.git
cd neuro-san-studio

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Set the following environment variables (or add to your run script):

```bash
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
OPENAI_API_VERSION=2024-12-01-preview
AGENT_MANIFEST_FILE=registries/manifest.hocon
PYTHONPATH=<path-to-neuro-san-studio>
AGENT_TOOL_PATH=<path-to-neuro-san-studio>/coded_tools
```

### Start the Server

```bash
# Start both backend server (port 8080) and UI (port 4173)
python -m neuro_san_studio run --server-http-port 8080 --nsflow-port 4173
```

Open **http://localhost:4173** and select **`hackathon/associate_hub`**.

### CLI Testing

```bash
python -m neuro_san.client.agent_cli \
  --agent hackathon/associate_hub \
  --http --host localhost --port 8080 \
  --one_shot --minimal
```

---

## Features

| Capability | Description |
|---|---|
| Holiday Lookup | Live office holiday list + address for 30+ global locations |
| RTO Compliance | Real attendance % vs threshold from DB |
| Policy Search | Full-text search across 13 HR policy PDFs with page citations |
| Associate Lookup | Profile: name, level, work model, account, supervisor |
| IT Support | GSD ticket guidance via ServiceNow / OneCognizant |
| GoPerform | Performance goals, ratings, PIP, mid-year review |
| Transport | Cab scheduling, tracking, MoveInSync / One Transport |
| MediAssist | MediBuddy insurance, claims, cashless hospitalisation |
| Talent Marketplace | TMP access, role applications, manager confirmation |

---

## Sample Queries

**No Associate ID needed:**
- `"What are the holidays in Bangalore?"`
- `"What is the leave encashment policy?"`
- `"How do I raise a GSD ticket?"`
- `"How do I book a desk in the office?"`
- `"What happens if I miss my cab?"`

**Associate ID required:**
- `"My associate ID is 2378257. What is my RTO compliance for June?"`
- `"Hi, my ID is 2378291"` → Full profile greeting

---

## Project Structure

```
registries/hackathon/
  associate_hub.hocon       # Agent network definition

coded_tools/hackathon/
  associate_lookup_tool.py  # DB: associate profile
  holiday_lookup_tool.py    # DB: office holidays + address
  policy_search_tool.py     # DB: full-text policy search
  compliance_tool.py        # DB: RTO attendance compliance

database/hackathon/
  hackathon.db              # SQLite: associates, attendance, holidays, policies
  Policy_Documents/         # 13 HR policy PDFs
```
