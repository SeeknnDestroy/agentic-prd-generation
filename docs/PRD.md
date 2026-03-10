# Product Requirements Document

## Summary

Agentic PRD Generation is an MVP that turns a single project idea into a structured PRD. The product emphasizes reliability and transparency over breadth: only implemented adapters and behaviors are exposed.

## Goals

- Produce a usable PRD draft with iterative outline, draft, critique, and revise stages.
- Stream the latest run state to the UI in real time.
- Keep local development and testing simple by working with either Redis or an in-memory fallback.

## In Scope

- One `POST /api/v1/generate_prd` endpoint that accepts `idea` and `adapter`
- One `GET /api/v1/stream/{run_id}` endpoint that replays the latest state and then streams future updates
- Streamlit UI for entering an idea, selecting an implemented adapter, and following a live PRD run
- Implemented adapters only: `vanilla_openai` and `vanilla_google`

## Out of Scope

- Framework comparison adapters
- Human-in-the-loop approval checkpoints
- Stop or cancel controls
- Tech spec generation

## Functional Requirements

- A new run must persist an initial state immediately.
- Each pipeline step must save a new immutable state with a truthful workflow step.
- Provider failures must end the run with `step="Error"` and a separate `error` field.
- SSE subscribers must receive the latest persisted state even if they connect late.

## Non-Functional Requirements

- Local development must work without Redis by falling back to in-memory storage.
- Health and readiness checks must reflect the actual backend state honestly.
- The repo must keep passing `ruff`, `mypy`, and `pytest`.

## Acceptance Criteria

- Submitting an idea returns a `run_id`.
- Refreshing or reconnecting to an active run replays the latest known state.
- Failed provider calls do not produce fake successful completions.
- The frontend only exposes shipped adapters and shipped behaviors.
