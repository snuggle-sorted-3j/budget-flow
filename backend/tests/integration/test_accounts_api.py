"""
Integration tests for /api/v1/accounts endpoints.

Covers:
- Create account: 201, 400 (invalid currency), 400 (duplicate name), 401
- List accounts: 200, 401
- Deactivate account: 200, 404, 401
- Delete account: 200, 404, 400 (has snapshots), 401
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient


def _create_account(client, headers, currency_id, name="TestBank", acct_type="BANK"):
    resp = client.post("/api/v1/accounts/", json={
        "account_name": name,
        "account_type": acct_type,
        "currency_id": str(currency_id),
        "opening_balance": "0.00"
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Create Account
# ---------------------------------------------------------------------------

class TestCreateAccount:

    def test_create_account_success(self, client: TestClient, auth_headers: Dict, test_currency):
        """Create account returns 201 with correct data."""
        resp = client.post("/api/v1/accounts/", json={
            "account_name": "My Savings",
            "account_type": "BANK",
            "currency_id": str(test_currency.id),
            "opening_balance": "1500.00"
        }, headers=auth_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data["account_name"] == "My Savings"
        assert data["account_type"] == "BANK"
        assert float(data["opening_balance"]) == 1500.0
        assert "id" in data

    def test_create_account_no_auth(self, client: TestClient, test_currency):
        """Create without auth returns 401."""
        resp = client.post("/api/v1/accounts/", json={
            "account_name": "X",
            "account_type": "BANK",
            "currency_id": str(test_currency.id)
        })
        assert resp.status_code == 401

    def test_create_account_invalid_currency(self, client: TestClient, auth_headers: Dict):
        """Create with non-existent currency_id returns 400."""
        resp = client.post("/api/v1/accounts/", json={
            "account_name": "BadCurrency",
            "account_type": "BANK",
            "currency_id": str(uuid.uuid4())
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "currency" in resp.json()["detail"].lower()

    def test_create_account_duplicate_name_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """Create two accounts with same name returns 400 on second."""
        _create_account(client, auth_headers, test_currency.id, "DuplicateName")

        resp = client.post("/api/v1/accounts/", json={
            "account_name": "DuplicateName",
            "account_type": "CASH",
            "currency_id": str(test_currency.id)
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_create_cash_account(self, client: TestClient, auth_headers: Dict, test_currency):
        """CASH account type is valid."""
        resp = client.post("/api/v1/accounts/", json={
            "account_name": "Cash Wallet",
            "account_type": "CASH",
            "currency_id": str(test_currency.id)
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["account_type"] == "CASH"


# ---------------------------------------------------------------------------
# List Accounts
# ---------------------------------------------------------------------------

class TestListAccounts:

    def test_list_accounts_empty(self, client: TestClient, auth_headers: Dict):
        """List returns empty list when no accounts exist."""
        resp = client.get("/api/v1/accounts/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_accounts_returns_own_accounts(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """List returns accounts for authenticated user only."""
        _create_account(client, auth_headers, test_currency.id, "ListAcct1")
        _create_account(client, auth_headers, test_currency.id, "ListAcct2")

        resp = client.get("/api/v1/accounts/", headers=auth_headers)
        assert resp.status_code == 200
        names = [a["account_name"] for a in resp.json()]
        assert "ListAcct1" in names
        assert "ListAcct2" in names

    def test_list_accounts_no_auth(self, client: TestClient):
        """List without auth returns 401."""
        resp = client.get("/api/v1/accounts/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Deactivate Account
# ---------------------------------------------------------------------------

class TestDeactivateAccount:

    def test_deactivate_account_success(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """Deactivate account sets is_active=False and returns 200."""
        acct = _create_account(client, auth_headers, test_currency.id, "ToDeactivate")

        resp = client.patch(
            f"/api/v1/accounts/{acct['id']}/deactivate",
            headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_deactivate_account_not_found(self, client: TestClient, auth_headers: Dict):
        """Deactivate non-existent account returns 404."""
        resp = client.patch(
            f"/api/v1/accounts/{uuid.uuid4()}/deactivate",
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_deactivate_account_no_auth(self, client: TestClient, test_currency):
        """Deactivate without auth returns 401."""
        resp = client.patch(f"/api/v1/accounts/{uuid.uuid4()}/deactivate")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Delete Account
# ---------------------------------------------------------------------------

class TestDeleteAccount:

    def test_delete_account_success(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """Delete account with no snapshots returns 200."""
        acct = _create_account(client, auth_headers, test_currency.id, "ToDelete")

        resp = client.delete(f"/api/v1/accounts/{acct['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

    def test_delete_account_not_found(self, client: TestClient, auth_headers: Dict):
        """Delete non-existent account returns 404."""
        resp = client.delete(f"/api/v1/accounts/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_account_no_auth(self, client: TestClient):
        """Delete without auth returns 401."""
        resp = client.delete(f"/api/v1/accounts/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_delete_account_with_snapshot_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency, test_user, db
    ):
        """Delete account that has balance snapshots returns 400."""
        from datetime import date
        from app.models.balance_snapshot import BalanceSnapshot
        from app.models.calculation_period import CalculationPeriod
        from decimal import Decimal

        acct = _create_account(client, auth_headers, test_currency.id, "SnapAcct")

        period = CalculationPeriod(
            id=uuid.uuid4(),
            user_id=test_user.id,
            period_name="SnapPeriod",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            snapshot_date=date(2026, 3, 31),
            status="FINALIZED"
        )
        db.add(period)
        db.flush()

        snap = BalanceSnapshot(
            id=uuid.uuid4(),
            calculation_period_id=period.id,
            account_id=uuid.UUID(acct["id"]),
            balance=Decimal("500.00"),
            snapshot_date=date(2026, 3, 31)
        )
        db.add(snap)
        db.commit()

        resp = client.delete(f"/api/v1/accounts/{acct['id']}", headers=auth_headers)
        assert resp.status_code == 400
        assert "snapshot" in resp.json()["detail"].lower()
