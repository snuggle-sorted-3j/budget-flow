"""
Integration tests for currency conversion error paths.
Covers: same currency 400, delete not found 404.
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from app.models.currency import Currency


def _create_period(client, headers):
    resp = client.post("/api/v1/periods/", json={
        "period_name": f"ConvPeriod-{uuid.uuid4().hex[:6]}",
        "start_date": "2026-07-01",
        "end_date": "2026-07-31",
        "snapshot_date": "2026-07-31"
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def _create_second_currency(client, headers, db, test_user):
    from app.models.currency import Currency as CurrencyModel
    cur = CurrencyModel(
        id=uuid.uuid4(),
        user_id=test_user.id,
        ticker="EUR",
        name="Euro",
        is_default=False
    )
    db.add(cur)
    db.commit()
    db.refresh(cur)
    return cur


class TestCurrencyConversionErrors:

    def test_create_conversion_same_currency_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency
    ):
        """POST conversion with same from/to currency returns 400."""
        period = _create_period(client, auth_headers)
        resp = client.post(
            f"/api/v1/periods/{period['id']}/currency-conversions",
            json={
                "from_currency_id": str(test_currency.id),
                "to_currency_id": str(test_currency.id),
                "from_amount": "100.00",
                "to_amount": "100.00",
                "rate": "1.00",
                "conversion_date": "2026-07-15"
            },
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "different" in resp.json()["detail"].lower()

    def test_delete_conversion_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """DELETE non-existent conversion returns 404."""
        resp = client.delete(
            f"/api/v1/currency-conversions/{uuid.uuid4()}",
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_create_conversion_success(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency,
        test_user, db
    ):
        """POST conversion with valid data returns 200."""
        eur = _create_second_currency(client, auth_headers, db, test_user)
        period = _create_period(client, auth_headers)

        resp = client.post(
            f"/api/v1/periods/{period['id']}/currency-conversions",
            json={
                "from_currency_id": str(test_currency.id),
                "to_currency_id": str(eur.id),
                "from_amount": "100.00",
                "to_amount": "93.00",
                "rate": "0.93",
                "conversion_date": "2026-07-15"
            },
            headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
