import pytest

pytestmark = pytest.mark.integration

from fastapi.testclient import TestClient
from app.models.user import User
from app.models.currency import Currency
from decimal import Decimal
import uuid

def test_health_check(client: TestClient):
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_version_check(client: TestClient):
    response = client.get("/api/v1/system/version")
    assert response.status_code == 200
    assert "version" in response.json()
    assert "environment" in response.json()

def test_create_period_api(client: TestClient, auth_headers: dict):
    payload = {
        "period_name": "API Period",
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "snapshot_date": "2026-01-31"
    }
    response = client.post("/api/v1/periods/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["period_name"] == "API Period"

def test_create_period_invalid_date(client: TestClient, auth_headers: dict):
    # snapshot_date != end_date should fail (pydantic validator)
    payload = {
        "period_name": "Invalid Period",
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "snapshot_date": "2026-02-01"
    }
    response = client.post("/api/v1/periods/", json=payload, headers=auth_headers)
    assert response.status_code == 422

def test_accounts_and_snapshots_flow(client: TestClient, auth_headers: dict, test_currency: Currency):
    # 1. Create Account
    acc_payload = {
        "account_name": "API Savings",
        "account_type": "BANK",
        "currency_id": str(test_currency.id)
    }
    acc_resp = client.post("/api/v1/accounts/", json=acc_payload, headers=auth_headers)
    assert acc_resp.status_code == 201
    account_id = acc_resp.json()["id"]

    # 2. Create Period
    period_payload = {
        "period_name": "Flow Period",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "snapshot_date": "2026-03-31"
    }
    period_resp = client.post("/api/v1/periods/", json=period_payload, headers=auth_headers)
    assert period_resp.status_code == 201
    period_id = period_resp.json()["id"]

    # 3. Create Bulk Snapshots
    snap_payload = [
        {
            "account_id": account_id,
            "balance": 2500.00
        }
    ]
    snap_resp = client.post(f"/api/v1/periods/{period_id}/snapshots", json=snap_payload, headers=auth_headers)
    assert snap_resp.status_code == 200
    assert len(snap_resp.json()) == 1
    assert float(snap_resp.json()[0]["balance"]) == 2500.00

    # 4. Get Snapshots
    get_snap_resp = client.get(f"/api/v1/periods/{period_id}/snapshots", headers=auth_headers)
    assert get_snap_resp.status_code == 200
    assert len(get_snap_resp.json()) == 1

def test_unauthenticated_access(client: TestClient):
    response = client.get("/api/v1/periods/")
    assert response.status_code == 401
