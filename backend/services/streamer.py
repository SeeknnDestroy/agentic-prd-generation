"""Service for streaming state updates to the frontend via SSE."""

import asyncio
from typing import Any

from sse_starlette.sse import EventSourceResponse


class StreamerService:
    """
    Manages SSE connections and streams data to clients.
    """

    def __init__(self) -> None:
        self.queues: dict[str, asyncio.Queue] = {}

    async def create_event_stream(self, run_id: str) -> EventSourceResponse:
        """
        Creates a new event stream for a given run ID.
        """
        if run_id not in self.queues:
            self.queues[run_id] = asyncio.Queue()

        async def event_publisher() -> Any:
            try:
                while True:
                    data = await self.queues[run_id].get()
                    yield data
            except asyncio.CancelledError:
                # Clean up the queue when the client disconnects
                del self.queues[run_id]

        return EventSourceResponse(event_publisher())

    async def push_data(self, run_id: str, data: Any) -> None:
        """
        Pushes data to the appropriate stream.
        """
        if run_id in self.queues:
            await self.queues[run_id].put({"data": data})
