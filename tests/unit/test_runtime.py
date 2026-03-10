"""Unit tests for settings and runtime selection."""

import pytest

from backend.runtime import _build_state_store
from backend.settings import AppSettings
from backend.state.in_memory_store import InMemoryStore
from backend.state.redis_store import RedisStore


def test_settings_parse_env_lists_and_state_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings should parse env-backed JSON and literals correctly."""
    monkeypatch.setenv("STATE_BACKEND", "memory")
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')

    settings = AppSettings()

    assert settings.state_backend == "memory"
    assert settings.cors_origins == ["http://localhost:3000"]


@pytest.mark.asyncio
async def test_runtime_falls_back_to_memory_when_redis_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auto mode falls back cleanly when Redis is unavailable."""
    settings = AppSettings(state_backend="auto")

    async def ping(self: RedisStore) -> bool:
        del self
        return False

    monkeypatch.setattr(RedisStore, "ping", ping)

    store = await _build_state_store(settings)

    assert isinstance(store, InMemoryStore)


@pytest.mark.asyncio
async def test_runtime_raises_when_redis_is_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit Redis mode should fail fast when Redis is unavailable."""
    settings = AppSettings(state_backend="redis")
    closed = False

    async def ping(self: RedisStore) -> bool:
        del self
        return False

    async def close(self: RedisStore) -> None:
        del self
        nonlocal closed
        closed = True

    monkeypatch.setattr(RedisStore, "ping", ping)
    monkeypatch.setattr(RedisStore, "close", close)

    with pytest.raises(RuntimeError, match="Redis was selected explicitly"):
        await _build_state_store(settings)
    assert closed is True
