import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.schemas.user import UserCreate

def test_create_user(client: TestClient):
    """Test creating a new user"""
    user_data = {
        "phone_number": "+6281234567890",
        "name": "Test User",
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123"
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data

def test_get_users(client: TestClient):
    """Test getting all users"""
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_user(client: TestClient):
    """Test getting a specific user"""
    # First create a user
    user_data = {
        "phone_number": "+6281234567891",
        "name": "Test User 2",
        "email": "test2@example.com",
        "username": "testuser2",
        "password": "TestPassword123"
    }
    create_response = client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]
    
    # Then get the user
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == user_data["email"] 