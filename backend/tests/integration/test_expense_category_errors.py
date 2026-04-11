"""
Integration tests for expense category error paths.
Covers: create with invalid parent 400, update paths (invalid parent 400, not found 404),
delete not found 404.
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient


def _create_category(client, headers, name="TestCat"):
    resp = client.post("/api/v1/expense-categories/", json={
        "category_name": name,
        "icon": "T"
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()


class TestCreateCategoryErrors:

    def test_create_category_invalid_parent_returns_400(
        self, client: TestClient, auth_headers: Dict
    ):
        """Create category with non-existent parent_category_id returns 400."""
        resp = client.post("/api/v1/expense-categories/", json={
            "category_name": "Child",
            "parent_category_id": str(uuid.uuid4())
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "parent" in resp.json()["detail"].lower()


class TestUpdateCategoryErrors:

    def test_update_category_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """PATCH non-existent category returns 404."""
        resp = client.patch(
            f"/api/v1/expense-categories/{uuid.uuid4()}",
            json={"category_name": "New Name"},
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_update_category_invalid_parent_returns_400(
        self, client: TestClient, auth_headers: Dict
    ):
        """PATCH category with non-existent parent_category_id returns 400."""
        cat = _create_category(client, auth_headers, "UpdateTest")
        resp = client.patch(
            f"/api/v1/expense-categories/{cat['id']}",
            json={"parent_category_id": str(uuid.uuid4())},
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "parent" in resp.json()["detail"].lower()

    def test_update_category_success(
        self, client: TestClient, auth_headers: Dict
    ):
        """PATCH category with valid data returns 200."""
        cat = _create_category(client, auth_headers, "BeforeUpdate")
        resp = client.patch(
            f"/api/v1/expense-categories/{cat['id']}",
            json={"category_name": "AfterUpdate"},
            headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["category_name"] == "AfterUpdate"

    def test_update_category_with_valid_parent(
        self, client: TestClient, auth_headers: Dict
    ):
        """PATCH category with valid parent_category_id returns 200."""
        parent = _create_category(client, auth_headers, "ParentCat")
        child = _create_category(client, auth_headers, "ChildCat")

        resp = client.patch(
            f"/api/v1/expense-categories/{child['id']}",
            json={"parent_category_id": parent["id"]},
            headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["parent_category_id"] == parent["id"]


class TestDeleteCategoryErrors:

    def test_delete_category_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """DELETE non-existent category returns 404."""
        resp = client.delete(
            f"/api/v1/expense-categories/{uuid.uuid4()}",
            headers=auth_headers
        )
        assert resp.status_code == 404
