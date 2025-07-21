"""
Main FastAPI application entry point.

This module sets up the FastAPI application with all routes, middleware,
and configuration for the Agentic PRD Generation platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.health import router as health_router

# Create FastAPI app
app = FastAPI(
    title="Agentic PRD Generation API",
    description="AI-powered platform for iterative PRD and Technical Specification generation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="", tags=["health"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
