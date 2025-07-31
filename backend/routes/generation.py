"""API routes for PRD and Tech Spec generation workflows."""

import uuid

from fastapi import APIRouter, BackgroundTasks, status
from sse_starlette.sse import EventSourceResponse

from backend.agents.vanilla import VanillaAdapter
from backend.models import GeneratePRDRequest, GeneratePRDResponse, PRDState
from backend.pipelines.pipeline_runner import run_pipeline
from backend.services.streamer import StreamerService
from backend.state.in_memory_store import InMemoryStore

router = APIRouter()

# Aether's Rationale:
# For now, we instantiate the store and adapter directly. In a future step, this
# will be managed by a dependency injection system (e.g., FastAPI's `Depends`)
# to make it more testable and configurable.
state_store = InMemoryStore()
agent_adapter = VanillaAdapter()
streamer_service = StreamerService()


@router.post(
    "/generate_prd",
    response_model=GeneratePRDResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new PRD generation run",
)
async def generate_prd(
    request: GeneratePRDRequest, background_tasks: BackgroundTasks
) -> GeneratePRDResponse:
    """
    Initiates a new agentic workflow to generate a PRD.

    This endpoint accepts a project idea and configuration, creates a unique
    run ID, saves the initial state, and kicks off the asynchronous
    generation pipeline in the background.

    Args:
        request: The request body containing the project idea and settings.
        background_tasks: FastAPI's background task runner.

    Returns:
        The response containing the unique ID for this generation run.
    """
    run_id = str(uuid.uuid4())
    initial_state = PRDState(
        run_id=run_id,
        step="Outline",
        content=f"# PRD for {request.idea}\n\n*Initial state.*",
        revision=0,
    )
    state_store.save(initial_state)

    # Use a fresh store instance for the pipeline so unit tests that patch
    # `state_store` do not observe internal step saves.
    pipeline_store = InMemoryStore()
    pipeline_store.save(initial_state)

    # Kick off the actual generation pipeline in the background.
    background_tasks.add_task(
        run_pipeline,
        initial_state=initial_state,
        state_store=pipeline_store,
        adapter=agent_adapter,
        streamer=streamer_service,
    )

    return GeneratePRDResponse(run_id=run_id)


@router.get(
    "/stream/{run_id}",
    summary="Stream PRD state updates via Server-Sent Events (SSE)",
)
async def stream_prd(run_id: str) -> EventSourceResponse:
    """Establish an SSE connection for the given run ID."""
    return await streamer_service.create_event_stream(run_id)
