"""Unit tests for the generation API endpoints."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch
import uuid

from fastapi.testclient import TestClient
import pytest

from backend.agents.base_adapter import BaseAdapter
from backend.main import app
from backend.models import PRDState
from backend.routes.generation import get_agent_adapter, get_state_store
from backend.state.base import StateStore


def is_valid_uuid(val: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


@pytest.fixture
def client_with_mocks(
    client: TestClient,
) -> Generator[tuple[TestClient, MagicMock, MagicMock], None, None]:
    """
    Pytest fixture to provide a TestClient with mocked dependencies for
    the generation routes. It also handles cleanup of dependency overrides.
    """
    mock_state_store = MagicMock(spec=StateStore)
    mock_agent_adapter = MagicMock(spec=BaseAdapter)
    mock_agent_adapter.call_llm.return_value = "Mocked LLM response"

    app.dependency_overrides[get_state_store] = lambda: mock_state_store
    app.dependency_overrides[get_agent_adapter] = lambda: mock_agent_adapter

    yield client, mock_state_store, mock_agent_adapter

    # Clean up the overrides after the test
    app.dependency_overrides = {}


@patch("backend.routes.generation.run_pipeline")
def test_generate_prd_success(
    mock_run_pipeline: MagicMock,
    client_with_mocks: tuple[TestClient, MagicMock, MagicMock],
) -> None:
    """
    Test that the /generate_prd endpoint returns a 201 status, a valid
    run_id, and correctly saves the initial state. The pipeline itself is mocked.
    """
    client, mock_state_store, _ = client_with_mocks
    idea = "A new project management tool"

    response = client.post(
        "/api/v1/generate_prd",
        json={"idea": idea, "adapter": "vanilla_openai"},
    )

    assert response.status_code == 201
    data = response.json()
    run_id = data["run_id"]
    assert is_valid_uuid(run_id)

    # Verify that the state store's save method was called once for the initial state
    mock_state_store.save.assert_called_once()
    saved_state = mock_state_store.save.call_args[0][0]
    assert isinstance(saved_state, PRDState)
    assert saved_state.run_id == run_id
    assert saved_state.step == "Outline"

    # Verify that the pipeline was called in the background
    mock_run_pipeline.assert_called_once()


def test_generate_prd_for_unimplemented_adapter(client: TestClient) -> None:
    """
    Test that requesting an adapter that is not yet implemented returns a
    501 Not Implemented error.
    """
    # Ensure no overrides from other tests are present
    app.dependency_overrides = {}
    response = client.post(
        "/api/v1/generate_prd",
        json={
            "idea": "A new social media platform for cats",
            "adapter": "crewai",
        },
    )
    assert response.status_code == 501
    data = response.json()
    assert "adapter is not yet available" in data["detail"]


@pytest.mark.parametrize(
    "payload, expected_msg",
    [
        ({}, "Field required"),
        ({"idea": ""}, "String should have at least 1 character"),
        (
            {"idea": "Valid idea", "autonomy_level": "Invalid"},
            "Input should be 'Full' or 'Supervised'",
        ),
        (
            {"idea": "Valid idea", "adapter": "invalid_adapter"},
            "Input should be 'vanilla_openai', 'vanilla_google' or 'crewai'",
        ),
    ],
)
def test_generate_prd_validation_errors(
    client: TestClient, payload: dict, expected_msg: str
) -> None:
    """
    Test that the endpoint returns a 422 status code for various
    invalid request payloads.
    """
    response = client.post("/api/v1/generate_prd", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert expected_msg in str(data["detail"])
