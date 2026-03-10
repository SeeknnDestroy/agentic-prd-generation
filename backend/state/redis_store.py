"""State manager for reading and writing PRD state to Redis."""

from inspect import isawaitable

import redis
import redis.asyncio as aredis

from backend.models import PRDState
from backend.state.base import StateStore


class RedisStore(StateStore):
    """
    A state store that persists PRDState in a Redis database.
    """

    _client: aredis.Redis
    backend_name = "redis"

    def __init__(self, redis_url: str, ttl_seconds: int = 60 * 60 * 24 * 7):
        """
        Initializes the Redis client.

        Args:
            redis_url: The connection URL for Redis.
            ttl_seconds: The retention period for saved run state.
        """
        self._client = aredis.from_url(redis_url, decode_responses=True)
        self._ttl_seconds = ttl_seconds

    def _get_key(self, run_id: str) -> str:
        """Generates the Redis key for a given run ID."""
        return f"prd_state:{run_id}"

    async def save(self, state: PRDState) -> None:
        """
        Saves the PRD state to Redis as a JSON string.

        The state is stored with a TTL of 7 days.
        """
        key = self._get_key(state.run_id)
        await self._client.set(key, state.model_dump_json(), ex=self._ttl_seconds)

    async def get(self, run_id: str) -> PRDState | None:
        """
        Retrieves a PRD state from Redis by its run ID.
        """
        key = self._get_key(run_id)
        data = await self._client.get(key)
        if not data:
            return None
        return PRDState.model_validate_json(data)

    async def ping(self) -> bool:
        """Check whether Redis is reachable."""
        try:
            return bool(await self._client.ping())
        except redis.exceptions.RedisError:
            return False

    async def close(self) -> None:
        """Close the Redis client cleanly."""
        async_close = getattr(self._client, "aclose", None)
        if callable(async_close):
            await async_close()
            return

        close_result = self._client.close()
        if isawaitable(close_result):
            await close_result
