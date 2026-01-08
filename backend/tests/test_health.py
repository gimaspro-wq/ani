import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test health endpoint returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "version" in data
