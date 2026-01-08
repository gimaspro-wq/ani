import pytest
from fastapi.testclient import TestClient


def test_register_login_me_flow(client: TestClient, test_user_data):
    """Test the complete flow: register -> login -> get user info."""
    
    # 1. Register a new user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in response.cookies
    
    access_token = data["access_token"]
    
    # 2. Get current user info with access token
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == test_user_data["email"]
    assert "id" in user_data
    assert user_data["is_active"] is True


def test_register_duplicate_email(client: TestClient, test_user_data):
    """Test that registering with duplicate email fails."""
    
    # Register first user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    
    # Try to register again with same email
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_with_valid_credentials(client: TestClient, test_user_data):
    """Test login with valid credentials."""
    
    # Register user first
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login
    response = client.post("/api/v1/auth/login", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in response.cookies


def test_login_with_invalid_credentials(client: TestClient, test_user_data):
    """Test login with invalid credentials."""
    
    # Register user first
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Try to login with wrong password
    response = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user."""
    
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "somepassword"
    })
    assert response.status_code == 401


def test_refresh_token_flow(client: TestClient, test_user_data):
    """Test refresh token flow: register -> refresh -> get user info."""
    
    # 1. Register user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    old_access_token = response.json()["access_token"]
    refresh_cookie = response.cookies.get("refresh_token")
    
    # 2. Refresh token (pass cookie explicitly for TestClient)
    response = client.post("/api/v1/auth/refresh", cookies={"refresh_token": refresh_cookie})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    new_access_token = data["access_token"]
    
    # Tokens should be different (new token issued)
    assert new_access_token != old_access_token
    
    # 3. Use new access token to get user info
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == test_user_data["email"]


def test_refresh_without_token(client: TestClient):
    """Test refresh without refresh token fails."""
    
    # Create a client without cookies
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_logout_flow(client: TestClient, test_user_data):
    """Test logout flow: register -> logout -> refresh fails."""
    
    # 1. Register user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    assert "refresh_token" in response.cookies
    
    # 2. Logout
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
    
    # 3. Try to refresh (should fail because token was revoked)
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_get_user_without_token(client: TestClient):
    """Test getting user info without access token fails."""
    
    response = client.get("/api/v1/users/me")
    assert response.status_code == 403  # Missing authorization header


def test_get_user_with_invalid_token(client: TestClient):
    """Test getting user info with invalid access token fails."""
    
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401
