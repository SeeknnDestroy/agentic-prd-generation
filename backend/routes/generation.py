"""API routes for PRD and Tech Spec generation workflows."""

import uuid

from fastapi import APIRouter, status

from backend.models import GeneratePRDRequest, GeneratePRDResponse, PRDState
from backend.state.in_memory_store import InMemoryStore

router = APIRouter()

# Aether's Rationale:
# For now, we instantiate the store directly. In a future step, this will be
# managed by a dependency injection system (e.g., FastAPI's `Depends`) to
# make it more testable and configurable.
state_store = InMemoryStore()


@router.post(
    "/generate_prd",
    response_model=GeneratePRDResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new PRD generation run",
)
async def generate_prd(
    request: GeneratePRDRequest,
) -> GeneratePRDResponse:
    """
    Initiates a new agentic workflow to generate a PRD.

    This endpoint accepts a project idea and configuration, creates a unique
    run ID, saves the initial state, and (in the future) will kick off the
    asynchronous generation pipeline.

    Args:
        request: The request body containing the project idea and settings.

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

    # TODO: Kick off the actual generation pipeline in the background.
    return GeneratePRDResponse(run_id=run_id)
