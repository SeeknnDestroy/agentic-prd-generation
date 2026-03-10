# Agentic PRD Generation

Alpha-stage MVP for generating Product Requirements Documents with a small, honest surface area.

## Current Scope

- Generate PRDs from a single project idea.
- Stream state updates from FastAPI to Streamlit over SSE.
- Use either the OpenAI adapter or the Google GenAI adapter.
- Persist run state in Redis when available, with automatic fallback to in-memory storage for local development and tests.

## Not Shipped Yet

- Framework comparison adapters such as CrewAI or AutoGen
- Supervised checkpoints or stop controls
- Technical specification generation

## Architecture

- `backend/`: FastAPI API, runtime setup, adapters, pipeline, and state backends
- `frontend/`: Streamlit UI for starting runs and following live updates
- `tests/`: unit and integration coverage for runtime selection, pipeline behavior, streaming, and CLI wiring

The backend uses lifespan-managed shared resources: `AppSettings`, one `StateStore`, and one `StreamerService` per process.

## Quickstart

1. Install dependencies:

```bash
pip install -e ".[dev,test]"
```

2. Create local configuration:

```bash
cp .env.example .env
```

3. Add at least one provider key to `.env`.

4. Run the backend:

```bash
agentic-prd --host 0.0.0.0 --port 8000 --reload
```

5. Run the frontend:

```bash
streamlit run frontend/app.py --server.port 8501
```

6. Open `http://localhost:8501`.

## Quality Gates

```bash
ruff check .
ruff format --check .
mypy backend frontend
pytest
```

## Docker

Runtime images install only the application package and its runtime dependencies.

```bash
docker-compose up --build
```

## Docs

- [`docs/PRD.md`](docs/PRD.md): current MVP product requirements
- [`docs/TECH_SPEC.md`](docs/TECH_SPEC.md): current architecture and API contract
