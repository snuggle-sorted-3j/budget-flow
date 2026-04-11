"""
Integration tests for /api/v1/settings endpoints.
Covers: GET 404 (no settings), GET 200, PUT 200, PUT 404 (no currency on create).
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient


class TestGetSettings:

    def test_get_settings_not_found_returns_404(self, client: TestClient, auth_headers: Dict):
        """GET settings for user with no settings returns 404."""
        resp = client.get("/api/v1/settings/", headers=auth_headers)
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_get_settings_returns_200_after_put(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """GET settings after PUT returns 200 with settings data."""
        client.put("/api/v1/settings/", json={
            "default_currency_id": str(test_currency.id),
            "tax_system": "NONE"
        }, headers=auth_headers)

        resp = client.get("/api/v1/settings/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["tax_system"] == "NONE"


class TestUpdateSettings:

    def test_put_settings_no_currency_no_existing_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """PUT settings without default_currency_id when no settings exist returns 404."""
        resp = client.put("/api/v1/settings/", json={
            "tax_system": "NONE"
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_put_settings_creates_successfully(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """PUT settings with default_currency_id creates settings and returns 200."""
        resp = client.put("/api/v1/settings/", json={
            "default_currency_id": str(test_currency.id),
            "tax_system": "NONE"
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["tax_system"] == "NONE"
        assert str(data["default_currency_id"]) == str(test_currency.id)

    def test_put_settings_updates_existing(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """PUT settings with existing settings updates and returns 200."""
        client.put("/api/v1/settings/", json={
            "default_currency_id": str(test_currency.id),
            "tax_system": "NONE"
        }, headers=auth_headers)

        resp = client.put("/api/v1/settings/", json={
            "tax_system": "POLISH_B2B",
            "tax_rate": "19.00"
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["tax_system"] == "POLISH_B2B"
