"""State manager for reading and writing PRD state to Redis."""

import os

import redis

from backend.models import PRDState
from backend.state.base import StateStore


class RedisStore(StateStore):
    """
    A state store that persists PRDState in a Redis database.
    """

    _client: redis.Redis

    def __init__(self, redis_url: str | None = None):
        """
        Initializes the Redis client.

        Args:
            redis_url: The connection URL for Redis. Defaults to the
                       REDIS_URL environment variable or a local instance.
        """
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if not url:
            raise ValueError("Redis URL not provided.")
        self._client = redis.from_url(url, decode_responses=True)
        try:
            self._client.ping()
        except redis.exceptions.ConnectionError as e:
            raise ConnectionError("Could not connect to Redis.") from e

    def _get_key(self, run_id: str) -> str:
        """Generates the Redis key for a given run ID."""
        return f"prd_state:{run_id}"

    def save(self, state: PRDState) -> None:
        """
        Saves the PRD state to Redis as a JSON string.

        The state is stored with a TTL of 7 days.
        """
        key = self._get_key(state.run_id)
        # Pydantic's model_dump_json is used for serialization
        self._client.set(key, state.model_dump_json(), ex=60 * 60 * 24 * 7)

    def get(self, run_id: str) -> PRDState | None:
        """
        Retrieves a PRD state from Redis by its run ID.
        """
        key = self._get_key(run_id)
        data = self._client.get(key)
        if not data:
            return None
        # Pydantic's parse_raw is used for deserialization
        return PRDState.parse_raw(data)
