"""API routes for PRD and Tech Spec generation workflows."""
import uuid

from fastapi import APIRouter, status

from backend.models import GeneratePRDRequest, GeneratePRDResponse

router = APIRouter()


@router.post(
    "/generate_prd",
    response_model=GeneratePRDResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new PRD generation run",
)
async def generate_prd(
    request: GeneratePRDRequest,  # noqa: F841
) -> GeneratePRDResponse:
    """
    Initiates a new agentic workflow to generate a PRD.

    This endpoint accepts a project idea and configuration, creates a unique
    run ID, and (in the future) will kick off the asynchronous generation
    pipeline.

    Args:
        request: The request body containing the project idea and settings.

    Returns:
        The response containing the unique ID for this generation run.
    """
    run_id = str(uuid.uuid4())
    # TODO: Kick off the actual generation pipeline in the background.
    return GeneratePRDResponse(run_id=run_id)
