"""Unit tests for the shared streamer service."""

import asyncio

import pytest

from backend.services.streamer import StreamerService


@pytest.mark.asyncio
async def test_streamer_broadcasts_to_multiple_subscribers() -> None:
    """All subscribers for a run should receive the same payload."""
    streamer = StreamerService()
    queue_one = await streamer.add_subscriber("run-1")
    queue_two = await streamer.add_subscriber("run-1")

    await streamer.publish("run-1", {"revision": 1, "step": "Outline"})

    assert await asyncio.wait_for(queue_one.get(), timeout=1) == {
        "revision": 1,
        "step": "Outline",
    }
    assert await asyncio.wait_for(queue_two.get(), timeout=1) == {
        "revision": 1,
        "step": "Outline",
    }


@pytest.mark.asyncio
async def test_streamer_cleans_up_subscribers() -> None:
    """Removing the last subscriber clears the internal run registry."""
    streamer = StreamerService()
    queue = await streamer.add_subscriber("run-2")

    await streamer.remove_subscriber("run-2", queue)

    assert "run-2" not in streamer._queues
