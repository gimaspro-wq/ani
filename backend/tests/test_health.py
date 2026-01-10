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


def test_ready_endpoint_reports_dependencies(client: TestClient):
    """Readiness should fail when Redis is not reachable."""
    response = client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert "checks" in data
    assert data["checks"].get("database") is True
    assert data["checks"].get("redis") is False
