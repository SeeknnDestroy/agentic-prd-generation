# Technical Specification — Agentic‑PRD‑Generation
*Version 0.1 • 2025‑07‑16*

---

## 1  Purpose & Scope
This document describes **how** we will implement the platform defined in [`docs/PRD.md`](PRD.md).  
It translates the *what/why* from the PRD into concrete architecture, APIs, data models, tooling, and quality attributes so any engineer can start coding with minimal ambiguity.

---

## 2  High‑Level Architecture

```

┌─────────────────────────────────────────────┐
│                  Front‑end                  │
│  Streamlit UI                               │
│  ├─ Input bar                               │
│  ├─ Status banner (SSE)                     │
│  ├─ Live PRD viewer                         │
│  └─ Diff / Tech‑Spec tab                    │
└───────────────▲───────────────▲─────────────┘
│ SSE/WebSocket │
│               │
┌───────────────┴───────────────┴─────────────┐
│                 FastAPI API                 │
│  /generate_prd  /stop  /generate_spec       │
│  ├─ Orchestrator service                    │
│  ├─ Agent adapters (strategy pattern)       │
│  └─ State manager (Redis)                   │
└───────────────▲───────────────▲─────────────┘
│ Async calls   │
│               │
┌──────────┴──────────┐   ┌┴────────────┐
│ OpenAI client (vA)  │   │ Google‑GenAI│
└─────────────────────┘   └─────────────┘

````

*A PNG/SVG version will be committed to `docs/diagrams/architecture_v1.png`.*

---

## 3  Component Design

| ID | Component | Responsibilities | Key Classes / Files |
|----|-----------|------------------|---------------------|
| **C1** | **Front‑end** | Render UI, open SSE channel, send user commands | `frontend/app.py`, `components/*` |
| **C2** | **API Gateway** | FastAPI routes, auth middleware | `backend/routes/*.py` |
| **C3** | **Pipeline Runner** | Functional async pipeline (`generate_outline` → `draft` → `critique` → `revise`); emits state events | `backend/pipelines/pipeline_runner.py` |
| **C4** | **Adapter Protocol** | Defines a single `call_llm()` function consumed by the pipeline        | `backend/agents/base_adapter.py`              |
| **C5** | **Adapter (Vanilla)** | Implements `call_llm` using OpenAI & Google clients                   | `backend/agents/vanilla.py`                   |
| **C6** | **Adapter (CrewAI)** | Wraps CrewAI workflow; adheres to C4 | `backend/agents/crewai_adapter.py` |
| **C7** | **State Manager** | Read/write PRD JSON, revision diff, progress | `backend/state/redis_store.py` |
| **C8** | **Streaming Service** | Push state deltas via SSE; optional WebSocket upgrade | `backend/services/streamer.py` |

---

## 4  Public API (FastAPI)

| Verb | Path | Payload | Response | Notes |
|------|------|---------|----------|-------|
| `POST` | `/generate_prd` | `{idea, autonomy, adapter}` | `{run_id}` | Starts Phase A/B run |
| `POST` | `/stop` | `{run_id}` | `202 Accepted` | Graceful cancel |
| `POST` | `/generate_spec` | `{run_id}` | `{spec_run_id}` | Triggers Tech Spec agent |
| `GET` | `/stream/{run_id}` | — | `text/event‑stream` | Emits JSON events: `{"step":"Draft","delta":"…"}"` |

---

## 5  Data Models

```python
class PRDState(BaseModel, frozen=True):
    run_id: str
    step: Literal["Outline","Research","Draft","Critique","Revise","Complete"]
    content: str            # full markdown
    revision: int
    diff: str | None        # unified diff vs. previous rev
    created_at: datetime
````

*Redis key:* `prd:{run_id}`
*TTL:* 7 days (configurable).

---

## 6  Agent Interface

```python
from typing import Protocol

class BaseAdapter(Protocol):
    async def call_llm(self, prompt: str) -> str: ...
```

All adapters (**vanilla, CrewAI, AutoGen…**) must:

* Implement the same coroutine methods.
* Emit `state_manager.save()` after each step.
* Respect `self.cancelled` flag (set by `/stop`).

---

## 7  Technology & Dependencies

| Layer  | Library                                       | Pin      |
| ------ | --------------------------------------------- | -------- |
| API    | `fastapi`                                     | `^0.110` |
| LLM    | `openai` ≥ 1.14 • `google-generativeai` ≥ 0.5 |          |
| Stream | `sse-starlette`                               |          |
| State  | `redis[p asyncio]`                            |          |
| UI     | `streamlit` ≥ 1.34                            |          |
| Dev    | `uvicorn`, `pytest`, `ruff`, `pre-commit`     |          |

---

## 8  Environment Variables

```env
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
REDIS_URL=redis://localhost:6379/0
AGENTIC_ADAPTER=vanilla_openai     # default
```

Secrets stored in GitHub Actions + `.env.example` for local dev.

---

## 9  Quality Attributes & Targets

| Attribute         | Target                        | Mechanism                                              |
| ----------------- | ----------------------------- | ------------------------------------------------------ |
| **Performance**   | PRD ≤ 5 min (95‑th pct)       | Async I/O, batching research calls                     |
| **Reliability**   | 99.5 % successful runs        | Retry w/ exponential back‑off, idempotent state writes |
| **Usability**     | Zero‑doc onboarding           | Inline hints, sane defaults                            |
| **Observability** | Trace each LLM call & latency | OpenTelemetry + console exporter (MVP)                 |
| **Security**      | No secrets in logs            | Pydantic redaction, HTTPS only                         |

---

## 10  Testing Strategy

| Layer       | Tool                        | Coverage                  |
| ----------- | --------------------------- | ------------------------- |
| Unit        | `pytest` + `pytest‑asyncio` | ≥ 80 %                    |
| Integration | Local Redis + mock LLMs     | agent loop end‑to‑end     |
| Contract    | `schemathesis` on `/stream` | SSE schema                |
| LLM Quality | rubric scorer agent         | PRD score automated in CI |

---

## 11  Deployment & CI/CD

* **CI** – GitHub Actions (`ci.yml`): lint ➜ unit tests ➜ upload coverage badge.
* **Preview** – Streamlit Community Cloud on every `main` push.
* **Prod candidate** – Docker Compose (`docker-compose.yml`) with FastAPI, Redis, Nginx.

---

## 12  Risks & Mitigations

| Risk                | Probability | Impact | Mitigation                        |
| ------------------- | ----------- | ------ | --------------------------------- |
| LLM API cost spike  | M           | H      | caching, temperature ≤ 0.7        |
| Redis single point  | L           | M      | allow env swap to AWS Elasticache |
| Framework API drift | M           | M      | pin versions, weekly Dependabot   |

---

## 13  Glossary

| Term        | Meaning                                                            |
| ----------- | ------------------------------------------------------------------ |
| **Agent**   | Autonomous loop that reasons → acts → writes state                 |
| **Adapter** | Wrapper that maps a third‑party agent framework to our `BaseAgent` |
| **Run ID**  | UUID for one PRD or Tech‑Spec generation session                   |

---

## 14  Acceptance Criteria (Tech Spec)

* [ ] All components described above exist as code stubs.
* [ ] `uvicorn backend.main:app` starts with no errors.
* [ ] `/generate_prd` returns `run_id`; `/stream/{run_id}` streams hello‑world events.
* [ ] Vanilla adapter completes full loop with mocked LLMs.
* [ ] CI passes on a clean clone (`make ci`).

---

## 15  Sign‑off

| Role         | Name  | Date | Signature |
| ------------ | ----- | ---- | --------- |
| Product Lead | *TBD* |      |           |
| Tech Lead    | *TBD* |      |           |
| QA Lead      | *TBD* |      |           |
