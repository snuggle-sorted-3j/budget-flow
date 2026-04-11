"""
Integration tests for suspended expenses error paths.
Covers: create 404 (period), settle 404/400, convert 404/400, delete 404.
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from app.models.currency import Currency


def _create_period(client, headers):
    resp = client.post("/api/v1/periods/", json={
        "period_name": f"SuspPeriod-{uuid.uuid4().hex[:6]}",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
        "snapshot_date": "2026-09-30"
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def _create_suspended_expense(client, headers, period_id, currency_id):
    resp = client.post(f"/api/v1/suspended-expenses/{period_id}", json={
        "item_name": "TestSuspended",
        "amount": "200.00",
        "currency_id": str(currency_id),
        "transaction_type": "LOAN_OUT"
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestCreateSuspendedExpenseErrors:

    def test_create_suspended_period_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """POST suspended expense to non-existent period returns 404."""
        resp = client.post(f"/api/v1/suspended-expenses/{uuid.uuid4()}", json={
            "item_name": "X",
            "amount": "50.00",
            "currency_id": str(test_currency.id),
            "transaction_type": "LOAN_OUT"
        }, headers=auth_headers)
        assert resp.status_code == 404


class TestSettleSuspendedExpenseErrors:

    def test_settle_expense_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """PATCH settle non-existent expense returns 404."""
        period = _create_period(client, auth_headers)
        resp = client.patch(
            f"/api/v1/suspended-expenses/{uuid.uuid4()}/settle/{period['id']}",
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_settle_period_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """PATCH settle with non-existent period returns 404."""
        period = _create_period(client, auth_headers)
        expense = _create_suspended_expense(client, auth_headers, period["id"], test_currency.id)

        resp = client.patch(
            f"/api/v1/suspended-expenses/{expense['id']}/settle/{uuid.uuid4()}",
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_settle_non_pending_expense_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """PATCH settle already-settled expense returns 400."""
        period = _create_period(client, auth_headers)
        expense = _create_suspended_expense(client, auth_headers, period["id"], test_currency.id)

        # Settle first time → OK
        client.patch(
            f"/api/v1/suspended-expenses/{expense['id']}/settle/{period['id']}",
            headers=auth_headers
        )

        # Settle again → 400
        resp = client.patch(
            f"/api/v1/suspended-expenses/{expense['id']}/settle/{period['id']}",
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "not pending" in resp.json()["detail"].lower()


class TestConvertSuspendedExpenseErrors:

    def test_convert_expense_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict, test_category
    ):
        """PATCH convert non-existent expense returns 404."""
        period = _create_period(client, auth_headers)
        resp = client.patch(
            f"/api/v1/suspended-expenses/{uuid.uuid4()}/convert",
            params={
                "period_id": period["id"],
                "category_id": str(test_category.id)
            },
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_convert_non_pending_expense_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, test_category
    ):
        """PATCH convert already-settled expense returns 400."""
        period = _create_period(client, auth_headers)
        expense = _create_suspended_expense(client, auth_headers, period["id"], test_currency.id)

        # Settle first
        client.patch(
            f"/api/v1/suspended-expenses/{expense['id']}/settle/{period['id']}",
            headers=auth_headers
        )

        # Convert settled → 400
        resp = client.patch(
            f"/api/v1/suspended-expenses/{expense['id']}/convert",
            params={
                "period_id": period["id"],
                "category_id": str(test_category.id)
            },
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "not pending" in resp.json()["detail"].lower()

    def test_convert_period_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, test_category
    ):
        """PATCH convert with non-existent period_id returns 404."""
        period = _create_period(client, auth_headers)
        expense = _create_suspended_expense(client, auth_headers, period["id"], test_currency.id)

        resp = client.patch(
            f"/api/v1/suspended-expenses/{expense['id']}/convert",
            params={
                "period_id": str(uuid.uuid4()),
                "category_id": str(test_category.id)
            },
            headers=auth_headers
        )
        assert resp.status_code == 404


class TestDeleteSuspendedExpenseErrors:

    def test_delete_suspended_expense_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """DELETE non-existent suspended expense returns 404."""
        resp = client.delete(
            f"/api/v1/suspended-expenses/{uuid.uuid4()}",
            headers=auth_headers
        )
        assert resp.status_code == 404
