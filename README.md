# OpsPilot — Autonomous Incident Investigation Agent

An agentic AI system that autonomously investigates software production incidents using tool calling, planning, retrieval-augmented generation (RAG), evidence verification, reflection, and human-in-the-loop approval.

---

## Architecture

```
                         ┌───────────────────────┐
                         │      User Request      │
                         │ "Investigate latency"  │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │    SUPERVISOR /        │
                         │    ORCHESTRATOR        │
                         │  (run_investigation)   │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      PLANNER          │
                         │  create_plan(goal)     │
                         │  re_plan() on demand   │
                         └───────────┬───────────┘
                                     │
                                     ▼
               ┌─────────────────────────────────────┐
               │         TOOL REGISTRY               │
               │  Dynamic dispatch by tool name       │
               ├──────────┬──────────┬───────────────┤
               │  Metrics  │  Logs    │  Deployments  │
               │  query_   │  search_ │  get_         │
               │  metrics  │  logs    │  deployments  │
               ├──────────┼──────────┼───────────────┤
               │ Incidents│ Runbook  │   RAG         │
               │ search_  │ retrieve_│ Knowledge Base│
               │ incidents│ runbook  │ Vector Search  │
               └──────────┴──────────┴───────────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  HYPOTHESIS GENERATOR  │
                         │  LLM + Evidence →      │
                         │  Root Cause Hypothesis │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  EVIDENCE VERIFIER     │
                         │  Check observations    │
                         │  against hypotheses    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  REFLECTION / CRITIC   │
                         │  Assess sufficiency    │
                         │  Find contradictions   │
                         │  Consider alternatives │
                         └───────────┬───────────┘
                                     │
                          ┌──────────┴──────────┐
                          │                     │
                    Re-plan if           Report if
                    insufficient         sufficient
                          │                     │
                          ▼                     ▼
                    ┌───────────┐       ┌───────────────┐
                    │  RE-PLAN  │       │ INCIDENT REPORT│
                    │ New steps │       │ Root Cause     │
                    └───────────┘       │ Confidence     │
                                        │ Evidence       │
                                        │ Action         │
                                        └───────┬───────┘
                                                │
                                                ▼
                                        ┌───────────────┐
                                        │ HUMAN APPROVAL│
                                        │ (if action is │
                                        │  high-impact) │
                                        └───────────────┘
```

---

## Features

| Requirement | Status | Implementation |
|---|---|---|
| 7+ Tools with schemas | Done | `query_metrics`, `search_logs`, `get_deployments`, `search_incidents`, `retrieve_runbook`, `create_incident_report`, `request_rollback` |
| Dynamic Tool Registry | Done | `ToolRegistry` class maps tool names to specs and functions |
| Multi-Step Agent Loop | Done | Plan → Execute → Observe → Hypothesize → Reflect → Re-plan → Report |
| Planning & Re-Planning | Done | Template-based plans with dependency tracking; re-plan on insufficient evidence |
| Reflection / Critic | Done | Evidence sufficiency check, contradiction detection, alternative hypotheses, trajectory logging |
| RAG Knowledge Layer | Done | 8 architecture documents, chunked, embedded (sentence-transformers), vector retrieved |
| Agentic RAG | Done | On-demand retrieval with query reformulation on weak results |
| Human-in-the-Loop | Done | Rollback actions require explicit approval; approval state tracked |
| Autonomous Controls | Done | Max iterations (20), max tool calls (50), max retries (3), duplicate call detection |
| Observability | Done | Full trajectory logging with per-incident timeline viewer |
| Evaluation (30 Scenarios) | Done | Subprocess-isolated evaluation pipeline with metric tracking |
| FastAPI Backend | Done | REST API with investigation, trajectory, approval, and evaluation endpoints |
| Streamlit UI | Done | Dashboard with Investigate, Approvals, Trajectory, and Evaluation tabs |
| Docker Packaging | Done | Dockerfile + docker-compose.yml |

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone / navigate to the project
cd OpsPilot_Agentic_AI

# Install dependencies
pip install -r requirements.txt
```

### Run the CLI

```bash
# Single investigation
python main.py "Investigate why checkout API latency increased in the last two hours"

# Run evaluation (30 scenarios)
python main.py evaluate

# Generate failure analysis report
python main.py failure-analysis
```

### Run the Streamlit UI

```bash
streamlit run ui/app.py --server.port 8501
```

Open `http://localhost:8501` in your browser.

### Run the FastAPI Backend

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API documentation at `http://localhost:8000/docs`

### Docker

```bash
docker-compose up
```

Runs both API (port 8000) and UI (port 8501).

---

## Streamlit Cloud Deployment

