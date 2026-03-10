"""Service for streaming state updates to the frontend via SSE."""

import asyncio
from collections import defaultdict
from typing import Any


class StreamerService:
    """
    Manages SSE connections and streams data to clients.
    """

    def __init__(self) -> None:
        self._queues: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def add_subscriber(self, run_id: str) -> asyncio.Queue[dict[str, Any]]:
        """Create and register a subscriber queue for a run."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._queues[run_id].add(queue)
        return queue

    async def remove_subscriber(
        self,
        run_id: str,
        queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        """Remove a subscriber queue for a run."""
        async with self._lock:
            subscribers = self._queues.get(run_id)
            if not subscribers:
                return
            subscribers.discard(queue)
            if not subscribers:
                self._queues.pop(run_id, None)

    async def publish(self, run_id: str, data: dict[str, Any]) -> None:
        """Broadcast a payload to all subscribers for a run."""
        async with self._lock:
            subscribers = list(self._queues.get(run_id, set()))
        for queue in subscribers:
            await queue.put(data)
