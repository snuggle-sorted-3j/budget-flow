"""
End-to-end workflow tests covering real user journeys.
These tests catch integration bugs that isolated API tests miss.
"""
import uuid
from typing import Dict
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from app.models.currency import Currency


def _create_period(client, headers, period_name=None):
    """Helper to create a period."""
    resp = client.post("/api/v1/periods/", json={
        "period_name": period_name or f"E2E-{uuid.uuid4().hex[:6]}",
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "snapshot_date": "2026-10-31"
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_account(client, headers, currency_id, name=None, opening_balance="0.00"):
    """Helper to create an account."""
    resp = client.post("/api/v1/accounts/", json={
        "account_name": name or f"Account-{uuid.uuid4().hex[:6]}",
        "account_type": "BANK",
        "currency_id": str(currency_id),
        "opening_balance": opening_balance
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestE2EReconciliationWorkflow:
    """Test: user creates period, adds income/expenses, takes snapshot, finalizes."""

    def test_full_balanced_reconciliation_flow(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, test_category
    ):
        """
        Full workflow: create account → create period → add income → add expense
        → take snapshot → reconcile → finalize.
        """
        # 1. Create account with opening balance
        account = _create_account(
            client, auth_headers, test_currency.id, "Main Bank", opening_balance="1000.00"
        )
        assert float(account["opening_balance"]) == 1000.0

        # 2. Create period
        period = _create_period(client, auth_headers)
        assert period["status"] == "DRAFT"

        # 3. Add income
        income_resp = client.post(
            f"/api/v1/periods/{period['id']}/incomes",
            json={
                "source_name": "Salary",
                "amount": "5000.00",
                "currency_id": str(test_currency.id),
                "income_date": "2026-10-05"
            },
            headers=auth_headers
        )
        assert income_resp.status_code == 201
        income = income_resp.json()
        assert income["source_name"] == "Salary"

        # 4. Add two expenses
        exp1_resp = client.post(
            f"/api/v1/periods/{period['id']}/expenses",
            json={
                "item_name": "Groceries",
                "amount": "500.00",
                "currency_id": str(test_currency.id),
                "category_id": str(test_category.id),
                "expense_date": "2026-10-10"
            },
            headers=auth_headers
        )
        assert exp1_resp.status_code == 201

        exp2_resp = client.post(
            f"/api/v1/periods/{period['id']}/expenses",
            json={
                "item_name": "Utilities",
                "amount": "200.00",
                "currency_id": str(test_currency.id),
                "category_id": str(test_category.id),
                "expense_date": "2026-10-15"
            },
            headers=auth_headers
        )
        assert exp2_resp.status_code == 201

        # 5. Take balance snapshot
        # Expected: 1000 (opening) + 5000 (income) - 500 - 200 (expenses) = 5300
        snap_resp = client.post(
            f"/api/v1/periods/{period['id']}/snapshots",
            json=[{"account_id": account["id"], "balance": "5300.00"}],
            headers=auth_headers
        )
        assert snap_resp.status_code == 200
        assert len(snap_resp.json()) >= 1

        # 6. Check reconciliation
        recon_resp = client.get(
            f"/api/v1/periods/{period['id']}/reconciliation",
            headers=auth_headers
        )
        assert recon_resp.status_code == 200
        recon = recon_resp.json()
        assert recon["overall_balanced"] is True

        # 7. Finalize period
        final_resp = client.patch(
            f"/api/v1/periods/{period['id']}/finalize",
            headers=auth_headers
        )
        assert final_resp.status_code == 200
        final = final_resp.json()
        assert final["status"] == "FINALIZED"

        # 8. Verify can't add expenses to finalized period
        blocked_exp = client.post(
            f"/api/v1/periods/{period['id']}/expenses",
            json={
                "item_name": "Should Fail",
                "amount": "100.00",
                "currency_id": str(test_currency.id),
                "category_id": str(test_category.id),
                "expense_date": "2026-10-20"
            },
            headers=auth_headers
        )
        assert blocked_exp.status_code == 400


class TestE2EMultiCategoryMultiSourceFlow:
    """Test: realistic scenario with multiple income sources and expense categories."""

    def test_multiple_categories_and_income_sources(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """
        Realistic scenario:
        - Multiple income sources (salary + bonus + freelance)
        - Multiple expense categories (food, rent, utilities, entertainment)
        - Verify analytics query works
        """
        # 1. Create categories
        cats = []
        for cat_name in ["Food & Dining", "Rent", "Utilities", "Entertainment"]:
            cat_resp = client.post("/api/v1/expense-categories/", json={
                "category_name": cat_name,
                "icon": "🏠" if cat_name == "Rent" else "🍔"
            }, headers=auth_headers)
            assert cat_resp.status_code == 201
            cats.append(cat_resp.json())

        # 2. Create account
        account = _create_account(
            client, auth_headers, test_currency.id, "Checking", opening_balance="500.00"
        )

        # 3. Create period
        period = _create_period(client, auth_headers)

        # 4. Add multiple income sources
        income_sources = [
            ("Salary", "5000.00"),
            ("Freelance Gig", "500.00"),
            ("Bonus", "200.00")
        ]
        total_income = Decimal("0.00")
        for source, amount in income_sources:
            client.post(
                f"/api/v1/periods/{period['id']}/incomes",
                json={
                    "source_name": source,
                    "amount": amount,
                    "currency_id": str(test_currency.id),
                    "income_date": "2026-10-05"
                },
                headers=auth_headers
            )
            total_income += Decimal(amount)

        # 5. Add expenses to different categories
        expenses = [
            ("Groceries", "150.00", cats[0]["id"]),
            ("Restaurant", "45.00", cats[0]["id"]),
            ("Rent", "2000.00", cats[1]["id"]),
            ("Electric", "120.00", cats[2]["id"]),
            ("Movie tickets", "30.00", cats[3]["id"])
        ]
        total_expenses = Decimal("0.00")
        for name, amount, cat_id in expenses:
            client.post(
                f"/api/v1/periods/{period['id']}/expenses",
                json={
                    "item_name": name,
                    "amount": amount,
                    "currency_id": str(test_currency.id),
                    "category_id": str(cat_id),
                    "expense_date": "2026-10-10"
                },
                headers=auth_headers
            )
            total_expenses += Decimal(amount)

        # 6. Take snapshot (balanced)
        expected_balance = Decimal("500.00") + total_income - total_expenses
        client.post(
            f"/api/v1/periods/{period['id']}/snapshots",
            json=[{"account_id": account["id"], "balance": str(expected_balance)}],
            headers=auth_headers
        )

        # 7. Verify reconciliation is balanced
        recon_resp = client.get(
            f"/api/v1/periods/{period['id']}/reconciliation",
            headers=auth_headers
        )
        assert recon_resp.status_code == 200
        assert recon_resp.json()["overall_balanced"] is True

        # 8. Check analytics query works (spending by category)
        analytics_resp = client.get(
            f"/api/v1/analytics/spending-by-category?period_id={period['id']}",
            headers=auth_headers
        )
        assert analytics_resp.status_code == 200
        analytics = analytics_resp.json()
        assert "by_category" in analytics
        assert len(analytics["by_category"]) >= 4  # At least our 4 categories

        # 9. Finalize successfully
        final_resp = client.patch(
            f"/api/v1/periods/{period['id']}/finalize",
            headers=auth_headers
        )
        assert final_resp.status_code == 200


class TestE2EUnbalancedQuickBalance:
    """Test: user finds unbalanced period, uses quick-balance to auto-close."""

    def test_quick_balance_closes_gap(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, test_category
    ):
        """
        Scenario: Period has income/expenses but actual balance is lower than expected.
        Use quick-balance to create 'Untracked Expenses' entry to balance.
        """
        # 1. Create account and period
        account = _create_account(client, auth_headers, test_currency.id)
        period = _create_period(client, auth_headers)

        # 2. Add income: $1000
        client.post(
            f"/api/v1/periods/{period['id']}/incomes",
            json={
                "source_name": "Salary",
                "amount": "1000.00",
                "currency_id": str(test_currency.id),
                "income_date": "2026-10-05"
            },
            headers=auth_headers
        )

        # 3. Add expense: $300
        client.post(
            f"/api/v1/periods/{period['id']}/expenses",
            json={
                "item_name": "Coffee",
                "amount": "300.00",
                "currency_id": str(test_currency.id),
                "category_id": str(test_category.id),
                "expense_date": "2026-10-10"
            },
            headers=auth_headers
        )

        # 4. Snapshot shows only $500 actual (expected: 1000 - 300 = 700)
        # Difference: 700 - 500 = 200 gap
        client.post(
            f"/api/v1/periods/{period['id']}/snapshots",
            json=[{"account_id": account["id"], "balance": "500.00"}],
            headers=auth_headers
        )

        # 5. Verify unbalanced
        recon_resp = client.get(
            f"/api/v1/periods/{period['id']}/reconciliation",
            headers=auth_headers
        )
        assert recon_resp.json()["overall_balanced"] is False

        # 6. Use quick-balance to fill gap
        qb_resp = client.post(
            f"/api/v1/periods/{period['id']}/quick-balance",
            json={"currency_ticker": test_currency.ticker},
            headers=auth_headers
        )
        assert qb_resp.status_code == 200
        qb_expense = qb_resp.json()
        assert qb_expense["item_name"] == "Untracked Expenses"
        assert float(qb_expense["amount"]) == 200.0

        # 7. Now finalize should succeed (balanced)
        final_resp = client.patch(
            f"/api/v1/periods/{period['id']}/finalize",
            headers=auth_headers
        )
        assert final_resp.status_code == 200
        assert final_resp.json()["status"] == "FINALIZED"


class TestE2EDecimalEdgeCases:
    """Test: edge cases with very small/large amounts and division."""

    def test_very_small_amounts_and_percentage_calculation(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, test_category
    ):
        """
        Test that analytics handles very small amounts correctly.
        Catch Decimal/float conversion bugs.
        """
        account = _create_account(client, auth_headers, test_currency.id, opening_balance="0.00")
        period = _create_period(client, auth_headers)

        # 1. Add micro-expenses
        amounts = ["0.01", "0.50", "1.00", "100.00"]
        for amount in amounts:
            client.post(
                f"/api/v1/periods/{period['id']}/expenses",
                json={
                    "item_name": f"Item-{amount}",
                    "amount": amount,
                    "currency_id": str(test_currency.id),
                    "category_id": str(test_category.id),
                    "expense_date": "2026-10-10"
                },
                headers=auth_headers
            )

        # 2. Add income to match total expenses
        total = sum(Decimal(a) for a in amounts)
        client.post(
            f"/api/v1/periods/{period['id']}/incomes",
            json={
                "source_name": "Income",
                "amount": str(total),
                "currency_id": str(test_currency.id),
                "income_date": "2026-10-05"
            },
            headers=auth_headers
        )

        # 3. Take balanced snapshot
        client.post(
            f"/api/v1/periods/{period['id']}/snapshots",
            json=[{"account_id": account["id"], "balance": "0.00"}],
            headers=auth_headers
        )

        # 4. Analytics should not crash on division/percentage
        analytics_resp = client.get(
            f"/api/v1/analytics/spending-by-category?period_id={period['id']}",
            headers=auth_headers
        )
        assert analytics_resp.status_code == 200
        analytics = analytics_resp.json()

        # Verify percentages are valid numbers
        for cat in analytics["by_category"]:
            assert isinstance(cat["percentage"], (int, float))
            assert 0 <= cat["percentage"] <= 100

        # 5. Finalize should work
        final_resp = client.patch(
            f"/api/v1/periods/{period['id']}/finalize",
            headers=auth_headers
        )
        assert final_resp.status_code == 200

    def test_very_large_amounts(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, test_category
    ):
        """Test that large amounts (999,999.99) don't overflow."""
        account = _create_account(client, auth_headers, test_currency.id, opening_balance="0.00")
        period = _create_period(client, auth_headers)

        # 1. Add large expense
        large_amount = "999999.99"
        exp_resp = client.post(
            f"/api/v1/periods/{period['id']}/expenses",
            json={
                "item_name": "Large Purchase",
                "amount": large_amount,
                "currency_id": str(test_currency.id),
                "category_id": str(test_category.id),
                "expense_date": "2026-10-10"
            },
            headers=auth_headers
        )
        assert exp_resp.status_code == 201

        # 2. Add matching income
        client.post(
            f"/api/v1/periods/{period['id']}/incomes",
            json={
                "source_name": "Large Income",
                "amount": large_amount,
                "currency_id": str(test_currency.id),
                "income_date": "2026-10-05"
            },
            headers=auth_headers
        )

        # 3. Take snapshot
        client.post(
            f"/api/v1/periods/{period['id']}/snapshots",
            json=[{"account_id": account["id"], "balance": "0.00"}],
            headers=auth_headers
        )

        # 4. Verify reconciliation works
        recon_resp = client.get(
            f"/api/v1/periods/{period['id']}/reconciliation",
            headers=auth_headers
        )
        assert recon_resp.status_code == 200
        assert recon_resp.json()["overall_balanced"] is True

        # 5. Finalize
        final_resp = client.patch(
            f"/api/v1/periods/{period['id']}/finalize",
            headers=auth_headers
        )
        assert final_resp.status_code == 200
