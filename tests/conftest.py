"""Pytest configuration and shared fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator

from fastapi.testclient import TestClient
import pytest

from backend.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[TestClient, None]:
    """Async FastAPI test client."""
    async with TestClient(app) as client:
        yield client
