"""
Integration tests for reconciliation endpoint error paths.
Covers: get_reconciliation 404, finalize_period 404/400, tax-benefits 404,
quick_balance 404/400 paths.
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from app.models.currency import Currency


def _create_period(client, headers):
    resp = client.post("/api/v1/periods/", json={
        "period_name": f"ReconErrP-{uuid.uuid4().hex[:6]}",
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
        "snapshot_date": "2026-08-31"
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()


class TestGetReconciliationErrors:

    def test_get_reconciliation_period_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """GET reconciliation for non-existent period returns 404."""
        resp = client.get(
            f"/api/v1/periods/{uuid.uuid4()}/reconciliation",
            headers=auth_headers
        )
        assert resp.status_code == 404


class TestFinalizePeriodErrors:

    def test_finalize_period_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """PATCH finalize non-existent period returns 404."""
        resp = client.patch(
            f"/api/v1/periods/{uuid.uuid4()}/finalize",
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_finalize_already_finalized_returns_400(
        self, client: TestClient, auth_headers: Dict, db
    ):
        """PATCH finalize already-finalized period returns 400."""
        period = _create_period(client, auth_headers)

        from app.models.calculation_period import CalculationPeriod
        p = db.get(CalculationPeriod, period["id"])
        p.status = "FINALIZED"
        db.commit()

        resp = client.patch(
            f"/api/v1/periods/{period['id']}/finalize",
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "already finalized" in resp.json()["detail"].lower()

    def test_finalize_unbalanced_period_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency,
        test_category
    ):
        """PATCH finalize unbalanced period returns 400."""
        period = _create_period(client, auth_headers)

        # Add an expense to make it unbalanced
        client.post(f"/api/v1/periods/{period['id']}/expenses", json={
            "item_name": "Unbalanced",
            "amount": "100.00",
            "currency_id": str(test_currency.id),
            "category_id": str(test_category.id),
            "expense_date": "2026-08-10"
        }, headers=auth_headers)

        resp = client.patch(
            f"/api/v1/periods/{period['id']}/finalize",
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "not balanced" in resp.json()["detail"]["message"].lower()


class TestTaxBenefitsErrors:

    def test_tax_benefits_period_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """GET tax-benefits for non-existent period returns 404."""
        resp = client.get(
            f"/api/v1/periods/{uuid.uuid4()}/tax-benefits",
            headers=auth_headers
        )
        assert resp.status_code == 404


class TestQuickBalanceErrors:

    def test_quick_balance_period_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """POST quick-balance for non-existent period returns 404."""
        resp = client.post(
            f"/api/v1/periods/{uuid.uuid4()}/quick-balance",
            json={"currency_ticker": "USD"},
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_quick_balance_finalized_period_returns_400(
        self, client: TestClient, auth_headers: Dict, db
    ):
        """POST quick-balance for finalized period returns 400."""
        period = _create_period(client, auth_headers)

        from app.models.calculation_period import CalculationPeriod
        p = db.get(CalculationPeriod, period["id"])
        p.status = "FINALIZED"
        db.commit()

        resp = client.post(
            f"/api/v1/periods/{period['id']}/quick-balance",
            json={"currency_ticker": "USD"},
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "finalized" in resp.json()["detail"].lower()

    def test_quick_balance_currency_not_in_recon_returns_400(
        self, client: TestClient, auth_headers: Dict
    ):
        """POST quick-balance with currency not in reconciliation returns 400."""
        period = _create_period(client, auth_headers)

        resp = client.post(
            f"/api/v1/periods/{period['id']}/quick-balance",
            json={"currency_ticker": "NOSUCHCUR"},
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "NOSUCHCUR" in resp.json()["detail"]

    def test_quick_balance_already_balanced_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """POST quick-balance on already balanced period returns 400."""
        period = _create_period(client, auth_headers)

        # Empty period with no income/expenses is balanced at 0 vs 0
        resp = client.post(
            f"/api/v1/periods/{period['id']}/quick-balance",
            json={"currency_ticker": test_currency.ticker},
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "balanced" in resp.json()["detail"].lower()

    def test_quick_balance_negative_difference_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """POST quick-balance where actual > expected (negative diff) returns 400."""
        period = _create_period(client, auth_headers)

        # Create account and snapshot with positive balance (actual > expected)
        acct_resp = client.post("/api/v1/accounts/", json={
            "account_name": f"QBNeg-{uuid.uuid4().hex[:6]}",
            "account_type": "BANK",
            "currency_id": str(test_currency.id),
            "opening_balance": "0.00"
        }, headers=auth_headers)
        account_id = acct_resp.json()["id"]

        # Add snapshot with balance 500 → actual = 500, expected = 0 → diff = -500
        client.post(f"/api/v1/periods/{period['id']}/snapshots", json=[
            {"account_id": account_id, "balance": "500.00"}
        ], headers=auth_headers)

        resp = client.post(
            f"/api/v1/periods/{period['id']}/quick-balance",
            json={"currency_ticker": test_currency.ticker},
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "income" in resp.json()["detail"].lower()

    def test_quick_balance_success_creates_untracked_expense(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """POST quick-balance where expected > actual creates Untracked Expenses entry."""
        period = _create_period(client, auth_headers)

        # Create account with snapshot at 0 → actual = 0
        acct_resp = client.post("/api/v1/accounts/", json={
            "account_name": f"QBSucc-{uuid.uuid4().hex[:6]}",
            "account_type": "BANK",
            "currency_id": str(test_currency.id),
            "opening_balance": "0.00"
        }, headers=auth_headers)
        account_id = acct_resp.json()["id"]

        client.post(f"/api/v1/periods/{period['id']}/snapshots", json=[
            {"account_id": account_id, "balance": "0.00"}
        ], headers=auth_headers)

        # Add income of 100 → expected = 100, actual = 0 → diff = 100 > 0
        client.post(f"/api/v1/periods/{period['id']}/incomes", json={
            "source_name": "Salary",
            "amount": "100.00",
            "currency_id": str(test_currency.id),
            "income_date": "2026-08-10"
        }, headers=auth_headers)

        resp = client.post(
            f"/api/v1/periods/{period['id']}/quick-balance",
            json={"currency_ticker": test_currency.ticker},
            headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["item_name"] == "Untracked Expenses"
        assert float(data["amount"]) == 100.0
