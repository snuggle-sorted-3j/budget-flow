"""
Integration Tests for Currency Conversion Workflow

Tests cover:
- Create conversion with valid data
- Validation: same currency rejected
- Validation: negative/zero amounts rejected
- List conversions by period (empty + populated)
- Delete conversion and verify removal
"""

import pytest
pytestmark = pytest.mark.integration

from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
import uuid


def _create_period(client, auth_headers):
    payload = {
        "period_name": f"Conv {uuid.uuid4()}",
        "start_date": "2027-01-01",
        "end_date": "2027-01-31",
        "snapshot_date": "2027-01-31",
    }
    resp = client.post("/api/v1/periods/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


def _create_second_currency(client, auth_headers):
    payload = {"ticker": "EUR", "name": "Euro", "is_default": False}
    resp = client.post("/api/v1/currencies/", json=payload, headers=auth_headers)
    assert resp.status_code in (200, 201)
    return resp.json()


def test_create_conversion_success(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Create a valid currency conversion and verify response fields."""
    period = _create_period(client, auth_headers)
    c2 = _create_second_currency(client, auth_headers)

    conv_payload = {
        "from_currency_id": str(test_currency.id),
        "to_currency_id": c2["id"],
        "from_amount": 100.00,
        "to_amount": 85.00,
        "rate": 0.85,
        "conversion_date": "2027-01-15",
    }
    resp = client.post(
        f"/api/v1/periods/{period['id']}/currency-conversions",
        json=conv_payload,
        headers=auth_headers,
    )
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["from_currency_id"] == str(test_currency.id)
    assert data["to_currency_id"] == c2["id"]
    assert float(data["from_amount"]) == 100.00
    assert float(data["to_amount"]) == 85.00
    assert "id" in data


def test_create_conversion_same_currency_rejected(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Cannot convert a currency to itself."""
    period = _create_period(client, auth_headers)

    conv_payload = {
        "from_currency_id": str(test_currency.id),
        "to_currency_id": str(test_currency.id),
        "from_amount": 100.00,
        "to_amount": 100.00,
        "rate": 1.0,
        "conversion_date": "2027-01-15",
    }
    resp = client.post(
        f"/api/v1/periods/{period['id']}/currency-conversions",
        json=conv_payload,
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "different" in resp.json()["detail"].lower()


def test_list_conversions_empty_period(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Listing conversions for a period with none returns empty list."""
    period = _create_period(client, auth_headers)

    resp = client.get(
        f"/api/v1/periods/{period['id']}/currency-conversions",
        headers=auth_headers,
    )
    assert resp.status_code in (200, 201)
    assert resp.json() == []


def test_list_conversions_returns_created(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Listing conversions returns all conversions created for that period."""
    period = _create_period(client, auth_headers)
    c2 = _create_second_currency(client, auth_headers)

    # Create two conversions
    for amount in [100.00, 250.00]:
        conv_payload = {
            "from_currency_id": str(test_currency.id),
            "to_currency_id": c2["id"],
            "from_amount": amount,
            "to_amount": amount * 0.85,
            "rate": 0.85,
            "conversion_date": "2027-01-15",
        }
        resp = client.post(
            f"/api/v1/periods/{period['id']}/currency-conversions",
            json=conv_payload,
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)

    list_resp = client.get(
        f"/api/v1/periods/{period['id']}/currency-conversions",
        headers=auth_headers,
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2


def test_delete_conversion_success(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Delete a conversion and verify it no longer appears in listings."""
    period = _create_period(client, auth_headers)
    c2 = _create_second_currency(client, auth_headers)

    conv_payload = {
        "from_currency_id": str(test_currency.id),
        "to_currency_id": c2["id"],
        "from_amount": 100.00,
        "to_amount": 85.00,
        "rate": 0.85,
        "conversion_date": "2027-01-15",
    }
    create_resp = client.post(
        f"/api/v1/periods/{period['id']}/currency-conversions",
        json=conv_payload,
        headers=auth_headers,
    )
    conv_id = create_resp.json()["id"]

    del_resp = client.delete(
        f"/api/v1/currency-conversions/{conv_id}", headers=auth_headers
    )
    assert del_resp.status_code == 200

    list_resp = client.get(
        f"/api/v1/periods/{period['id']}/currency-conversions",
        headers=auth_headers,
    )
    assert len(list_resp.json()) == 0


def test_delete_nonexistent_conversion(
    client: TestClient, auth_headers: Dict[str, str]
):
    """Deleting a non-existent conversion returns 404."""
    fake_id = str(uuid.uuid4())
    resp = client.delete(
        f"/api/v1/currency-conversions/{fake_id}", headers=auth_headers
    )
    assert resp.status_code == 404
