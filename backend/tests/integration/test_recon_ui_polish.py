"""
Integration tests for Reconciliation UI Polish.

Tests:
- Finalized period rejects create/update/delete of income and expenses
- Quick-balance endpoint auto-creates expense in Untracked Expenses category
"""
import pytest
import uuid
from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory


def _create_balanced_period(client, auth_headers, currency_id, category_id):
    """Create a period that is fully balanced and ready to finalize."""
    period = client.post("/api/v1/periods/", json={
        "period_name": f"Balanced Period {uuid.uuid4().hex[:6]}",
        "start_date": "2026-04-01",
        "end_date": "2026-04-30",
        "snapshot_date": "2026-04-30"
    }, headers=auth_headers).json()
    period_id = period["id"]

    # Account
    acc = client.post("/api/v1/accounts/", json={
        "account_name": "Test Bank",
        "account_type": "BANK",
        "currency_id": str(currency_id)
    }, headers=auth_headers).json()
    account_id = acc["id"]

    # Income: 1000
    client.post(f"/api/v1/periods/{period_id}/incomes", json={
        "source_name": "Salary",
        "amount": 1000,
        "currency_id": str(currency_id)
    }, headers=auth_headers)

    # Expense: 200
    client.post(f"/api/v1/periods/{period_id}/expenses", json={
        "item_name": "Rent",
        "amount": 200,
        "currency_id": str(currency_id),
        "category_id": str(category_id)
    }, headers=auth_headers)

    # Snapshot: 800 (balanced: 0 + 1000 - 200 = 800)
    client.post(f"/api/v1/periods/{period_id}/snapshots", json=[
        {"account_id": account_id, "balance": 800}
    ], headers=auth_headers)

    return period_id, account_id


class TestFinalizedPeriodLocking:
    """Once a period is finalized, income/expense mutations must be rejected."""

    def test_finalized_period_rejects_new_income(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        test_currency: Currency,
        test_category: ExpenseCategory,
    ):
        """POST /periods/{id}/incomes returns 400 when period is FINALIZED."""
        period_id, _ = _create_balanced_period(
            client, auth_headers, test_currency.id, test_category.id
        )
        # Finalize
        fin = client.patch(f"/api/v1/periods/{period_id}/finalize", headers=auth_headers)
        assert fin.status_code == 200

        # Try to add income
        resp = client.post(f"/api/v1/periods/{period_id}/incomes", json={
            "source_name": "Bonus",
            "amount": 500,
            "currency_id": str(test_currency.id)
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "finalized" in resp.json()["detail"].lower()

    def test_finalized_period_rejects_new_expense(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        test_currency: Currency,
        test_category: ExpenseCategory,
    ):
        """POST /periods/{id}/expenses returns 400 when period is FINALIZED."""
        period_id, _ = _create_balanced_period(
            client, auth_headers, test_currency.id, test_category.id
        )
        client.patch(f"/api/v1/periods/{period_id}/finalize", headers=auth_headers)

        resp = client.post(f"/api/v1/periods/{period_id}/expenses", json={
            "item_name": "Coffee",
            "amount": 5,
            "currency_id": str(test_currency.id),
            "category_id": str(test_category.id)
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "finalized" in resp.json()["detail"].lower()

    def test_finalized_period_rejects_income_update(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        test_currency: Currency,
        test_category: ExpenseCategory,
    ):
        """PATCH /incomes/{id} returns 400 when period is FINALIZED."""
        period_id, _ = _create_balanced_period(
            client, auth_headers, test_currency.id, test_category.id
        )

        # Get incomes before finalizing
        incomes = client.get(f"/api/v1/periods/{period_id}/incomes", headers=auth_headers).json()
        income_id = incomes[0]["id"]

        client.patch(f"/api/v1/periods/{period_id}/finalize", headers=auth_headers)

        resp = client.patch(f"/api/v1/incomes/{income_id}", json={
            "amount": 9999
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "finalized" in resp.json()["detail"].lower()

    def test_finalized_period_rejects_expense_delete(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        test_currency: Currency,
        test_category: ExpenseCategory,
    ):
        """DELETE /expenses/{id} returns 400 when period is FINALIZED."""
        period_id, _ = _create_balanced_period(
            client, auth_headers, test_currency.id, test_category.id
        )

        expenses = client.get(f"/api/v1/periods/{period_id}/expenses", headers=auth_headers).json()
        expense_id = expenses[0]["id"]

        client.patch(f"/api/v1/periods/{period_id}/finalize", headers=auth_headers)

        resp = client.delete(f"/api/v1/expenses/{expense_id}", headers=auth_headers)
        assert resp.status_code == 400
        assert "finalized" in resp.json()["detail"].lower()


class TestQuickBalance:
    """Quick-balance endpoint auto-adds an Untracked Expenses entry."""

    def test_quick_balance_creates_untracked_expense(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        test_currency: Currency,
        test_category: ExpenseCategory,
    ):
        """POST /periods/{id}/quick-balance creates expense in Untracked Expenses."""
        # Period with imbalance: 0 + 500 - 100 = 400 expected, snapshot = 350 → diff = -50
        period = client.post("/api/v1/periods/", json={
            "period_name": f"Imbalanced {uuid.uuid4().hex[:6]}",
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
            "snapshot_date": "2026-05-31"
        }, headers=auth_headers).json()
        period_id = period["id"]

        acc = client.post("/api/v1/accounts/", json={
            "account_name": "Cash",
            "account_type": "CASH",
            "currency_id": str(test_currency.id)
        }, headers=auth_headers).json()

        client.post(f"/api/v1/periods/{period_id}/incomes", json={
            "source_name": "Work",
            "amount": 500,
            "currency_id": str(test_currency.id)
        }, headers=auth_headers)

        client.post(f"/api/v1/periods/{period_id}/expenses", json={
            "item_name": "Groceries",
            "amount": 100,
            "currency_id": str(test_currency.id),
            "category_id": str(test_category.id)
        }, headers=auth_headers)

        client.post(f"/api/v1/periods/{period_id}/snapshots", json=[
            {"account_id": acc["id"], "balance": 350}
        ], headers=auth_headers)

        # Quick balance: difference = 400 - 350 = 50 (expected > actual → Untracked Expense of 50)
        resp = client.post(
            f"/api/v1/periods/{period_id}/quick-balance",
            json={"currency_ticker": test_currency.ticker},
            headers=auth_headers
        )
        assert resp.status_code in (200, 201)

        data = resp.json()
        assert data["item_name"] == "Untracked Expenses"
        assert float(data["amount"]) == 50.0

    def test_quick_balance_404_when_balanced(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        test_currency: Currency,
        test_category: ExpenseCategory,
    ):
        """POST /periods/{id}/quick-balance returns 400 when period is already balanced."""
        period_id, _ = _create_balanced_period(
            client, auth_headers, test_currency.id, test_category.id
        )

        resp = client.post(
            f"/api/v1/periods/{period_id}/quick-balance",
            json={"currency_ticker": test_currency.ticker},
            headers=auth_headers
        )
        assert resp.status_code == 400
