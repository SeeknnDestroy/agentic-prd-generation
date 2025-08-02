"""API routes for PRD and Tech Spec generation workflows."""

from typing import Annotated, Literal, cast
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from backend.agents.base_adapter import BaseAdapter
from backend.agents.vanilla import VanillaAdapter
from backend.models import GeneratePRDRequest, GeneratePRDResponse, PRDState
from backend.pipelines.pipeline_runner import run_pipeline
from backend.services.streamer import StreamerService
from backend.state.base import StateStore
from backend.state.redis_store import RedisStore

router = APIRouter()


# Aether's Rationale:
# Using FastAPI's dependency injection system is the standard for managing
# dependencies like database connections or external service clients. It makes
# the application more modular, easier to test (by overriding dependencies),
# and aligns with FastAPI best practices.


# These functions act as dependency providers.
def get_state_store() -> StateStore:
    """Dependency to get the application's state store."""
    try:
        return RedisStore()
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to Redis: {e}",
        ) from e


def get_streamer_service() -> StreamerService:
    """Dependency to get the streamer service."""
    return StreamerService()


def get_agent_adapter(request: GeneratePRDRequest) -> BaseAdapter:
    """Selects and instantiates the correct agent adapter based on the request."""
    adapter_type = request.adapter
    if adapter_type in ("vanilla_openai", "vanilla_google"):
        vanilla_adapter_type = cast(
            "Literal['vanilla_openai', 'vanilla_google']", adapter_type
        )
        try:
            return VanillaAdapter(adapter_type=vanilla_adapter_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
    if adapter_type == "crewai":
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
    request: GeneratePRDRequest,
    background_tasks: BackgroundTasks,
    state_store: Annotated[StateStore, Depends(get_state_store)],
    streamer_service: Annotated[StreamerService, Depends(get_streamer_service)],
    agent_adapter: Annotated[BaseAdapter, Depends(get_agent_adapter)],
) -> GeneratePRDResponse:
    """
    Initiates a new agentic workflow to generate a PRD.
    """
    run_id = str(uuid.uuid4())
    initial_state = PRDState(
        run_id=run_id,
        step="Outline",
        content=f"# PRD for {request.idea}\n\n*Initial state.*",
        revision=0,
    )
    state_store.save(initial_state)

    # Kick off the actual generation pipeline in the background.
    background_tasks.add_task(
        run_pipeline,
        initial_state=initial_state,
        state_store=state_store,
        adapter=agent_adapter,
        streamer=streamer_service,
    )

    return GeneratePRDResponse(run_id=run_id)


@router.get(
    "/stream/{run_id}",
    summary="Stream PRD state updates via Server-Sent Events (SSE)",
)
async def stream_prd(
    run_id: str,
    streamer_service: Annotated[StreamerService, Depends(get_streamer_service)],
) -> EventSourceResponse:
    """Establish an SSE connection for the given run ID."""
    # Aether's Rationale:
    # The streamer service needs to be a singleton or managed by a robust
    # dependency injection system to handle multiple concurrent streams.
    # For this project's scope, instantiating it per-request is acceptable,
    # but in a larger-scale app, we would manage its lifecycle carefully.
    return await streamer_service.create_event_stream(run_id)
