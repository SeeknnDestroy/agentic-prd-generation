"""API routes for PRD and Tech Spec generation workflows."""

from collections.abc import AsyncIterator
import json
from typing import Annotated
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from backend.agents.base_adapter import BaseAdapter
from backend.dependencies import (
    get_agent_adapter,
    get_state_store,
    get_streamer_service,
)
from backend.models import GeneratePRDRequest, GeneratePRDResponse, PRDState
from backend.pipelines.pipeline_runner import run_pipeline
from backend.services.streamer import StreamerService
from backend.state.base import StateStore

router = APIRouter()


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
        idea=request.idea,
        step="Outline",
        content=f"# PRD for {request.idea}\n\n_Starting outline generation..._",
        revision=0,
        error=None,
    )
    await state_store.save(initial_state)

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
    state_store: Annotated[StateStore, Depends(get_state_store)],
    streamer_service: Annotated[StreamerService, Depends(get_streamer_service)],
) -> EventSourceResponse:
    """Establish an SSE connection for the given run ID."""
    queue = await streamer_service.add_subscriber(run_id)
    latest_state = await state_store.get(run_id)
    if latest_state is None:
        await streamer_service.remove_subscriber(run_id, queue)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No PRD run found for run_id '{run_id}'.",
        )

    async def event_publisher() -> AsyncIterator[dict[str, str]]:
        last_revision = latest_state.revision
        try:
            yield _to_sse_message(latest_state.to_event_payload())
            while True:
                payload = await queue.get()
                revision = int(payload.get("revision", last_revision))
                if revision <= last_revision and payload.get("step") != "Error":
                    continue
                last_revision = max(last_revision, revision)
                yield _to_sse_message(payload)
        finally:
            await streamer_service.remove_subscriber(run_id, queue)

    return EventSourceResponse(event_publisher())


def _to_sse_message(payload: dict[str, object]) -> dict[str, str]:
    """Serialize a state payload into an SSE message."""
    return {"event": "message", "data": json.dumps(payload)}
