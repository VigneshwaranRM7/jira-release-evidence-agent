# Yellow Network AI Engineering Assessment: Jira Release Evidence Agent

An autonomous, backend-first Jira Evidence Agent built with **FastAPI** and **Python 3.10+**. The agent evaluates release readiness for service **`atlas-assistant`** against **Release `R2.4`**, commit **`b7a91f2`**, prompt version **`p7`**, in the **`production`** environment using evidence from Atlassian Jira Cloud (or an offline in-memory Mock provider).

---

## 📑 Architecture Overview

The codebase strictly adheres to the client's architecture specification (`struture.md`):

```
project/
├── main.py                          # Application entrypoint & FastAPI ASGI initialization
├── definitions.py                   # Central workspace constants, enums, and project paths
├── pyproject.toml                   # Project metadata and tool configuration
├── requirements.txt                 # Pinned dependencies
├── .env.example                     # Environment configuration template
├── README.md                        # Documentation and run instructions
│
├── data/
│   └── dataset.json                 # Extracted benchmark dataset (400 records, 2,059 comments)
│
├── artifacts/
│   ├── release_readiness_report.md  # Generated Markdown readiness report
│   ├── release_readiness_report.json# Structured JSON release assessment
│   └── investigation_trace.json     # Telemetry trace logging tool invocations, latency, tokens
│
├── models/v1/
│   ├── jira/
│   │   ├── dataset.py               # Dataset schemas (TargetBuildConfig, DatasetRecord)
│   │   └── issue.py                 # Jira issue models (JiraIssue, JiraComment, JiraSearchResult)
│   ├── assessment/
│   │   ├── manifest.py              # AssessmentManifest & AssessmentManifestItem models
│   │   ├── decision.py              # RequirementEvaluation & ReleaseDecisionSummary models
│   │   └── report.py                # AssessmentRunRequest & ReleaseReadinessReport models
│   └── telemetry/
│       └── trace.py                 # ToolInvocation & InvestigationTrace models
│
├── controllers/v1/
│   ├── jira/
│   │   ├── base_client.py           # Abstract BaseJiraClient interface
│   │   ├── mock_client.py           # In-memory Jira Cloud v3 provider with JQL parser & link index
│   │   ├── cloud_client.py          # Real Jira Cloud REST API v3 client with basic auth
│   │   └── bulk_importer.py         # Two-pass repeatable bulk dataset importer
│   ├── agent/
│   │   ├── tools/
│   │   │   ├── registry.py          # OpenAI/JSON schemas for agent function calls
│   │   │   ├── search.py            # search_jira_issues tool execution
│   │   │   ├── issue.py             # get_ticket_details and get_ticket_comments tool execution
│   │   │   └── link.py              # get_linked_evidence tool execution
│   │   ├── prompts.py               # Agent system prompt embedding manifest rules
│   │   └── engine.py                # ReAct investigation engine collecting evidence & telemetry
│   ├── assessment/
│   │   ├── policy_rules.py          # Deterministic policy auditor evaluating REQ-01 through REQ-12
│   │   └── orchestrator.py          # Central coordinator executing runs and caching results
│   └── report/
│       └── generator.py             # Formatter generating Markdown, JSON, and Trace artifacts
│
├── routes/v1/
│   ├── api_router.py                # Master v1 router aggregating all endpoints
│   ├── system/
│   │   └── health.py                # System health check endpoint
│   ├── jira/
│   │   └── importer.py              # Trigger dataset bulk import endpoint
│   └── assessment/
│       ├── assessment.py            # POST /run and GET /{id}/status endpoints
│       ├── report.py                # GET /{id}/report (JSON or Markdown) endpoint
│       └── trace.py                 # GET /{id}/trace endpoint
│
├── utils/
│   ├── context.py                   # Pydantic BaseSettings loading .env configuration
│   ├── text_parser.py               # Scenario comment parser (extracting actor, role, timestamp)
│   ├── cost_calculator.py           # Rate-card model cost calculator
│   └── telemetry.py                 # Telemetry collector tracking tool calls, duration, and tokens
│
├── scripts/
│   ├── import_dataset.py            # CLI script to run bulk dataset import
│   └── run_assessment.py            # Standalone CLI script to run release assessment
│
└── tests/
    ├── conftest.py                  # Pytest fixtures (async HTTP client, mock Jira client)
    ├── test_importer.py             # 2-pass bulk import and scenario metadata tests
    ├── test_agent_tools.py          # Unit tests for the 4 Jira agent tools & schemas
    ├── test_policy_rules.py         # Complete evaluation tests across all 12 requirements
    └── test_api_endpoints.py        # FastAPI API lifecycle integration tests
```

---

## 🎯 Target Build & Benchmark Decisions

### Target Configuration
- **Release:** `R2.4`
- **Commit:** `b7a91f2`
- **Service:** `atlas-assistant`
- **Environment:** `production`
- **Prompt:** `p7`
- **Dataset Scope Label:** `tyn-release-assessment-v2`

### Evaluation Summary
- **Overall Decision:** 🔴 **`BLOCKED`**
- **Scorecard:** **4 PASSED**, **7 FAILED**, **1 INSUFFICIENT EVIDENCE** (Total: 12 Mandatory Requirements)

