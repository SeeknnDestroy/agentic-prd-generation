# Technical Specification

## Architecture

- FastAPI application with lifespan-managed runtime resources
- `AppSettings` loaded with `pydantic-settings`
- Shared `StateStore` selected by configuration:
  - `memory`: always use the in-memory store
  - `redis`: require Redis to be reachable
  - `auto`: use Redis when reachable, otherwise fall back to memory
- Shared `StreamerService` that fans out updates to all subscribers for a run
- Streamlit frontend that starts runs and listens for SSE updates without rerun-driven reconnects

## Workflow

1. Persist an initial `Outline` state with the original idea.
2. Generate outline content.
3. Generate draft content.
4. Run critique and revise iterations until approval or the revision limit is reached.
5. Persist `Complete`, or `Error` when a provider call fails.

## Public API

### `POST /api/v1/generate_prd`

Request body:

```json
{
  "idea": "AI project idea",
  "adapter": "vanilla_openai"
}
```

Supported adapters:

- `vanilla_openai`
- `vanilla_google`

Response body:

```json
{
  "run_id": "uuid"
}
```

### `GET /api/v1/stream/{run_id}`

- Replays the latest persisted state first
- Streams future run updates as SSE `message` events

Event payload:

```json
{
  "run_id": "uuid",
  "step": "Draft",
  "content": "# PRD ...",
  "revision": 2,
  "diff": "@@ ...",
  "error": null,
  "created_at": "2026-03-10T12:00:00Z"
}
```

### `GET /health`

- Lightweight liveness probe

### `GET /ready`

- Reports readiness for the selected state backend

## Data Model

Persisted run state includes:

- `run_id`
- `idea`
- `step`
- `content`
- `revision`
- `diff`
- `error`
- `created_at`

The original `idea` is stored for pipeline correctness but omitted from the public SSE payload.

## Operational Notes

- OpenAI calls use the official `openai` SDK.
- Google calls use the supported `google-genai` SDK.
- Structured logging is emitted with step, adapter, run id, and outcome metadata.

## Test Strategy

- Unit tests cover runtime selection, pipeline transitions, streamer fan-out, frontend helpers, and CLI wiring.
- Integration tests cover `POST /generate_prd` plus late-subscriber SSE replay.
- CI keeps `ruff`, `mypy`, and `pytest` as baseline gates.
