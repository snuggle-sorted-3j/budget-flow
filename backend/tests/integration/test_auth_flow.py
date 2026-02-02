"""
Integration Tests for Authentication Flow

Tests cover:
- User registration (success and duplicate email)
- User login (success and failure cases)
- Protected endpoint access (with and without token)
- Token validation edge cases
"""
import pytest
import uuid
from typing import Dict
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestUserRegistration:
    """Test user registration endpoint."""
    
    def test_register_new_user(self, client: TestClient):
        """Test: Successfully register a new user."""
        email = f"newuser-{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": email,
            "full_name": "New User",
            "password": "SecurePassword123!"
        }
        
        response = client.post("/api/v1/auth/register", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "password" not in data  # Password should never be returned
        assert "password_hash" not in data

    def test_register_duplicate_email(self, client: TestClient):
        """Test: Registration fails for duplicate email."""
        email = f"duplicate-{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": email,
            "full_name": "First User",
            "password": "Password123!"
        }
        
        # First registration
        response1 = client.post("/api/v1/auth/register", json=payload)
        assert response1.status_code == 201
        
        # Duplicate registration
        payload["full_name"] = "Second User"
        response2 = client.post("/api/v1/auth/register", json=payload)
        
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]

    def test_register_invalid_email(self, client: TestClient):
        """Test: Registration fails for invalid email format."""
        payload = {
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "Password123!"
        }
        
        response = client.post("/api/v1/auth/register", json=payload)
        
        assert response.status_code == 422  # Pydantic validation error

    def test_register_missing_fields(self, client: TestClient):
        """Test: Registration fails when required fields missing."""
        # Missing password
        payload = {
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=payload)
        
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoints."""
    
    def test_login_success_form(self, client: TestClient):
        """Test: Successfully login with form data (OAuth2 flow)."""
        # First register
        email = f"login-form-{uuid.uuid4().hex[:8]}@example.com"
        password = "LoginPassword123!"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": "Login User",
            "password": password
        })
        
        # Login with form data
        response = client.post("/api/v1/auth/login", data={
            "username": email,  # OAuth2 uses 'username' field
            "password": password
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_success_json(self, client: TestClient):
        """Test: Successfully login with JSON body."""
        # First register
        email = f"login-json-{uuid.uuid4().hex[:8]}@example.com"
        password = "JsonPassword123!"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": "JSON Login User",
            "password": password
        })
        
        # Login with JSON
        response = client.post("/api/v1/auth/login/json", json={
            "email": email,
            "password": password
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_invalid_password(self, client: TestClient):
        """Test: Login fails with wrong password."""
        email = f"wrongpass-{uuid.uuid4().hex[:8]}@example.com"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": "Test User",
            "password": "CorrectPassword123!"
        })
        
        response = client.post("/api/v1/auth/login/json", json={
            "email": email,
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test: Login fails for non-existent email."""
        response = client.post("/api/v1/auth/login/json", json={
            "email": "nonexistent@example.com",
            "password": "AnyPassword123!"
        })
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


class TestProtectedEndpoints:
    """Test protected endpoint access."""
    
    def test_protected_endpoint_valid_token(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test: Access protected endpoint with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data

    def test_protected_endpoint_no_token(self, client: TestClient):
        """Test: Protected endpoint returns 401 without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

    def test_protected_endpoint_invalid_token(self, client: TestClient):
        """Test: Protected endpoint returns 401 with invalid token."""
        headers = {"Authorization": "Bearer invalid-token-12345"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401

    def test_protected_endpoint_malformed_header(self, client: TestClient):
        """Test: Protected endpoint returns 401 with malformed auth header."""
        # Missing "Bearer " prefix
        headers = {"Authorization": "just-a-token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401

    def test_protected_periods_endpoint(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test: Periods endpoint requires authentication."""
        # With auth
        response_auth = client.get("/api/v1/periods/", headers=auth_headers)
        assert response_auth.status_code == 200
        
        # Without auth
        response_no_auth = client.get("/api/v1/periods/")
        assert response_no_auth.status_code == 401


class TestUserProfile:
    """Test user profile endpoint."""
    
    def test_get_current_user(
        self, client: TestClient, auth_headers: Dict[str, str], test_user
    ):
        """Test: Get current user profile returns correct data."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] is True


class TestTokenValidation:
    """Test token validation edge cases."""
    
    def test_token_works_for_multiple_requests(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test: Same token works for multiple requests."""
        # Make multiple requests with same token
        for _ in range(3):
            response = client.get("/api/v1/auth/me", headers=auth_headers)
            assert response.status_code == 200

    def test_different_users_have_different_tokens(self, client: TestClient):
        """Test: Different users get different tokens."""
        # Create two users
        users = []
        for i in range(2):
            email = f"user{i}-{uuid.uuid4().hex[:8]}@example.com"
            client.post("/api/v1/auth/register", json={
                "email": email,
                "full_name": f"User {i}",
                "password": "Password123!"
            })
            
            login_resp = client.post("/api/v1/auth/login/json", json={
                "email": email,
                "password": "Password123!"
            })
            users.append({
                "email": email,
                "token": login_resp.json()["access_token"]
            })
        
        # Tokens should be different
        assert users[0]["token"] != users[1]["token"]
        
        # Each token should return the correct user
        for user in users:
            headers = {"Authorization": f"Bearer {user['token']}"}
            me_resp = client.get("/api/v1/auth/me", headers=headers)
            assert me_resp.json()["email"] == user["email"]
