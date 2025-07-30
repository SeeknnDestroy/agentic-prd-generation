"""Unit tests for the generation API endpoints."""
import uuid

import pytest
from fastapi.testclient import TestClient


def is_valid_uuid(val: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def test_generate_prd_success(client: TestClient) -> None:
    """
    Test that the /generate_prd endpoint returns a 201 status and a valid
    run_id for a correct request.
    """
    response = client.post(
        "/api/v1/generate_prd",
        json={"idea": "A new project management tool"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "run_id" in data
    assert is_valid_uuid(data["run_id"])


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
