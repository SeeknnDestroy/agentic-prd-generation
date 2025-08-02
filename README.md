# 🛠️ Agentic‑PRD‑Generation

> **Status — Alpha / Implementation Phase**
> The project scaffolding is complete, and the core backend logic for the vanilla agent workflow is currently under development.

## 📖 What is this project?

An AI‑powered platform that **iteratively generates Project Requirement Documents (PRDs) _and_ the follow‑up Technical Specification (Tech Spec)** through an agentic workflow.
The goal is to compare vanilla LLM clients (OpenAI & Google GenAI) with popular agent frameworks (CrewAI, AutoGen, etc.) while visualising every step—outline, draft, critique, revision—in real time.

## ✨ Core Features (MVP)

| Phase | Feature | Status |
|-------|---------|----------|
| **A** | Vanilla workflow using official `openai` and `google-generativeai` Python clients | 🚧 In Progress |
| **B** | Pluggable adapter modules for frameworks (CrewAI, AutoGen, …) | ⏳ Planned |
| — | FastAPI backend that streams live updates via SSE | ✅ Implemented |
| — | Minimal front‑end (Streamlit) showing progress | 🚧 In Progress |
| — | One‑click **“Generate Tech Spec”** from the approved PRD | ⏳ Planned |

*See [`docs/PRD.md`](docs/PRD.md) for the full requirements.*

## 🗺️ Roadmap

1.  **Docs** – ✅ Finalise PRD and Tech Spec.
2.  **Scaffolding** – ✅ Set up repo structure, CI, and basic FastAPI + Streamlit apps.
3.  **Phase A** – 🚧 Implement the vanilla LLM workflow, including real LLM calls and connecting the frontend to the backend stream.
4.  **Phase B** – ⏳ Implement the first framework adapter (e.g., CrewAI).
5.  **Tech Spec Generator** – ⏳ Build the agent that converts the final PRD into a design doc.
6.  **Evaluation** – ⏳ Add more framework adapters & generate a comparison report.

*Timeline details live inside the PRD.*

## 🏗️ Repository Structure

```
backend/     # FastAPI app with routes, services, and agent pipeline
frontend/    # Streamlit UI application
agents/      # Shared agent protocols (interfaces)
docs/        # PRD.md, TECH_SPEC.md, and diagrams
.github/     # CI workflows and issue templates
```

## 🤝 Contributing

We welcome issues and discussions.
A `CONTRIBUTING.md` guide will be added once the core features are stable.

## 📜 License

MIT
