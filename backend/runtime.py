"""Application runtime resources and lifecycle helpers."""

from dataclasses import dataclass

import structlog

from backend.logging import configure_logging
from backend.services.streamer import StreamerService
from backend.settings import AppSettings
from backend.state.base import StateStore
from backend.state.in_memory_store import InMemoryStore
from backend.state.redis_store import RedisStore

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class AppRuntime:
    """Shared application resources."""

    settings: AppSettings
    state_store: StateStore
    streamer: StreamerService


async def build_runtime(settings: AppSettings) -> AppRuntime:
    """Create shared process-level resources."""
    configure_logging(settings.debug)
    state_store = await _build_state_store(settings)
    streamer = StreamerService()
    logger.info(
        "app_runtime_initialized",
        environment=settings.environment,
        state_backend=state_store.backend_name,
    )
    return AppRuntime(settings=settings, state_store=state_store, streamer=streamer)


async def close_runtime(runtime: AppRuntime) -> None:
    """Release shared resources on shutdown."""
    await runtime.state_store.close()
    logger.info("app_runtime_closed", state_backend=runtime.state_store.backend_name)


async def _build_state_store(settings: AppSettings) -> StateStore:
    """Select a concrete state store based on configuration and availability."""
    if settings.state_backend == "memory":
        return InMemoryStore()

    redis_store = RedisStore(
        redis_url=settings.redis_url,
        ttl_seconds=settings.redis_ttl_seconds,
    )
    redis_ready = await redis_store.ping()
    if redis_ready:
        return redis_store

    if settings.state_backend == "redis":
        await redis_store.close()
        msg = "Redis was selected explicitly but is not reachable."
        raise RuntimeError(msg)

    logger.warning(
        "state_store_fallback",
        requested_backend=settings.state_backend,
        fallback_backend="memory",
        redis_url=settings.redis_url,
    )
    await redis_store.close()
    return InMemoryStore()
