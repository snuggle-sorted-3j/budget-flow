"""
Integration tests for template endpoint error paths.
Covers: update template 404, delete template 404.
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient


class TestTemplateErrors:

    def test_update_template_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """PATCH non-existent template returns 404."""
        resp = client.patch(
            f"/api/v1/templates/{uuid.uuid4()}",
            json={"template_name": "Renamed"},
            headers=auth_headers
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_delete_template_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """DELETE non-existent template returns 404."""
        resp = client.delete(
            f"/api/v1/templates/{uuid.uuid4()}",
            headers=auth_headers
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()
