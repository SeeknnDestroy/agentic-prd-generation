# 🛠️ Agentic‑PRD‑Generation

> **Status — pre‑alpha / planning phase**
> We are currently drafting the Product Requirements Document (PRD) and have not committed any source code yet. Follow the roadmap below for upcoming milestones.

## 📖 What is this project?

An AI‑powered platform that **iteratively generates Project Requirement Documents (PRDs) _and_ the follow‑up Technical Specification (Tech Spec)** through an agentic workflow.
The goal is to compare vanilla LLM clients (OpenAI & Google GenAI) with popular agent frameworks (CrewAI, AutoGen, etc.) while visualising every step—outline, draft, critique, revision—in real time.

## ✨ Planned core features (MVP)

| Phase | Feature | Planned? |
|-------|---------|----------|
| **A** | Vanilla workflow using official `openai` and `google-generativeai` Python clients | ✔ Planned |
| **B** | Pluggable adapter modules for frameworks (CrewAI, AutoGen, …) | ✔ Planned |
| — | FastAPI backend that streams live updates (SSE or WebSocket) | ✔ Planned |
| — | Minimal front‑end (Streamlit) showing<br>• current step<br>• latest full PRD<br>• diff history | ✔ Planned |
| — | One‑click **“Generate Tech Spec”** from the approved PRD | ✔ Planned |

*See [`docs/PRD.md`](docs/PRD.md) for the full requirements.*

## 🗺️ Roadmap

1. **Docs** – finalise PRD → get stakeholder sign‑off.
2. **Scaffolding** – repo structure, CI, basic FastAPI + Streamlit “hello world”.
3. **Phase A** – implement vanilla LLM workflow.
4. **Phase B** – implement first framework adapter (CrewAI).
5. **Tech Spec generator** – agent that converts the final PRD into a design doc.
6. Additional framework adapters & comparison report.

*Timeline details live inside the PRD.*

## 🏗️ Repository structure (planned)

```

backend/     # FastAPI app (to be created)
frontend/    # Streamlit UI (to be created)
agents/      # Framework‑specific adapters
docs/        # PRD.md, future Tech\_Spec.md, diagrams
.github/     # CI workflows, templates

```

## 🤝 Contributing

We welcome issues and discussions even before code lands.
A `CONTRIBUTING.md` guide will be added once the initial scaffolding is ready.

## 📜 License

MIT
