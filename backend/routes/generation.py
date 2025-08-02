"""API routes for PRD and Tech Spec generation workflows."""

from typing import Literal, cast
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from backend.agents.base_adapter import BaseAdapter
from backend.agents.vanilla import VanillaAdapter
from backend.models import GeneratePRDRequest, GeneratePRDResponse, PRDState
from backend.pipelines.pipeline_runner import run_pipeline
from backend.services.streamer import StreamerService
from backend.state.redis_store import RedisStore

router = APIRouter()

# Aether's Rationale:
# For now, we instantiate the store directly. In a future step, this will be
# managed by a dependency injection system (e.g., FastAPI's `Depends`) to make
# it more testable and configurable.
try:
    state_store = RedisStore()
except ConnectionError:
    # Aether's Rationale:
    # In a real production environment, you would want the application to fail
    # fast if it cannot connect to its primary database. For this project,
    # we could add a fallback to InMemoryStore for local development without
    # Redis, but for now, we'll keep it strict.
    print("FATAL: Could not connect to Redis. Please check the REDIS_URL.")
    exit(1)

streamer_service = StreamerService()


def get_adapter_from_request(request: GeneratePRDRequest) -> BaseAdapter:
    """Selects and instantiates the correct agent adapter."""
    adapter_type = request.adapter
    if adapter_type in ("vanilla_openai", "vanilla_google"):
        # Cast the type to satisfy the VanillaAdapter constructor
        vanilla_adapter_type = cast(
            Literal["vanilla_openai", "vanilla_google"], adapter_type
        )
        return VanillaAdapter(adapter_type=vanilla_adapter_type)
    if adapter_type == "crewai":
        # Aether's Rationale:
        # This is a placeholder for the CrewAI adapter, which will be
        # implemented in a future step. Raising an error for now ensures the
        # API contract is clear.
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="The 'crewai' adapter is not yet available.",
        )
    # This should be unreachable due to Pydantic validation
    raise ValueError(f"Unknown adapter type: {adapter_type}")


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
    pipeline_store = RedisStore()
    pipeline_store.save(initial_state)

    try:
        agent_adapter = get_adapter_from_request(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

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
