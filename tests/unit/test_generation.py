"""Unit tests for the generation API endpoints."""

from unittest.mock import patch
import uuid

from fastapi.testclient import TestClient
import pytest

from backend.models import PRDState


def is_valid_uuid(val: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


@patch("backend.routes.generation.state_store")
def test_generate_prd_success(mock_state_store, client: TestClient) -> None:
    """
    Test that the /generate_prd endpoint returns a 201 status, a valid
    run_id, and correctly saves the initial state.
    """
    idea = "A new project management tool"
    response = client.post("/api/v1/generate_prd", json={"idea": idea})

    assert response.status_code == 201
    data = response.json()
    assert "run_id" in data
    run_id = data["run_id"]
    assert is_valid_uuid(run_id)

    # Verify that the state store's save method was called once
    mock_state_store.save.assert_called_once()
    # Get the state object that was passed to the save method
    saved_state = mock_state_store.save.call_args[0][0]

    assert isinstance(saved_state, PRDState)
    assert saved_state.run_id == run_id
    assert saved_state.step == "Outline"
    assert saved_state.revision == 0
    assert f"PRD for {idea}" in saved_state.content


def test_generate_prd_with_all_params(client: TestClient) -> None:
    """
    Test the endpoint with all optional parameters provided.
    """
    response = client.post(
        "/api/v1/generate_prd",
        json={
            "idea": "A new social media platform for cats",
            "autonomy_level": "Supervised",
            "adapter": "crewai",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "run_id" in data
    assert is_valid_uuid(data["run_id"])


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
