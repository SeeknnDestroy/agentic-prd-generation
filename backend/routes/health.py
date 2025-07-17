"""Health check endpoints for monitoring and Docker health checks."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "agentic-prd-generation"}


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Agentic PRD Generation API",
        "version": "0.1.0",
        "docs": "/docs",
    } 