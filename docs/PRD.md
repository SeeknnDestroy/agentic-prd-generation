# Project Requirement Document: Agentic PRD Generation

1. **Executive Summary**
   - “Agentic PRD Generation” is a platform that automates the creation of high‑quality PRDs **and, in Phase 2, the accompanying Technical Specification** through an agentic loop (outline → draft → critique → revise). A real‑time front‑end visualises progress, helping developers and product managers turn ideas into structured, actionable plans quickly.

2. **Success Metrics & Evaluation**
   - **PRD Quality** – average rubric score ≥ 4/5 (clarity, completeness, coherence).
   - **User Satisfaction** – CSAT ≥ 80 % or NPS ≥ 40 among pilot users.
   - **Framework Insights** – qualitative comparison report produced in Phase B.
   - **Tech Spec Completeness (Phase 2)** – generated spec passes an internal checklist (architecture, APIs, risks) with ≥ 90 % coverage.

3. **Functional Scope**
   - **Input** – single high‑level project idea.
   - **Agentic Workflow** – Outline → (optional) Research → Draft → Critique/Revise → **Generate Tech Spec**.
   - **Framework Implementation**
     - **Phase A (Required):** vanilla `openai` & `google-generativeai` clients.
     - **Phase B (Optional/Pluggable):** `openai‑agents`, `CrewAI`, `AutoGen`, `smolagents`. Others (LangGraph, LangChain, LlamaIndex, DSPy) may be added after MVP.
   - **Real‑Time UI** – display current step, full up‑to‑date PRD, diff history, and a **“Generate Tech Spec”** button.
   - **Autonomy Levels** – Full vs. Supervised (user approvals at checkpoints).

4. **Non‑Functional Requirements**
   - **Performance** – end‑to‑end PRD generation ≤ 5 min on a standard project idea.
   - **Reliability** – retry logic on LLM API errors; graceful degradation.
   - **Usability** – intuitive UI, zero onboarding docs required.
   - **Extensibility** – add new framework adapters with minimal refactor.

5. **Solution Architecture**

   **5.1 Phase A — Vanilla Clients**
   - FastAPI orchestrator.
   - State in Redis (local dev fallback: in‑memory dict).
   - Each agentic step is a **pure async function** that transforms an immutable `PRDState`; an async functional pipeline composes these steps end‑to‑end.
   - Streaming via **Server‑Sent Events (SSE)**; `/stop` endpoint lets the UI cancel a run.

   **5.2 Phase B — Framework Adapters**
   - One module per framework (`agents/crewai_adapter.py`, etc.).
   - Strategy pattern selects the adapter; shared state & streaming layer remain untouched.

6. **Technology Stack**

   | Category | Required | Optional / Experimental |
   |----------|----------|-------------------------|
   | **Backend** | FastAPI (≥0.110), Python 3.11+ | – |
   | **LLM Clients** | `openai`, `google-generativeai` | – |
   | **Agentic Frameworks** | – | `openai‑agents`, `CrewAI`, `AutoGen`, `smolagents`, … |
   | **Front‑end** | Streamlit (fastest to PoC) | Future React/Next.js port |
   | **State / Streaming** | Redis + SSE | WebSocket upgrade if bidirectional control needed |

7. **Agentic Workflow Spec**

   1. **Outline** – generate structured headings; exit when template matched.
   2. **Research (Optional)** – targeted web search for ambiguous sections; exit on time or confidence threshold.
   3. **Draft** – populate all sections.
   4. **Critique & Revise Loop** – critique agent checks clarity/guardrails → revision agent fixes; repeat until no issues.
   5. **Generate Tech Spec** – new agent consumes final PRD JSON, outputs architecture, APIs, risks.
   - **Guardrails** – relevance checks, harmful‑content filter, user “stop” control.

8. **UI Wireframe Outline**

   - **Input Bar** – project idea, “Generate PRD” button.
   - **Sidebar** – autonomy level radio buttons; framework selector.
   - **Main Panel**
     - **Status Banner** – current step (e.g., “Drafting…”).
     - **Live PRD View** – markdown rendering auto‑refreshes.
     - **Diff / Changelog** – collapsible.
     - **Tech Spec Tab** (appears after PRD approval) – live stream of the spec.
     - **Generate Tech Spec** button.

9. **MVP Milestones & Timeline**

   | Week | Deliverable |
   |------|-------------|
   | 1 | Repo scaffolding, FastAPI + Streamlit hello‑world, SSE pipeline mocked |
   | 2 | Vanilla workflow with real OpenAI & Google clients |
   | 3 | Live PRD diff viewer |
   | 4 | First framework adapter (CrewAI) |
   | 5 | Tech Spec generator + UI tab; decide whether to add more adapters |

10. **Risks & Mitigations**

   | Risk | Mitigation |
   |------|------------|
   | Inconsistent LLM output | Deterministic prompts, critique loop, temperature tuning |
   | Scope creep from many frameworks | Limit Phase B to 1–2 adapters for MVP |
   | State sync complexity | Start with Redis pub/sub; monitor latency before adding WebSockets |
   | API cost overruns | Cache repeated calls, batch generations during research |

11. **Acceptance‑Test Checklist**

   - [ ] Submit idea → receive complete PRD.
   - [ ] UI streams current workflow step in real time.
   - [ ] PRD view updates after each revision; diff displayed.
   - [ ] User can choose Phase A or a Phase B adapter.
   - [ ] “Generate Tech Spec” button produces a spec streamed to UI.
   - [ ] PRD passes quality rubric (≥ 4/5).
   - [ ] Tech Spec covers architecture, APIs, risks (≥ 90 % checklist).
   - [ ] Autonomy level setting correctly pauses for approvals.
