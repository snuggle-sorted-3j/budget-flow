"""
Integration tests for auth endpoint error paths.
Covers: form login 401, inactive user 403 (form and JSON login).
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient


class TestAuthFormLoginErrors:

    def test_form_login_invalid_password_returns_401(self, client: TestClient):
        """Form-based login with wrong password returns 401."""
        email = f"form-err-{uuid.uuid4().hex[:8]}@test.com"
        client.post("/api/v1/auth/register", json={
            "email": email, "full_name": "User", "password": "GoodPass123!"
        })

        resp = client.post("/api/v1/auth/login", data={
            "username": email, "password": "WrongPass123!"
        })
        assert resp.status_code == 401
        assert "Incorrect" in resp.json()["detail"]

    def test_form_login_inactive_user_returns_403(self, client: TestClient, db):
        """Form-based login with inactive user returns 403."""
        email = f"inactive-form-{uuid.uuid4().hex[:8]}@test.com"
        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email, "full_name": "Inactive", "password": "Pass123!"
        })
        user_id = reg_resp.json()["id"]

        # Deactivate the user directly via DB
        from app.models.user import User
        user = db.get(User, user_id)
        user.is_active = False
        db.commit()

        resp = client.post("/api/v1/auth/login", data={
            "username": email, "password": "Pass123!"
        })
        assert resp.status_code == 403
        assert "Inactive" in resp.json()["detail"]

    def test_json_login_inactive_user_returns_403(self, client: TestClient, db):
        """JSON login with inactive user returns 403."""
        email = f"inactive-json-{uuid.uuid4().hex[:8]}@test.com"
        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email, "full_name": "Inactive", "password": "Pass123!"
        })
        user_id = reg_resp.json()["id"]

        from app.models.user import User
        user = db.get(User, user_id)
        user.is_active = False
        db.commit()

        resp = client.post("/api/v1/auth/login/json", json={
            "email": email, "password": "Pass123!"
        })
        assert resp.status_code == 403
        assert "Inactive" in resp.json()["detail"]
