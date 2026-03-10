"""Integration tests for generation and streaming."""

import asyncio
import json
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sse_starlette.sse import EventSourceResponse

from backend.routes.generation import stream_prd

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


async def _read_first_sse_event(
    response: EventSourceResponse,
) -> dict[str, object]:
    """Read the first payload from an SSE response body iterator."""
    iterator = cast("AsyncIterator[dict[str, object]]", response.body_iterator)
    message = await anext(iterator)
    data = cast("str", message["data"])
    return cast("dict[str, object]", json.loads(data))


async def _stream_is_exhausted(response: EventSourceResponse) -> bool:
    """Return whether the SSE body iterator terminates after the first event."""
    iterator = cast("AsyncIterator[dict[str, object]]", response.body_iterator)
    try:
        await anext(iterator)
    except StopAsyncIteration:
        return True
    return False


@patch("backend.routes.generation.run_pipeline", new_callable=AsyncMock)
def test_generate_prd_stream_replays_latest_state(
    mock_run_pipeline: AsyncMock,
    client: TestClient,
) -> None:
    """A subscriber should immediately receive the latest persisted run state."""
    response = client.post(
        "/api/v1/generate_prd",
        json={"idea": "A PRD assistant", "adapter": "vanilla_openai"},
    )
    assert response.status_code == 201

    run_id = response.json()["run_id"]
    runtime = client.app.state.runtime  # type: ignore[attr-defined]
    stream_response = asyncio.run(
        stream_prd(run_id, runtime.state_store, runtime.streamer)
    )
    payload = asyncio.run(_read_first_sse_event(stream_response))

    assert payload["run_id"] == run_id
    assert payload["step"] == "Outline"
    assert payload["error"] is None
    mock_run_pipeline.assert_awaited_once()


@patch("backend.routes.generation.run_pipeline", new_callable=AsyncMock)
def test_stream_replays_terminal_error_state(
    mock_run_pipeline: AsyncMock,
    client: TestClient,
) -> None:
    """Late subscribers should see terminal error state replay."""
    response = client.post(
        "/api/v1/generate_prd",
        json={"idea": "Broken run", "adapter": "vanilla_openai"},
    )
    run_id = response.json()["run_id"]
    runtime = client.app.state.runtime  # type: ignore[attr-defined]
    latest_state = asyncio.run(runtime.state_store.get(run_id))
    assert latest_state is not None

    asyncio.run(
        runtime.state_store.save(
            latest_state.model_copy(
                update={"step": "Error", "revision": 1, "error": "boom"}
            )
        )
    )
    stream_response = asyncio.run(
        stream_prd(run_id, runtime.state_store, runtime.streamer)
    )
    payload = asyncio.run(_read_first_sse_event(stream_response))

    assert payload["step"] == "Error"
    assert payload["error"] == "boom"
    assert asyncio.run(_stream_is_exhausted(stream_response)) is True
    mock_run_pipeline.assert_awaited_once()
