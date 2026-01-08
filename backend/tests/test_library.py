"""Tests for library, progress, and history endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_library_item_crud_flow(client: TestClient, test_user_data):
    """Test the complete library item CRUD flow."""
    
    # Register and login
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get empty library
    response = client.get("/api/v1/me/library", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
    
    # Add item to library
    response = client.put(
        "/api/v1/me/library/anime-123?provider=rpc",
        headers=headers,
        json={"status": "watching", "is_favorite": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title_id"] == "anime-123"
    assert data["status"] == "watching"
    assert data["is_favorite"] is True
    assert data["provider"] == "rpc"
    
    # Get library with item
    response = client.get("/api/v1/me/library", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["title_id"] == "anime-123"
    
    # Update item status
    response = client.put(
        "/api/v1/me/library/anime-123?provider=rpc",
        headers=headers,
        json={"status": "completed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["is_favorite"] is True  # Should remain unchanged
    
    # Filter by status
    response = client.get("/api/v1/me/library?status=completed", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    
    response = client.get("/api/v1/me/library?status=watching", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 0
    
    # Filter by favorites
    response = client.get("/api/v1/me/library?favorites=true", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    
    # Delete item
    response = client.delete("/api/v1/me/library/anime-123?provider=rpc", headers=headers)
    assert response.status_code == 200
    
    # Verify deletion
    response = client.get("/api/v1/me/library", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
    
    # Try to delete non-existent item
    response = client.delete("/api/v1/me/library/anime-999?provider=rpc", headers=headers)
    assert response.status_code == 404


def test_progress_tracking(client: TestClient, test_user_data):
    """Test episode progress tracking."""
    
    # Register
    response = client.post("/api/v1/auth/register", json=test_user_data)
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get empty progress
    response = client.get("/api/v1/me/progress", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
    
    # Update progress for episode
    response = client.put(
        "/api/v1/me/progress/episode-1?provider=rpc",
        headers=headers,
        json={
            "title_id": "anime-123",
            "position_seconds": 120.5,
            "duration_seconds": 1440.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["episode_id"] == "episode-1"
    assert data["title_id"] == "anime-123"
    assert data["position_seconds"] == 120.5
    assert data["duration_seconds"] == 1440.0
    
    # Get all progress
    response = client.get("/api/v1/me/progress", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    
    # Filter progress by title
    response = client.get("/api/v1/me/progress?title_id=anime-123", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    
    response = client.get("/api/v1/me/progress?title_id=anime-999", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 0
    
    # Update progress again (should update, not create new)
    response = client.put(
        "/api/v1/me/progress/episode-1?provider=rpc",
        headers=headers,
        json={
            "title_id": "anime-123",
            "position_seconds": 300.0,
            "duration_seconds": 1440.0
        }
    )
    assert response.status_code == 200
    
    # Verify still only one progress entry
    response = client.get("/api/v1/me/progress", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["position_seconds"] == 300.0


def test_watch_history(client: TestClient, test_user_data):
    """Test watch history tracking."""
    
    # Register
    response = client.post("/api/v1/auth/register", json=test_user_data)
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get empty history
    response = client.get("/api/v1/me/history", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
    
    # Update progress (which also adds to history)
    response = client.put(
        "/api/v1/me/progress/episode-1?provider=rpc",
        headers=headers,
        json={
            "title_id": "anime-123",
            "position_seconds": 100.0,
            "duration_seconds": 1440.0
        }
    )
    assert response.status_code == 200
    
    # Check history
    response = client.get("/api/v1/me/history", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["title_id"] == "anime-123"
    assert items[0]["episode_id"] == "episode-1"
    assert items[0]["position_seconds"] == 100.0
    
    # Watch another episode
    response = client.put(
        "/api/v1/me/progress/episode-2?provider=rpc",
        headers=headers,
        json={
            "title_id": "anime-123",
            "position_seconds": 50.0,
            "duration_seconds": 1440.0
        }
    )
    assert response.status_code == 200
    
    # Check history has both entries
    response = client.get("/api/v1/me/history", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    # Should be ordered by most recent first
    assert items[0]["episode_id"] == "episode-2"
    assert items[1]["episode_id"] == "episode-1"
    
    # Test limit parameter
    response = client.get("/api/v1/me/history?limit=1", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1


def test_library_requires_authentication(client: TestClient):
    """Test that library endpoints require authentication."""
    
    # Try to access without token
    response = client.get("/api/v1/me/library")
    assert response.status_code == 403
    
    response = client.put("/api/v1/me/library/anime-123", json={"status": "watching"})
    assert response.status_code == 403
    
    response = client.get("/api/v1/me/progress")
    assert response.status_code == 403
    
    response = client.get("/api/v1/me/history")
    assert response.status_code == 403


def test_multiple_providers(client: TestClient, test_user_data):
    """Test that different providers are isolated."""
    
    # Register
    response = client.post("/api/v1/auth/register", json=test_user_data)
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Add item with rpc provider
    response = client.put(
        "/api/v1/me/library/anime-123?provider=rpc",
        headers=headers,
        json={"status": "watching"}
    )
    assert response.status_code == 200
    
    # Add same title with different provider
    response = client.put(
        "/api/v1/me/library/anime-123?provider=aniliberty",
        headers=headers,
        json={"status": "completed"}
    )
    assert response.status_code == 200
    
    # Get library for rpc provider
    response = client.get("/api/v1/me/library?provider=rpc", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["status"] == "watching"
    
    # Get library for aniliberty provider
    response = client.get("/api/v1/me/library?provider=aniliberty", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["status"] == "completed"
