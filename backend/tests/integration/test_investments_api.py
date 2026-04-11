"""
Integration tests for /api/v1/investments endpoints.

Covers:
- Investment accounts: create, list, delete (200 + 404 + 403)
- Investments (categories): create, list, delete (200 + 404 + 403)
- Investment transfers: create, list, delete (200 + 404 + 403 + 400 finalized)
- Auth: 401 without token
"""
import uuid
from typing import Dict
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.models.currency import Currency
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_period(client, headers, name="InvPeriod", status_="DRAFT"):
    resp = client.post("/api/v1/periods/", json={
        "period_name": name,
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "snapshot_date": "2026-01-31"
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_account(client, headers, currency_id, name="TestBank"):
    resp = client.post("/api/v1/accounts/", json={
        "account_name": name,
        "account_type": "BANK",
        "currency_id": str(currency_id)
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_inv_account(client, headers, name="MyBrokerage"):
    resp = client.post("/api/v1/investments/accounts", json={
        "account_name": name,
        "account_type": "BROKERAGE",
        "notes": "Test brokerage",
        "is_active": True
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _create_investment(client, headers, name="Stocks"):
    resp = client.post("/api/v1/investments/", json={
        "category_name": name,
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Investment Accounts
# ---------------------------------------------------------------------------

class TestInvestmentAccounts:

    def test_create_investment_account(self, client: TestClient, auth_headers: Dict):
        """Create a new investment account — 200 response with correct data."""
        resp = client.post("/api/v1/investments/accounts", json={
            "account_name": "Crypto Exchange",
            "account_type": "CRYPTO_EXCHANGE",
            "notes": "Binance account",
            "is_active": True
        }, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["account_name"] == "Crypto Exchange"
        assert data["account_type"] == "CRYPTO_EXCHANGE"
        assert "id" in data

    def test_create_investment_account_no_auth(self, client: TestClient):
        """Create without auth returns 401."""
        resp = client.post("/api/v1/investments/accounts", json={
            "account_name": "X", "account_type": "BROKERAGE"
        })
        assert resp.status_code == 401

    def test_list_investment_accounts(self, client: TestClient, auth_headers: Dict):
        """List returns all accounts for authenticated user."""
        _create_inv_account(client, auth_headers, "ListBrokerage1")
        _create_inv_account(client, auth_headers, "ListBrokerage2")

        resp = client.get("/api/v1/investments/accounts", headers=auth_headers)
        assert resp.status_code == 200
        names = [a["account_name"] for a in resp.json()]
        assert "ListBrokerage1" in names
        assert "ListBrokerage2" in names

    def test_list_investment_accounts_no_auth(self, client: TestClient):
        """List without auth returns 401."""
        resp = client.get("/api/v1/investments/accounts")
        assert resp.status_code == 401

    def test_delete_investment_account(self, client: TestClient, auth_headers: Dict):
        """Delete existing account returns 204."""
        acct = _create_inv_account(client, auth_headers, "DeleteMe")
        resp = client.delete(f"/api/v1/investments/accounts/{acct['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_investment_account_not_found(self, client: TestClient, auth_headers: Dict):
        """Delete non-existent account returns 404."""
        resp = client.delete(f"/api/v1/investments/accounts/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_investment_account_wrong_user(
        self, client: TestClient, auth_headers: Dict, db, test_currency
    ):
        """Delete another user's account returns 403."""
        # Create as one user, try to delete as another
        acct = _create_inv_account(client, auth_headers, "OtherUserAcct")

        # Create second user and token
        from app.models.user import User
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"other-{uuid.uuid4()}@example.com",
            password_hash=get_password_hash("pw"),
            full_name="Other",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.delete(
            f"/api/v1/investments/accounts/{acct['id']}",
            headers=other_headers
        )
        assert resp.status_code == 403

    def test_physical_account_type_allowed(self, client: TestClient, auth_headers: Dict):
        """PHYSICAL is a valid account_type."""
        resp = client.post("/api/v1/investments/accounts", json={
            "account_name": "Gold Vault",
            "account_type": "PHYSICAL",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["account_type"] == "PHYSICAL"


# ---------------------------------------------------------------------------
# Investments (Categories)
# ---------------------------------------------------------------------------

class TestInvestments:

    def test_create_investment(self, client: TestClient, auth_headers: Dict):
        """Create investment category — 200 with correct data."""
        resp = client.post("/api/v1/investments/", json={
            "category_name": "SP500 Index"
        }, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["category_name"] == "SP500 Index"
        assert "id" in data

    def test_create_investment_no_auth(self, client: TestClient):
        """Create without auth returns 401."""
        resp = client.post("/api/v1/investments/", json={"category_name": "X"})
        assert resp.status_code == 401

    def test_create_investment_with_account(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """Create investment linked to an investment account."""
        acct = _create_inv_account(client, auth_headers, "LinkedBrokerage")
        resp = client.post("/api/v1/investments/", json={
            "category_name": "ETF Portfolio",
            "investment_account_id": acct["id"],
            "opening_balance": "5000.00",
            "opening_balance_date": "2026-01-01",
            "opening_balance_currency_id": str(test_currency.id)
        }, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["category_name"] == "ETF Portfolio"
        assert data["investment_account_id"] == acct["id"]

    def test_list_investments(self, client: TestClient, auth_headers: Dict):
        """List returns all investments for authenticated user."""
        _create_investment(client, auth_headers, "ListInv1")
        _create_investment(client, auth_headers, "ListInv2")

        resp = client.get("/api/v1/investments/", headers=auth_headers)
        assert resp.status_code == 200
        names = [i["category_name"] for i in resp.json()]
        assert "ListInv1" in names
        assert "ListInv2" in names

    def test_list_investments_no_auth(self, client: TestClient):
        """List without auth returns 401."""
        resp = client.get("/api/v1/investments/")
        assert resp.status_code == 401

    def test_delete_investment(self, client: TestClient, auth_headers: Dict):
        """Delete existing investment returns 204."""
        inv = _create_investment(client, auth_headers, "DeleteInv")
        resp = client.delete(f"/api/v1/investments/{inv['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_investment_not_found(self, client: TestClient, auth_headers: Dict):
        """Delete non-existent investment returns 404."""
        resp = client.delete(f"/api/v1/investments/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_investment_wrong_user(self, client: TestClient, auth_headers: Dict, db):
        """Delete another user's investment returns 403."""
        inv = _create_investment(client, auth_headers, "OtherUserInv")

        from app.models.user import User
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"other2-{uuid.uuid4()}@example.com",
            password_hash=get_password_hash("pw"),
            full_name="Other2",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.delete(f"/api/v1/investments/{inv['id']}", headers=other_headers)
        assert resp.status_code == 403

    def test_list_investments_includes_account_name(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """List investments returns account_name and currency_ticker when linked."""
        acct = _create_inv_account(client, auth_headers, "ListLinkedBrokerage")
        resp = client.post("/api/v1/investments/", json={
            "category_name": "LinkedETF",
            "investment_account_id": acct["id"],
            "opening_balance": "1000.00",
            "opening_balance_date": "2026-01-01",
            "opening_balance_currency_id": str(test_currency.id)
        }, headers=auth_headers)
        assert resp.status_code == 200

        list_resp = client.get("/api/v1/investments/", headers=auth_headers)
        assert list_resp.status_code == 200
        linked = next((i for i in list_resp.json() if i["category_name"] == "LinkedETF"), None)
        assert linked is not None
        assert linked["account_name"] == "ListLinkedBrokerage"
        assert linked["currency_ticker"] == test_currency.ticker


# ---------------------------------------------------------------------------
# Investment Transfers
# ---------------------------------------------------------------------------

class TestInvestmentTransfers:

    def _setup(self, client, auth_headers, test_currency):
        """Create period, bank account, investment account, investment for transfer tests."""
        period = _create_period(client, auth_headers, f"InvTransP-{uuid.uuid4().hex[:6]}")
        bank_acct = _create_account(client, auth_headers, test_currency.id, "InvBankAcct")
        inv = _create_investment(client, auth_headers, f"InvCat-{uuid.uuid4().hex[:6]}")
        return period, bank_acct, inv

    def test_create_transfer(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """Create investment transfer — 200 with correct data."""
        period, bank_acct, inv = self._setup(client, auth_headers, test_currency)

        resp = client.post(f"/api/v1/investments/transfers/{period['id']}", json={
            "investment_id": inv["id"],
            "amount_transferred": "1000.00",
            "currency_id": str(test_currency.id),
            "source_account_id": bank_acct["id"],
            "transfer_date": "2026-01-15",
            "units_added": "10.5",
            "notes": "First purchase"
        }, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert float(data["amount_transferred"]) == 1000.0
        assert data["investment_id"] == inv["id"]

    def test_create_transfer_no_auth(
        self, client: TestClient, test_currency: Currency
    ):
        """Create without auth returns 401."""
        resp = client.post(f"/api/v1/investments/transfers/{uuid.uuid4()}", json={
            "investment_id": str(uuid.uuid4()),
            "amount_transferred": "100.00",
            "currency_id": str(test_currency.id),
            "source_account_id": str(uuid.uuid4()),
            "transfer_date": "2026-01-15"
        })
        assert resp.status_code == 401

    def test_create_transfer_period_not_found(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """Create transfer for non-existent period returns 404."""
        inv = _create_investment(client, auth_headers, f"InvNoPeriod-{uuid.uuid4().hex[:4]}")
        bank = _create_account(client, auth_headers, test_currency.id, "NoPeriodBank")

        resp = client.post(f"/api/v1/investments/transfers/{uuid.uuid4()}", json={
            "investment_id": inv["id"],
            "amount_transferred": "500.00",
            "currency_id": str(test_currency.id),
            "source_account_id": bank["id"],
            "transfer_date": "2026-01-15"
        }, headers=auth_headers)

        assert resp.status_code == 404

    def test_list_transfers_for_period(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """List transfers returns all transfers for the given period."""
        period, bank_acct, inv = self._setup(client, auth_headers, test_currency)

        # Create 2 transfers
        for amount in ["500.00", "750.00"]:
            client.post(f"/api/v1/investments/transfers/{period['id']}", json={
                "investment_id": inv["id"],
                "amount_transferred": amount,
                "currency_id": str(test_currency.id),
                "source_account_id": bank_acct["id"],
                "transfer_date": "2026-01-20"
            }, headers=auth_headers)

        resp = client.get(f"/api/v1/investments/transfers/{period['id']}", headers=auth_headers)
        assert resp.status_code == 200
        amounts = [float(t["amount_transferred"]) for t in resp.json()]
        assert 500.0 in amounts
        assert 750.0 in amounts

    def test_list_transfers_no_auth(self, client: TestClient):
        """List without auth returns 401."""
        resp = client.get(f"/api/v1/investments/transfers/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_delete_transfer(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """Delete transfer returns 204."""
        period, bank_acct, inv = self._setup(client, auth_headers, test_currency)

        t_resp = client.post(f"/api/v1/investments/transfers/{period['id']}", json={
            "investment_id": inv["id"],
            "amount_transferred": "300.00",
            "currency_id": str(test_currency.id),
            "source_account_id": bank_acct["id"],
            "transfer_date": "2026-01-10"
        }, headers=auth_headers)
        transfer_id = t_resp.json()["id"]

        resp = client.delete(f"/api/v1/investments/transfers/{transfer_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_transfer_not_found(self, client: TestClient, auth_headers: Dict):
        """Delete non-existent transfer returns 404."""
        resp = client.delete(
            f"/api/v1/investments/transfers/{uuid.uuid4()}", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_delete_transfer_wrong_user_returns_403(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, db
    ):
        """Delete transfer belonging to another user's period returns 403."""
        period, bank_acct, inv = self._setup(client, auth_headers, test_currency)

        t_resp = client.post(f"/api/v1/investments/transfers/{period['id']}", json={
            "investment_id": inv["id"],
            "amount_transferred": "200.00",
            "currency_id": str(test_currency.id),
            "source_account_id": bank_acct["id"],
            "transfer_date": "2026-01-12"
        }, headers=auth_headers)
        assert t_resp.status_code == 200
        transfer_id = t_resp.json()["id"]

        # Create another user with no relation to this period
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"other3-{uuid.uuid4()}@example.com",
            password_hash=get_password_hash("pw"),
            full_name="Other3",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.delete(
            f"/api/v1/investments/transfers/{transfer_id}",
            headers=other_headers
        )
        assert resp.status_code == 403

    def test_delete_transfer_in_finalized_period_blocked(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, db
    ):
        """Delete transfer in a FINALIZED period returns 400."""
        period, bank_acct, inv = self._setup(client, auth_headers, test_currency)

        t_resp = client.post(f"/api/v1/investments/transfers/{period['id']}", json={
            "investment_id": inv["id"],
            "amount_transferred": "100.00",
            "currency_id": str(test_currency.id),
            "source_account_id": bank_acct["id"],
            "transfer_date": "2026-01-05"
        }, headers=auth_headers)
        transfer_id = t_resp.json()["id"]

        # Directly finalize the period via DB to avoid reconciliation balance requirement
        from app.models.calculation_period import CalculationPeriod
        p = db.get(CalculationPeriod, period["id"])
        p.status = "FINALIZED"
        db.commit()

        resp = client.delete(
            f"/api/v1/investments/transfers/{transfer_id}", headers=auth_headers
        )
        assert resp.status_code == 400