| Requirement | Title | Decision | Reason / Critical Finding | Key Record |
| :--- | :--- | :---: | :--- | :--- |
| **REQ-01** | Automated regression tests | **PASS** | `REG-804` passed 146 of 146 tests on target commit `b7a91f2` in production. | `REC-2081` |
| **REQ-02** | Customer document isolation | **FAIL** | `ISO-318` leak detected: customer ALPHA received BETA-017; defect `ISO-DEF-12` reopened. | `REC-1001` |
| **REQ-03** | Prompt answer quality | **FAIL** | `EVAL-55` was tested with frozen prompt `p6`, not deployed prompt `p7`. | `REC-4323` |
| **REQ-04** | End-to-end latency | **PASS** | `PERF-827` measured p95 latency of 1.40s under peak load (<= 2.0s limit). | `REC-6024` |
| **REQ-05** | Model cost budget | **FAIL** | `COST-881` cost is USD 0.018 > USD 0.012 threshold; dev waiver note rejected per manifest. | `REC-5716` |
| **REQ-06** | Security sign-off | **FAIL** | Asha Rao approved `STAGING` scope only; production sign-off explicitly pending. | `REC-2828` |
| **REQ-07** | Log redaction verification | **PASS** | Retest `REDACT-901` explicitly supersedes `REDACT-870` with 28/28 redactions passing. | `REC-9745` |
| **REQ-08** | Support team handoff delivery | **FAIL** | `HND-77` 0/12 escalated chats delivered; open blocker defect `HND-DEF-4`. | `REC-9635` |
| **REQ-09** | Rollback rehearsal data preservation | **FAIL** | `RB-402` restore completed but lost 214 session records during the recovery window. | `REC-6198` |
| **REQ-10** | Document parsing completeness | **PASS** | Retest `PARSE-622` explicitly supersedes `PARSE-601` with 60/60 documents parsing. | `REC-9611` |
| **REQ-11** | Accessible keyboard navigation | **INSUFFICIENT** | `KBD-210` was tested on release `R2.3` (commit `42d0a19`); unverified on `R2.4`. | `REC-8801` |
| **REQ-12** | Streaming response integrity | **FAIL** | `STREAM-731` case `STREAM-50` produced duplicate final message (49/50 passed). | `REC-5957` |

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10+
- pip

### 2. Environment Setup
```bash
# Clone or navigate to the project directory
cd project

# Create virtual environment (optional but recommended)
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
To run against real Atlassian Jira Cloud:
```env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_jira_api_token
```
*Note: If Jira credentials are not configured or `--mock` is passed, the system runs with the high-performance offline Mock provider.*

### 4. Running with Docker (Alternative)
```bash
# Build and run with Docker Compose
docker compose up -d

# Check logs
docker compose logs -f
```

---

## 🛠️ Usage Instructions

### 1. Repeatable Jira Bulk Importer (CLI)
Import the dataset into Jira Cloud (or verify against the in-memory mock client):
```bash
python scripts/import_dataset.py --mock
```
Output:
```
=== Jira Dataset Bulk Importer ===
Dataset File: C:\Users\...\data\dataset.json
Project Key:  REL
Using High-Performance In-Memory Mock Jira Client

--- Import Summary ---
Issues Created:   400
Comments Created: 2059
Links Created:    76
Bulk import completed successfully.
```

### 2. Run Autonomous Assessment (CLI)
Run the full 12-rule release readiness assessment and generate deliverables:
```bash
python scripts/run_assessment.py
```
Output:
- Prints executive summary, requirement-by-requirement scorecard, and telemetry.
- Generates all deliverables in `artifacts/`:
  - `artifacts/release_readiness_report.md`
  - `artifacts/release_readiness_report.json`
  - `artifacts/investigation_trace.json`

### 3. Launch FastAPI Backend Server
Start the Uvicorn ASGI server:
```bash
python main.py
```
Or via uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health status and timestamp |
| `POST` | `/api/v1/jira/import` | Trigger repeatable bulk dataset import |
| `POST` | `/api/v1/assessment/run` | Execute autonomous release readiness assessment |
| `GET` | `/api/v1/assessment/{id}/status` | Check assessment run progress |
| `GET` | `/api/v1/assessment/{id}/report` | Fetch release report (`?format=json` or `?format=markdown`) |
| `GET` | `/api/v1/assessment/latest/report` | Fetch latest release report |
| `GET` | `/api/v1/assessment/{id}/trace` | Fetch investigation tool execution trace and token metrics |
| `GET` | `/api/v1/assessment/latest/trace` | Fetch latest investigation trace |

---

## 🧪 Automated Testing

Run the automated test suite with pytest:
```bash
python -m pytest tests/ -v
```

### Test Suite Coverage:
- `tests/test_importer.py`: 2-pass import, comment scenario parsing, and inward/outward link resolution.
- `tests/test_agent_tools.py`: All 4 Jira tools (`search_jira_issues`, `get_ticket_details`, `get_ticket_comments`, `get_linked_evidence`), function calling schemas, and telemetry collector.
- `tests/test_policy_rules.py`: Exact verification of all 12 requirement decisions against manifest acceptance criteria and release synthesis logic.
- `tests/test_api_endpoints.py`: End-to-end FastAPI test coverage for health, import, assessment execution, Markdown/JSON reports, and traces.

---

## 💡 Key Design & Engineering Highlights

1. **Strict Folder Structure Adherence**: Root `main.py`, `definitions.py`, modular `controllers/v1/`, `routes/v1/`, `models/v1/`, `utils/`, `scripts/`, `tests/` cleanly decoupling API routing, business logic, schemas, and persistence.
2. **Deterministic Manifest Auditing**: Evaluates evidence strictly against the target commit (`b7a91f2`), environment (`production`), service (`atlas-assistant`), and prompt (`p7`), correctly rejecting superseded runs, staging-only sign-offs, and informal developer waivers.
3. **Comprehensive Telemetry & Traceability**: Every tool call records step index, arguments, summary output, execution duration, and token usage, persisted in `artifacts/investigation_trace.json`.
4. **Dual Jira Provider Support**: Supports both live Atlassian Cloud REST API v3 instances and high-performance in-memory mock execution for 100% reproducible testing.

