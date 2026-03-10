"""Main FastAPI application entry point."""

import argparse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.routes.generation import router as generation_router
from backend.routes.health import router as health_router
from backend.runtime import build_runtime, close_runtime
from backend.settings import AppSettings


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Create a configured FastAPI application."""
    app_settings = settings or AppSettings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        runtime = await build_runtime(app_settings)
        app.state.runtime = runtime
        yield
        await close_runtime(runtime)

    app = FastAPI(
        title=app_settings.app_name,
        description="AI-powered platform for iterative PRD generation.",
        version=app_settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="", tags=["health"])
    app.include_router(generation_router, prefix="/api/v1", tags=["generation"])
    return app


DEFAULT_SETTINGS = AppSettings()
app = create_app(DEFAULT_SETTINGS)


def cli(argv: list[str] | None = None) -> int:
    """Run the API server from the installed console script."""
    parser = argparse.ArgumentParser(description="Run the Agentic PRD API server.")
    parser.add_argument("--host", default=DEFAULT_SETTINGS.api_host)
    parser.add_argument("--port", type=int, default=DEFAULT_SETTINGS.api_port)
    parser.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_SETTINGS.environment == "development",
    )
    args = parser.parse_args(argv)
    uvicorn.run(
        "backend.main:app",
        host=args.host,  # nosec B104
        port=args.port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
