"""
Integration tests for /api/v1/periods/{period_id}/snapshots endpoints.
Covers: create 404 (no period), create 400 (no account), read 404 (no period), read 200.
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from app.models.currency import Currency


def _create_period(client, headers):
    resp = client.post("/api/v1/periods/", json={
        "period_name": f"SnapPeriod-{uuid.uuid4().hex[:6]}",
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
        "snapshot_date": "2026-06-30"
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def _create_account(client, headers, currency_id):
    resp = client.post("/api/v1/accounts/", json={
        "account_name": f"SnapAcct-{uuid.uuid4().hex[:6]}",
        "account_type": "BANK",
        "currency_id": str(currency_id),
        "opening_balance": "0.00"
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()


class TestCreateSnapshots:

    def test_create_snapshot_period_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """POST snapshots for non-existent period returns 404."""
        account = _create_account(client, auth_headers, test_currency.id)
        resp = client.post(
            f"/api/v1/periods/{uuid.uuid4()}/snapshots",
            json=[{"account_id": account["id"], "balance": "500.00"}],
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_create_snapshot_account_not_found_returns_400(
        self, client: TestClient, auth_headers: Dict
    ):
        """POST snapshots with non-existent account_id returns 400."""
        period = _create_period(client, auth_headers)
        resp = client.post(
            f"/api/v1/periods/{period['id']}/snapshots",
            json=[{"account_id": str(uuid.uuid4()), "balance": "500.00"}],
            headers=auth_headers
        )
        assert resp.status_code == 400

    def test_create_snapshot_success(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """POST snapshots with valid data returns 200 with list."""
        period = _create_period(client, auth_headers)
        account = _create_account(client, auth_headers, test_currency.id)

        resp = client.post(
            f"/api/v1/periods/{period['id']}/snapshots",
            json=[{"account_id": account["id"], "balance": "1000.00"}],
            headers=auth_headers
        )
        assert resp.status_code == 200
        snapshots = resp.json()
        assert len(snapshots) == 1
        assert float(snapshots[0]["balance"]) == 1000.0


class TestReadSnapshots:

    def test_read_snapshots_period_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """GET snapshots for non-existent period returns 404."""
        resp = client.get(
            f"/api/v1/periods/{uuid.uuid4()}/snapshots",
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_read_snapshots_success(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """GET snapshots for valid period returns list."""
        period = _create_period(client, auth_headers)
        account = _create_account(client, auth_headers, test_currency.id)

        client.post(
            f"/api/v1/periods/{period['id']}/snapshots",
            json=[{"account_id": account["id"], "balance": "250.00"}],
            headers=auth_headers
        )

        resp = client.get(
            f"/api/v1/periods/{period['id']}/snapshots",
            headers=auth_headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1
