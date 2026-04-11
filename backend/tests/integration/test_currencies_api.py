"""Integration tests for /api/v1/currencies endpoints."""

import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from app.models.currency import Currency
from app.models.user import User


BASE_URL = "/api/v1/currencies"


# ---------------------------------------------------------------------------
# POST /currencies/ — create currency
# ---------------------------------------------------------------------------

def test_create_currency_success(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    payload = {"ticker": "EUR", "name": "Euro", "is_default": False}
    resp = client.post(f"{BASE_URL}/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["ticker"] == "EUR"
    assert data["name"] == "Euro"
    assert data["is_default"] is False
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data


def test_create_currency_as_default(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    payload = {"ticker": "GBP", "name": "British Pound", "is_default": True}
    resp = client.post(f"{BASE_URL}/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["ticker"] == "GBP"
    assert data["is_default"] is True


def test_create_currency_default_unsets_previous_default(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,  # already is_default=True with ticker USD
):
    # test_currency fixture creates USD as default
    # Creating a new default should unset USD
    payload = {"ticker": "PLN", "name": "Polish Zloty", "is_default": True}
    resp = client.post(f"{BASE_URL}/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["is_default"] is True

    # USD should no longer be default
    get_resp = client.get(f"{BASE_URL}/{test_currency.id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["is_default"] is False


def test_create_currency_ticker_uppercased(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    payload = {"ticker": "chf", "name": "Swiss Franc", "is_default": False}
    resp = client.post(f"{BASE_URL}/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["ticker"] == "CHF"


def test_create_currency_requires_auth(
    client: TestClient,
):
    payload = {"ticker": "JPY", "name": "Japanese Yen", "is_default": False}
    resp = client.post(f"{BASE_URL}/", json=payload)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /currencies/ — list currencies
# ---------------------------------------------------------------------------

def test_list_currencies_empty(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    resp = client.get(f"{BASE_URL}/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_currencies_returns_only_own(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
):
    resp = client.get(f"{BASE_URL}/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == str(test_currency.id)
    assert data[0]["ticker"] == test_currency.ticker


def test_list_currencies_multiple(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
):
    # Create an additional currency
    client.post(f"{BASE_URL}/", json={"ticker": "EUR", "name": "Euro", "is_default": False}, headers=auth_headers)

    resp = client.get(f"{BASE_URL}/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_currencies_requires_auth(
    client: TestClient,
):
    resp = client.get(f"{BASE_URL}/")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /currencies/{currency_id} — get single currency
# ---------------------------------------------------------------------------

def test_get_currency_success(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
):
    resp = client.get(f"{BASE_URL}/{test_currency.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(test_currency.id)
    assert data["ticker"] == test_currency.ticker
    assert data["name"] == test_currency.name


def test_get_currency_not_found(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    non_existent = uuid.uuid4()
    resp = client.get(f"{BASE_URL}/{non_existent}", headers=auth_headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_get_currency_other_user_not_found(
    client: TestClient,
    db,
    test_currency: Currency,
):
    """A currency belonging to another user should return 404."""
    from app.core.security import get_password_hash, create_access_token

    other_user = User(
        id=uuid.uuid4(),
        email=f"other-{uuid.uuid4()}@example.com",
        password_hash=get_password_hash("otherpass"),
        full_name="Other User",
        is_active=True,
    )
    db.add(other_user)
    db.commit()

    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    resp = client.get(f"{BASE_URL}/{test_currency.id}", headers=other_headers)
    assert resp.status_code == 404


def test_get_currency_requires_auth(
    client: TestClient,
    test_currency: Currency,
):
    resp = client.get(f"{BASE_URL}/{test_currency.id}")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /currencies/{currency_id}/set-default — set default currency
# ---------------------------------------------------------------------------

def test_set_default_currency_success(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
):
    # Create a second currency that we'll set as default
    create_resp = client.post(
        f"{BASE_URL}/",
        json={"ticker": "CAD", "name": "Canadian Dollar", "is_default": False},
        headers=auth_headers,
    )
    new_id = create_resp.json()["id"]

    resp = client.patch(f"{BASE_URL}/{new_id}/set-default", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == new_id
    assert data["is_default"] is True


def test_set_default_unsets_previous_default(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
):
    # test_currency (USD) starts as default
    create_resp = client.post(
        f"{BASE_URL}/",
        json={"ticker": "AUD", "name": "Australian Dollar", "is_default": False},
        headers=auth_headers,
    )
    new_id = create_resp.json()["id"]

    client.patch(f"{BASE_URL}/{new_id}/set-default", headers=auth_headers)

    # USD should no longer be default
    usd_resp = client.get(f"{BASE_URL}/{test_currency.id}", headers=auth_headers)
    assert usd_resp.json()["is_default"] is False


def test_set_default_currency_not_found(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    non_existent = uuid.uuid4()
    resp = client.patch(f"{BASE_URL}/{non_existent}/set-default", headers=auth_headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_set_default_currency_requires_auth(
    client: TestClient,
    test_currency: Currency,
):
    resp = client.patch(f"{BASE_URL}/{test_currency.id}/set-default")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /currencies/{currency_id} — delete currency
# ---------------------------------------------------------------------------

def test_delete_currency_success(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
):
    resp = client.delete(f"{BASE_URL}/{test_currency.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(test_currency.id)

    # Should no longer be retrievable
    get_resp = client.get(f"{BASE_URL}/{test_currency.id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_delete_currency_not_found(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    non_existent = uuid.uuid4()
    resp = client.delete(f"{BASE_URL}/{non_existent}", headers=auth_headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_delete_currency_other_user_not_found(
    client: TestClient,
    db,
    test_currency: Currency,
):
    """Deleting another user's currency should return 404, not delete it."""
    from app.core.security import get_password_hash, create_access_token

    other_user = User(
        id=uuid.uuid4(),
        email=f"delother-{uuid.uuid4()}@example.com",
        password_hash=get_password_hash("otherpass"),
        full_name="Delete Other",
        is_active=True,
    )
    db.add(other_user)
    db.commit()

    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    resp = client.delete(f"{BASE_URL}/{test_currency.id}", headers=other_headers)
    assert resp.status_code == 404


def test_delete_currency_requires_auth(
    client: TestClient,
    test_currency: Currency,
):
    resp = client.delete(f"{BASE_URL}/{test_currency.id}")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /currencies/initialize — initialize default currencies
# ---------------------------------------------------------------------------

def test_initialize_currencies_success(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    resp = client.post(f"{BASE_URL}/initialize", headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    tickers = [c["ticker"] for c in data]
    assert "EUR" in tickers
    assert "USD" in tickers
    assert "PLN" in tickers


def test_initialize_currencies_skips_existing(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,  # USD already exists
):
    resp = client.post(f"{BASE_URL}/initialize", headers=auth_headers)
    assert resp.status_code == 201
    tickers = [c["ticker"] for c in resp.json()]
    # USD should appear only once
    assert tickers.count("USD") == 1


def test_initialize_currencies_idempotent(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    resp1 = client.post(f"{BASE_URL}/initialize", headers=auth_headers)
    count1 = len(resp1.json())

    resp2 = client.post(f"{BASE_URL}/initialize", headers=auth_headers)
    count2 = len(resp2.json())

    assert resp2.status_code == 201
    assert count1 == count2


def test_initialize_currencies_requires_auth(
    client: TestClient,
):
    resp = client.post(f"{BASE_URL}/initialize")
    assert resp.status_code == 401
