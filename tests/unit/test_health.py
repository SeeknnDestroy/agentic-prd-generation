"""Unit tests for health endpoints."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """`/health` reports liveness."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "agentic-prd-generation"


def test_readiness_check(client: TestClient) -> None:
    """`/ready` reports the selected state backend."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "state_backend": "memory"}


def test_root_endpoint(client: TestClient) -> None:
    """The root endpoint exposes basic API metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Agentic PRD Generation API"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"
    assert data["ready"] == "/ready"
