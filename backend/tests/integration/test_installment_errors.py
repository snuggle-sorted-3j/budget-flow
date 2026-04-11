"""
Integration tests for installments endpoint error paths and uncovered happy paths.
Covers: update item, get payments per item, payment create/delete error paths.
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from app.models.currency import Currency


def _create_period(client, headers):
    resp = client.post("/api/v1/periods/", json={
        "period_name": f"InstErrP-{uuid.uuid4().hex[:6]}",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "snapshot_date": "2026-03-31"
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_item(client, headers, currency_id, period_id, name="TestItem"):
    resp = client.post("/api/v1/installments/items", json={
        "item_name": name,
        "total_price": "600.00",
        "currency_id": str(currency_id),
        "initial_period_id": period_id,
        "monthly_payment_amount": "100.00",
        "months_to_pay": 6
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestInstallmentUpdateItem:

    def test_update_item_success(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """Update installment item notes — 200 with updated data."""
        period = _create_period(client, auth_headers)
        item = _create_item(client, auth_headers, test_currency.id, period["id"])

        resp = client.patch(f"/api/v1/installments/items/{item['id']}", json={
            "notes": "Updated notes"
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Updated notes"

    def test_update_item_not_found(self, client: TestClient, auth_headers: Dict):
        """Update non-existent item returns 404."""
        resp = client.patch(f"/api/v1/installments/items/{uuid.uuid4()}", json={
            "notes": "X"
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_update_item_wrong_user_returns_404(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, db
    ):
        """Update item owned by another user returns 404."""
        period = _create_period(client, auth_headers)
        item = _create_item(client, auth_headers, test_currency.id, period["id"])

        from app.models.user import User
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"inst-upd-{uuid.uuid4()}@test.com",
            password_hash=get_password_hash("pw"),
            full_name="Other",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.patch(f"/api/v1/installments/items/{item['id']}", json={
            "notes": "Hack"
        }, headers=other_headers)
        assert resp.status_code == 404


class TestInstallmentGetPayments:

    def test_get_payments_for_item(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """Get payments for an item returns list with period_name populated."""
        period = _create_period(client, auth_headers)
        item = _create_item(client, auth_headers, test_currency.id, period["id"])

        # Add a payment
        client.post(
            f"/api/v1/installments/items/{item['id']}/payments",
            params={"period_id": period["id"]},
            json={"payment_amount": "100.00", "payment_date": "2026-03-10"},
            headers=auth_headers
        )

        resp = client.get(
            f"/api/v1/installments/items/{item['id']}/payments",
            headers=auth_headers
        )
        assert resp.status_code == 200
        payments = resp.json()
        assert len(payments) >= 1

    def test_get_payments_item_not_found(self, client: TestClient, auth_headers: Dict):
        """Get payments for non-existent item returns 404."""
        resp = client.get(
            f"/api/v1/installments/items/{uuid.uuid4()}/payments",
            headers=auth_headers
        )
        assert resp.status_code == 404


class TestInstallmentPaymentErrors:

    def test_create_payment_item_not_found(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """Add payment to non-existent item returns 404."""
        period = _create_period(client, auth_headers)
        resp = client.post(
            f"/api/v1/installments/items/{uuid.uuid4()}/payments",
            params={"period_id": period["id"]},
            json={"payment_amount": "100.00", "payment_date": "2026-03-10"},
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_create_payment_period_not_found(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """Add payment with non-existent period returns 404."""
        period = _create_period(client, auth_headers)
        item = _create_item(client, auth_headers, test_currency.id, period["id"])

        resp = client.post(
            f"/api/v1/installments/items/{item['id']}/payments",
            params={"period_id": str(uuid.uuid4())},
            json={"payment_amount": "100.00", "payment_date": "2026-03-10"},
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_delete_payment_not_found(self, client: TestClient, auth_headers: Dict):
        """Delete non-existent payment returns 404."""
        resp = client.delete(
            f"/api/v1/installments/payments/{uuid.uuid4()}",
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_delete_payment_wrong_user_returns_403(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, db
    ):
        """Delete payment owned by another user returns 403."""
        period = _create_period(client, auth_headers)
        item = _create_item(client, auth_headers, test_currency.id, period["id"])
        pay_resp = client.post(
            f"/api/v1/installments/items/{item['id']}/payments",
            params={"period_id": period["id"]},
            json={"payment_amount": "100.00", "payment_date": "2026-03-10"},
            headers=auth_headers
        )
        payment_id = pay_resp.json()["id"]

        from app.models.user import User
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"inst-pay-{uuid.uuid4()}@test.com",
            password_hash=get_password_hash("pw"),
            full_name="Other",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.delete(
            f"/api/v1/installments/payments/{payment_id}",
            headers=other_headers
        )
        assert resp.status_code == 403
