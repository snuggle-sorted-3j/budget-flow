"""
Integration Tests for Multi-Tenant Authorization

Verifies that users cannot read, modify, or delete each other's resources.
This is a critical security test suite — every endpoint that filters by user_id
should return 404 (not 403) when accessed by another user, to avoid leaking
resource existence.

Industry best practice: treat cross-user access as "not found" rather than
"forbidden" to prevent enumeration attacks.
"""

import pytest
import uuid

pytestmark = [pytest.mark.integration, pytest.mark.security]
from typing import Dict, Tuple
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.currency import Currency
from app.core.security import create_access_token, get_password_hash


# ---------------------------------------------------------------------------
# Fixtures: second user with independent auth
# ---------------------------------------------------------------------------

@pytest.fixture
def second_user(db: Session) -> User:
    """Create a second test user for cross-user access tests."""
    user = User(
        id=uuid.uuid4(),
        email=f"attacker-{uuid.uuid4()}@example.com",
        password_hash=get_password_hash("attackerpass123"),
        full_name="Attacker User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def second_auth_headers(second_user: User) -> Dict[str, str]:
    """Auth headers for the second (attacker) user."""
    token = create_access_token(data={"sub": str(second_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_currency(db: Session, second_user: User) -> Currency:
    """Currency for the second user."""
    currency = Currency(
        id=uuid.uuid4(),
        user_id=second_user.id,
        ticker="EUR",
        name="Euro",
        is_default=True,
    )
    db.add(currency)
    db.commit()
    db.refresh(currency)
    return currency


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_period(client, auth_headers, suffix=""):
    resp = client.post("/api/v1/periods/", json={
        "period_name": f"AuthZ Period {suffix} {uuid.uuid4()}",
        "start_date": "2027-03-01",
        "end_date": "2027-03-31",
        "snapshot_date": "2027-03-31",
    }, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


def _create_income(client, auth_headers, period_id, currency_id):
    resp = client.post(f"/api/v1/periods/{period_id}/incomes", json={
        "source_name": "Victim Salary",
        "amount": 5000,
        "currency_id": str(currency_id),
    }, headers=auth_headers)
    assert resp.status_code in (200, 201)
    return resp.json()


def _create_expense(client, auth_headers, period_id, currency_id, category_id):
    resp = client.post(f"/api/v1/periods/{period_id}/expenses", json={
        "item_name": "Victim Rent",
        "amount": 1500,
        "currency_id": str(currency_id),
        "category_id": str(category_id),
    }, headers=auth_headers)
    assert resp.status_code in (200, 201)
    return resp.json()


def _create_account(client, auth_headers, currency_id):
    resp = client.post("/api/v1/accounts/", json={
        "account_name": "Victim Bank",
        "account_type": "BANK",
        "currency_id": str(currency_id),
    }, headers=auth_headers)
    assert resp.status_code in (200, 201)
    return resp.json()


# ===========================================================================
# PERIOD ISOLATION TESTS
# ===========================================================================

class TestPeriodIsolation:
    """User A's periods must be invisible to User B."""

    def test_cannot_list_other_user_periods(
        self, client, auth_headers, second_auth_headers, test_currency
    ):
        """User A creates a period; User B's period list must not include it."""
        _create_period(client, auth_headers, "victim")

        victim_periods = client.get("/api/v1/periods/", headers=auth_headers).json()
        attacker_periods = client.get("/api/v1/periods/", headers=second_auth_headers).json()

        victim_ids = {p["id"] for p in victim_periods}
        attacker_ids = {p["id"] for p in attacker_periods}
        assert victim_ids.isdisjoint(attacker_ids), "Attacker can see victim's periods"

    def test_cannot_read_other_user_period(
        self, client, auth_headers, second_auth_headers, test_currency
    ):
        """Directly accessing another user's period by ID should return 404."""
        period = _create_period(client, auth_headers)
        resp = client.get(f"/api/v1/periods/{period['id']}", headers=second_auth_headers)
        assert resp.status_code == 404

    def test_cannot_delete_other_user_period(
        self, client, auth_headers, second_auth_headers, test_currency
    ):
        """Deleting another user's period should return 404."""
        period = _create_period(client, auth_headers)
        resp = client.delete(f"/api/v1/periods/{period['id']}", headers=second_auth_headers)
        assert resp.status_code == 404

    def test_cannot_finalize_other_user_period(
        self, client, auth_headers, second_auth_headers, test_currency
    ):
        """Changing status on another user's period should return 404."""
        period = _create_period(client, auth_headers)
        resp = client.patch(
            f"/api/v1/periods/{period['id']}/status",
            json={"status": "FINALIZED"},
            headers=second_auth_headers,
        )
        assert resp.status_code == 404


# ===========================================================================
# INCOME ISOLATION TESTS
# ===========================================================================

class TestIncomeIsolation:
    """User A's incomes must be invisible to User B."""

    def test_cannot_list_other_user_incomes(
        self, client, auth_headers, second_auth_headers, test_currency
    ):
        """Listing incomes for another user's period should fail."""
        period = _create_period(client, auth_headers)
        _create_income(client, auth_headers, period["id"], test_currency.id)

        resp = client.get(
            f"/api/v1/periods/{period['id']}/incomes", headers=second_auth_headers
        )
        # Should either 404 (period not found for this user) or return empty
        assert resp.status_code == 404 or len(resp.json()) == 0

    def test_cannot_delete_other_user_income(
        self, client, auth_headers, second_auth_headers, test_currency
    ):
        """Deleting another user's income should not succeed.

        NOTE: Ideally returns 404 to prevent enumeration. If the endpoint
        returns 403 instead, this is an information disclosure issue
        (attacker can confirm the income ID exists).
        """
        period = _create_period(client, auth_headers)
        income = _create_income(client, auth_headers, period["id"], test_currency.id)

        resp = client.delete(
            f"/api/v1/incomes/{income['id']}", headers=second_auth_headers
        )
        # Must not succeed — 403 or 404 both block the action, but 404 is preferred
        assert resp.status_code in (403, 404)

        # Verify income still exists for the real owner
        incomes = client.get(
            f"/api/v1/periods/{period['id']}/incomes", headers=auth_headers
        ).json()
        assert any(i["id"] == income["id"] for i in incomes), "Income was deleted by attacker!"


# ===========================================================================
# EXPENSE ISOLATION TESTS
# ===========================================================================

class TestExpenseIsolation:
    """User A's expenses must be invisible to User B."""

    def test_cannot_list_other_user_expenses(
        self, client, auth_headers, second_auth_headers,
        test_currency, test_category
    ):
        """Listing expenses for another user's period should fail."""
        period = _create_period(client, auth_headers)
        _create_expense(client, auth_headers, period["id"], test_currency.id, test_category.id)

        resp = client.get(
            f"/api/v1/periods/{period['id']}/expenses", headers=second_auth_headers
        )
        assert resp.status_code == 404 or len(resp.json()) == 0

    def test_cannot_delete_other_user_expense(
        self, client, auth_headers, second_auth_headers,
        test_currency, test_category
    ):
        """Deleting another user's expense should not succeed."""
        period = _create_period(client, auth_headers)
        expense = _create_expense(
            client, auth_headers, period["id"], test_currency.id, test_category.id
        )

        resp = client.delete(
            f"/api/v1/expenses/{expense['id']}", headers=second_auth_headers
        )
        assert resp.status_code in (403, 404)

        # Verify expense still exists
        expenses = client.get(
            f"/api/v1/periods/{period['id']}/expenses", headers=auth_headers
        ).json()
        assert any(e["id"] == expense["id"] for e in expenses), "Expense was deleted by attacker!"


# ===========================================================================
# ACCOUNT ISOLATION TESTS
# ===========================================================================

class TestAccountIsolation:
    """User A's accounts must be invisible to User B."""

    def test_cannot_list_other_user_accounts(
        self, client, auth_headers, second_auth_headers, test_currency
    ):
        """User B should not see User A's accounts."""
        _create_account(client, auth_headers, test_currency.id)

        victim_accounts = client.get("/api/v1/accounts/", headers=auth_headers).json()
        attacker_accounts = client.get("/api/v1/accounts/", headers=second_auth_headers).json()

        victim_ids = {a["id"] for a in victim_accounts}
        attacker_ids = {a["id"] for a in attacker_accounts}
        assert victim_ids.isdisjoint(attacker_ids), "Attacker can see victim's accounts"

    def test_cannot_delete_other_user_account(
        self, client, auth_headers, second_auth_headers, test_currency
    ):
        """Deleting another user's account should return 404."""
        account = _create_account(client, auth_headers, test_currency.id)

        resp = client.delete(
            f"/api/v1/accounts/{account['id']}", headers=second_auth_headers
        )
        assert resp.status_code == 404

        # Verify still exists
        accounts = client.get("/api/v1/accounts/", headers=auth_headers).json()
        assert any(a["id"] == account["id"] for a in accounts), "Account was deleted by attacker!"


# ===========================================================================
# INJECTION SAFETY TESTS
# ===========================================================================

class TestInjectionSafety:
    """Text fields should safely store malicious input without execution."""

    SQL_INJECTION_PAYLOADS = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "Robert'); DROP TABLE income_entries;--",
        "' UNION SELECT password_hash FROM users--",
    ]

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        '<img src=x onerror="alert(1)">',
        "javascript:alert(document.cookie)",
    ]

    def test_sql_injection_in_period_name(
        self, client, auth_headers
    ):
        """SQL injection in period_name should be stored as literal text."""
        for payload in self.SQL_INJECTION_PAYLOADS:
            resp = client.post("/api/v1/periods/", json={
                "period_name": payload,
                "start_date": "2027-06-01",
                "end_date": "2027-06-30",
                "snapshot_date": "2027-06-30",
            }, headers=auth_headers)
            # Should succeed — the payload is just a string
            assert resp.status_code == 201
            assert resp.json()["period_name"] == payload

    def test_sql_injection_in_income_source(
        self, client, auth_headers, test_currency
    ):
        """SQL injection in income source_name should be stored as literal text."""
        period = _create_period(client, auth_headers, "inj")

        for payload in self.SQL_INJECTION_PAYLOADS:
            resp = client.post(f"/api/v1/periods/{period['id']}/incomes", json={
                "source_name": payload,
                "amount": 100,
                "currency_id": str(test_currency.id),
            }, headers=auth_headers)
            assert resp.status_code in (200, 201)
            assert resp.json()["source_name"] == payload

    def test_xss_in_expense_name(
        self, client, auth_headers, test_currency, test_category
    ):
        """XSS payloads in expense names should be stored as literal text."""
        period = _create_period(client, auth_headers, "xss")

        for payload in self.XSS_PAYLOADS:
            resp = client.post(f"/api/v1/periods/{period['id']}/expenses", json={
                "item_name": payload,
                "amount": 50,
                "currency_id": str(test_currency.id),
                "category_id": str(test_category.id),
            }, headers=auth_headers)
            assert resp.status_code in (200, 201)
            # Stored as-is (SQLAlchemy parameterized queries prevent execution)
            assert resp.json()["item_name"] == payload

    def test_database_survives_injection_attempts(
        self, client, auth_headers
    ):
        """After injection attempts, the database should still be fully functional."""
        # Create a normal period after injection tests
        resp = client.post("/api/v1/periods/", json={
            "period_name": "Post-Injection Sanity Check",
            "start_date": "2027-07-01",
            "end_date": "2027-07-31",
            "snapshot_date": "2027-07-31",
        }, headers=auth_headers)
        assert resp.status_code == 201

        # List should work
        list_resp = client.get("/api/v1/periods/", headers=auth_headers)
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1
