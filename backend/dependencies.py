"""FastAPI dependency providers backed by shared app runtime state."""

from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status

from backend.agents.base_adapter import BaseAdapter
from backend.agents.vanilla import VanillaAdapter
from backend.models import GeneratePRDRequest
from backend.runtime import AppRuntime
from backend.services.streamer import StreamerService
from backend.settings import AppSettings
from backend.state.base import StateStore


def get_runtime(request: Request) -> AppRuntime:
    """Return the process-level runtime container."""
    return cast("AppRuntime", request.app.state.runtime)


def get_settings(runtime: Annotated[AppRuntime, Depends(get_runtime)]) -> AppSettings:
    """Return application settings."""
    return runtime.settings


def get_state_store(
    runtime: Annotated[AppRuntime, Depends(get_runtime)],
) -> StateStore:
    """Return the shared state store."""
    return runtime.state_store


def get_streamer_service(
    runtime: Annotated[AppRuntime, Depends(get_runtime)],
) -> StreamerService:
    """Return the shared streamer service."""
    return runtime.streamer


def get_agent_adapter(
    request: GeneratePRDRequest,
    settings: Annotated[AppSettings, Depends(get_settings)],
) -> BaseAdapter:
    """Instantiate the selected LLM adapter."""
    try:
        return VanillaAdapter(
            adapter_type=request.adapter,
            openai_api_key=settings.openai_api_key,
            google_api_key=settings.google_api_key,
            openai_model=settings.openai_model,
            google_model=settings.google_model,
            temperature=settings.default_temperature,
            max_output_tokens=settings.max_output_tokens,
            request_timeout_seconds=settings.request_timeout_seconds,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
