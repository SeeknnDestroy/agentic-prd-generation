"""Pytest configuration and shared fixtures."""

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.main import create_app
from backend.settings import AppSettings


@pytest.fixture(scope="session")
def test_settings() -> AppSettings:
    """Stable settings for local tests."""
    return AppSettings(
        environment="test",
        debug=True,
        state_backend="memory",
        openai_api_key="test-openai-key",
        google_api_key="test-google-key",
    )


@pytest.fixture
def app(test_settings: AppSettings) -> FastAPI:
    """Create a fresh FastAPI app for each test."""
    return create_app(test_settings)


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """FastAPI test client with lifespan support enabled."""
    with TestClient(app) as test_client:
        yield test_client
