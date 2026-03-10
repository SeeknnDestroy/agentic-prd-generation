"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from backend.dependencies import get_runtime
from backend.runtime import AppRuntime

router = APIRouter()


@router.get("/health")
async def health_check(
    runtime: AppRuntime = Depends(get_runtime),
) -> dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "agentic-prd-generation",
        "version": runtime.settings.app_version,
    }


@router.get("/ready")
async def readiness_check(
    runtime: AppRuntime = Depends(get_runtime),
) -> JSONResponse:
    """Readiness check for the selected state backend."""
    ready = await runtime.state_store.ping()
    status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    payload = {
        "status": "ready" if ready else "not_ready",
        "state_backend": runtime.state_store.backend_name,
    }
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/")
async def root(request: Request) -> dict[str, str]:
    """Root endpoint with API information."""
    runtime: AppRuntime = request.app.state.runtime
    return {
        "message": "Agentic PRD Generation API",
        "version": runtime.settings.app_version,
        "docs": "/docs",
        "ready": "/ready",
    }