Deploy the exact existing OpsPilot UI to [Streamlit Cloud](https://streamlit.io/cloud) — no
separate backend service is required. The Streamlit app imports the `opspilot` Python modules
directly (metrics, logs, deployments, incidents, RAG, agent loop, approvals, observability), so
`api/main.py` (FastAPI) is optional and not needed for the UI to function.

### 1. GitHub repository

```
nikkudeekshith/OpsPilot-Agentic-AI
```

### 2. Branch

```
main
```

### 3. Streamlit entry point

The app **must** be pointed at the existing UI file — not `main.py` (which is the CLI entry point):

```
ui/app.py
```

| Field | Value |
|---|---|
| Repository | `nikkudeekshith/OpsPilot-Agentic-AI` |
| Branch | `main` |
| Main file path | `ui/app.py` |

> `main.py` contains a CLI-only `sys.stdout` wrapper. It is isolated so it can never break the
> Streamlit UI, but `ui/app.py` is the correct Streamlit entry point.

### 4. Required secrets

Configure in **Streamlit Cloud → app → Settings → Secrets**:

```toml
OPENAI_API_KEY = "sk-..."
```

The key is **optional but recommended**. Without it, the agent runs in keyword-based fallback
mode. The app reads the key from Streamlit secrets first, then the `OPENAI_API_KEY` environment
variable (or a local `.env` file). Never commit a real key — `.env.example` only contains a
placeholder.

### 5. Required environment variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | No (recommended) | Enables real LLM reasoning/hypothesis generation |

All other configuration is code/data embedded in the repository.

### 6. Local run command

```bash
streamlit run ui/app.py --server.port 8501
```

Open `http://localhost:8501`.

### 7. Streamlit Cloud run configuration

- **Python version:** the platform default (3.11/3.12) is supported.
- **Dependencies:** installed automatically from `requirements.txt`.
- **Secrets:** add `OPENAI_API_KEY` as shown above, then **Rerun** the app.
- **Deploys:** push to the `main` branch (or press "Rerun"/deploy in the dashboard).

### 8. Known limitations on Streamlit Cloud

- **30-scenario evaluation (`Run Full Evaluation`):** the evaluation pipeline isolates each
  scenario in a sub-process (`subprocess.run`), which the Streamlit Cloud sandbox restricts.
  The Analytics page will show a friendly message instead of a traceback. Run evaluations
  locally with `python main.py evaluate` or `python main.py failure-analysis`.
- **In-memory state:** investigations, trajectories, and approvals live in memory; they reset on
  rerun and are not persisted between sessions.
- **Synthetic data:** metrics, logs, deployments, and incidents are simulated — connect your own
  monitoring systems to generalize.
- **Optional embeddings:** `sentence-transformers` is intentionally not required; the RAG layer
  falls back to keyword scoring when it is absent.

### 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `AttributeError: ... has no attribute 'buffer'` | Make sure the Main file path is `ui/app.py` (not `main.py`). |
| UI loads but investigations use fallback reasoning | Add `OPENAI_API_KEY` to app Secrets and Rerun. |
| Analytics evaluation fails | Expected on Cloud (sub-process sandbox); run evaluation locally via CLI. |
| Changes not appearing after push | Confirm you are on `main` and the branch is `main` in the dashboard. |

---

## Project Structure

```
OpsPilot_Agentic_AI/
│
├── main.py                     CLI entry point
├── requirements.txt            Python dependencies
├── Dockerfile                  Container definition
├── docker-compose.yml          Multi-service orchestration
├── .env.example                Environment variable template
│
├── opspilot/                   Core agent package
│   ├── __init__.py
│   ├── schemas.py              Pydantic models (State, Plan, Hypothesis, Report, etc.)
│   ├── state.py                Agent state and memory management
│   ├── planner.py              Plan generation and re-planning
│   ├── loop.py                 Main agent execution loop
│   ├── reflection.py           Evidence critique and re-plan trigger
│   ├── llm.py                  LLM integration (OpenAI + smart fallback)
│   ├── controls.py             Autonomous safety limits
│   ├── observability.py        Trajectory logging
│   ├── human_approval.py       Human-in-the-loop approval workflow
│   │
│   ├── tools/                  Tool implementations
│   │   ├── registry.py         Dynamic tool dispatch
│   │   ├── metrics.py          query_metrics
│   │   ├── logs.py             search_logs
│   │   ├── deployments.py      get_deployments
│   │   ├── incidents.py        search_incidents
│   │   ├── runbook.py          retrieve_runbook
│   │   ├── report.py           create_incident_report
│   │   └── rollback.py         request_rollback
│   │
│   ├── rag/                    RAG knowledge layer
│   │   ├── knowledge_base.py   8 architecture documents + chunking
│   │   ├── embedding.py        Sentence-transformer embeddings
│   │   └── retriever.py        Vector + Agentic retriever
│   │
│   └── evaluation/             Evaluation framework
│       ├── scenarios.py        30 synthetic incident scenarios
│       ├── pipeline.py         Subprocess-isolated evaluation
│       └── failure_analysis.py Auto-generated failure report
│
├── api/
│   └── main.py                 FastAPI REST API
│
├── ui/
│   └── app.py                  Streamlit dashboard
│
└── tests/
    └── test_basic.py           14 unit tests
```

---

## Evaluation Methodology

### Metrics

| Metric | Description | Calculation |
|---|---|---|
| Investigation Success Rate | Did the workflow complete? | Loop terminated with "complete" or "sufficient" reason |
| Tool Selection Accuracy | Correct tools chosen? | Intersection of used tools and expected tools / union size |
| Root Cause Accuracy | Final diagnosis matches expected cause? | Word overlap + substring matching against expected root cause |
| Average Tool Calls | Efficiency | Mean tools used across all scenarios |
| Average Confidence | Mean confidence score | Average of report confidence across all scenarios |
| Evidence Grounded Rate | Claims supported by evidence? | Scenarios with >= 2 evidence items |
| Loop Completion Rate | Workflows terminate correctly? | Percentage of scenarios finishing without error |

### Running Evaluation

```bash
python main.py evaluate
```

Each scenario runs in an isolated subprocess to prevent state leakage. Results include per-scenario metrics and aggregate scores.

### 30 Scenarios

Scenarios cover:
- Latency spikes (checkout-api, payment-service)
- Error rate increases
- Database timeouts and connection pool exhaustion
- CPU and memory anomalies
- Deployment-related degradation
- Webhook and callback failures
- Rollback assessment

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/investigate` | Run investigation |
| GET | `/trajectory/{incident_id}` | Get agent trajectory |
| GET | `/approvals/pending` | List pending approvals |
| POST | `/approvals/respond` | Approve or deny request |
| POST | `/evaluate` | Run evaluation |
| GET | `/evaluate/failure-analysis` | Failure analysis report |
| GET | `/health` | Health check |

---

## Using a Real LLM

Create a `.env` file with your API key:

```
OPENAI_API_KEY=sk-...
```

Or set it as an environment variable. The agent will automatically use GPT-4o-mini for:
- Tool selection decisions
- Hypothesis generation with confidence scoring
- Reflection and critique

Without an API key, the agent uses a keyword-based fallback that handles common scenarios but may struggle with ambiguous cases.

---

## Technical Review Questions

**Why an agent instead of a deterministic workflow?**
Incidents are unpredictable. An agent adapts its investigation path dynamically based on tool outputs, evidence gathered, and hypothesis confidence. No two incidents follow exactly the same path.

**Where can the agent loop?**
Repeated identical tool calls (handled by duplicate detection), reflection-triggered re-planning cycles (handled by max iteration limit), and empty observation retries (handled by max retries).

**How is tool-routing evaluated?**
Each scenario defines expected tools. The evaluation pipeline compares actual tool selections against expected ones, measuring accuracy as intersection over union.

**How are malformed tool arguments handled?**
The registry validates arguments against the tool's schema. Invalid arguments are replaced with defaults, and the error is logged in the trajectory.

**What about prompt injection in retrieved documents?**
Retrieved RAG content is treated as evidence, not as instructions. The agent observes and cites it but does not execute commands from it.

**Why include reflection?**
Reflection catches insufficient evidence, missed investigation paths, and contradictions. It measurably improves investigation quality by triggering re-planning when needed.

**How are duplicate tool calls prevented?**
The agent tracks the last 5 tool calls. If the same tool+arguments appear more than once, it's flagged as duplicate. A retry with modified parameters is attempted up to 3 times.

**What state is persisted?**
Incident goal, investigation plan, tool history, observations, evidence, hypotheses, iteration count, reflection results, and the final report. Everything is in-memory (no database).

**When must the system ask for human approval?**
Any high-impact operational action (rollback, restart, scaling) requires explicit human approval. Read-only actions (metrics queries, log searches) execute automatically.

---

## Limitations

1. **LLM Fallback:** Without a real API key, hypothesis generation is rule-based and may not capture nuanced root causes.
2. **Synthetic Data:** All monitoring data is simulated. Real integration requires Prometheus/Datadog adapters.
3. **No Persistence:** State is in-memory. Restarting loses history.
4. **Static Knowledge Base:** RAG documents are fixed. No dynamic ingestion from the UI.
5. **Sequential Evaluation:** 30 scenarios run sequentially; evaluation takes time.

---

## Future Work

- LangGraph migration for state graph management
- Live Prometheus/Datadog metric integration
- Persistent SQLite/PostgreSQL state storage
- Dynamic RAG ingestion via the UI
- Multi-turn conversational investigation refinement
- Parallel evaluation with multiprocessing
- Security audit logging and prompt injection detection

---

## License

Internship project for educational purposes.
