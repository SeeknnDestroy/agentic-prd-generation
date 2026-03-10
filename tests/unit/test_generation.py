"""Unit tests for the generation API endpoints."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.agents.base_adapter import BaseAdapter
from backend.dependencies import get_agent_adapter, get_state_store
from backend.models import PRDState
from backend.state.base import StateStore


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


@pytest.fixture
def client_with_mocks(
    app: FastAPI,
    client: TestClient,
) -> Generator[tuple[TestClient, MagicMock, MagicMock], None, None]:
    """Provide a client with mocked generation dependencies."""
    mock_state_store = MagicMock(spec=StateStore)
    mock_agent_adapter = MagicMock(spec=BaseAdapter)

    app.dependency_overrides[get_state_store] = lambda: mock_state_store
    app.dependency_overrides[get_agent_adapter] = lambda: mock_agent_adapter

    yield client, mock_state_store, mock_agent_adapter

    app.dependency_overrides = {}


@patch("backend.routes.generation.run_pipeline", new_callable=AsyncMock)
def test_generate_prd_success(
    mock_run_pipeline: AsyncMock,
    client_with_mocks: tuple[TestClient, MagicMock, MagicMock],
) -> None:
    """`POST /generate_prd` returns a run id and saves the initial state."""
    client, mock_state_store, _ = client_with_mocks

    response = client.post(
        "/api/v1/generate_prd",
        json={"idea": "A new project management tool", "adapter": "vanilla_openai"},
    )

    assert response.status_code == 201
    run_id = response.json()["run_id"]
    assert is_valid_uuid(run_id)

    mock_state_store.save.assert_called_once()
    saved_state = mock_state_store.save.call_args.args[0]
    assert isinstance(saved_state, PRDState)
    assert saved_state.run_id == run_id
    assert saved_state.idea == "A new project management tool"
    assert saved_state.step == "Outline"
    assert saved_state.error is None

    mock_run_pipeline.assert_awaited_once()


def test_generate_prd_validation_errors(
    client: TestClient,
) -> None:
    """The route validates the narrowed request contract."""
    response = client.post("/api/v1/generate_prd", json={})
    assert response.status_code == 422
    assert "Field required" in str(response.json()["detail"])

    response = client.post(
        "/api/v1/generate_prd", json={"idea": "", "adapter": "vanilla_openai"}
    )
    assert response.status_code == 422
    assert "at least 1 character" in str(response.json()["detail"])

    response = client.post(
        "/api/v1/generate_prd",
        json={"idea": "Valid idea", "adapter": "invalid_adapter"},
    )
    assert response.status_code == 422
    assert "vanilla_openai" in str(response.json()["detail"])
    assert "vanilla_google" in str(response.json()["detail"])
