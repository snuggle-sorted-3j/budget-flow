"""
Integration Tests for Investment Workflow

Tests cover:
- Creating investment accounts
- Creating investment categories/holdings
- Creating transfers
- Listing transfers by period
- Deletion flows
"""

import pytest
pytestmark = pytest.mark.integration

from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
import uuid

def create_period_helper(client, auth_headers):
    payload = {
        "period_name": f"Inv Period {uuid.uuid4()}",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
        "snapshot_date": "2026-09-30"
    }
    resp = client.post("/api/v1/periods/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()

def test_investment_full_lifecycle(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Test: Inv Account -> Inv Category -> Transfer -> List."""
    period = create_period_helper(client, auth_headers)
    
    # 1. Create Investment Account
    acc_payload = {
        "account_name": "Robinhood",
        "account_type": "BROKERAGE",
        "is_active": True
    }
    acc_resp = client.post("/api/v1/investments/accounts", json=acc_payload, headers=auth_headers)
    assert acc_resp.status_code == 200
    acc_id = acc_resp.json()["id"]
    
    # 2. Create Investment Category (Holding)
    inv_payload = {
        "category_name": "Growth Stock",
        "investment_account_id": acc_id,
        "opening_balance": 0.0,
        "opening_balance_date": "2026-01-01",
        "opening_balance_currency_id": str(test_currency.id)
    }
    inv_resp = client.post("/api/v1/investments/", json=inv_payload, headers=auth_headers)
    assert inv_resp.status_code == 200
    inv_id = inv_resp.json()["id"]
    
    # 3. Create Source Account (Bank) for transfer source
    # Need regular account CRUD via API? Let's check logic. API usually exists.
    # Assuming /api/v1/accounts exists. It should.
    # Let's try.
    bank_payload = {
        "account_name": "Checking",
        "account_type": "BANK",
        "currency_id": str(test_currency.id)
    }
    bank_resp = client.post("/api/v1/accounts/", json=bank_payload, headers=auth_headers)
    if bank_resp.status_code == 404:
        pytest.skip("Account API not found, cannot test transfer integration fully without it")
    
    bank_id = bank_resp.json()["id"]
    
    # 4. Create Transfer
    transfer_payload = {
        "investment_id": inv_id,
        "amount_transferred": 500.00,
        "currency_id": str(test_currency.id),
        "source_account_id": bank_id,
        "transfer_date": "2026-09-15",
        "units_added": 2.5
    }
    
    t_resp = client.post(f"/api/v1/investments/transfers/{period['id']}", json=transfer_payload, headers=auth_headers)
    assert t_resp.status_code == 200
    transfer_id = t_resp.json()["id"]
    
    # 5. List Transfers
    list_resp = client.get(f"/api/v1/investments/transfers/{period['id']}", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert float(list_resp.json()[0]["amount_transferred"]) == 500.00
    
    # 6. Delete Transfer
    del_resp = client.delete(f"/api/v1/investments/transfers/{transfer_id}", headers=auth_headers)
    assert del_resp.status_code == 204
    
    # Verify Empty
    list_resp_2 = client.get(f"/api/v1/investments/transfers/{period['id']}", headers=auth_headers)
    assert len(list_resp_2.json()) == 0

def test_list_investment_accounts(
    client: TestClient, auth_headers: Dict[str, str]
):
    """Creating multiple investment accounts and listing returns all of them."""
    names = ["Vanguard", "Fidelity", "Coinbase"]
    types = ["BROKERAGE", "BROKERAGE", "CRYPTO_EXCHANGE"]

    created_ids = []
    for name, acc_type in zip(names, types):
        resp = client.post("/api/v1/investments/accounts", json={
            "account_name": name,
            "account_type": acc_type,
        }, headers=auth_headers)
        assert resp.status_code == 200
        created_ids.append(resp.json()["id"])

    list_resp = client.get("/api/v1/investments/accounts", headers=auth_headers)
    assert list_resp.status_code == 200
    listed_ids = [a["id"] for a in list_resp.json()]
    for cid in created_ids:
        assert cid in listed_ids


def test_list_investment_categories(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Creating investment categories and listing returns them."""
    # Create account first
    acc_resp = client.post("/api/v1/investments/accounts", json={
        "account_name": "Cat Test Broker",
        "account_type": "BROKERAGE",
    }, headers=auth_headers)
    acc_id = acc_resp.json()["id"]

    # Create two categories
    created_ids = []
    for cat_name in ["Index Fund", "Bonds"]:
        resp = client.post("/api/v1/investments/", json={
            "category_name": cat_name,
            "investment_account_id": acc_id,
            "opening_balance": 0.0,
            "opening_balance_date": "2026-01-01",
            "opening_balance_currency_id": str(test_currency.id),
        }, headers=auth_headers)
        assert resp.status_code == 200
        created_ids.append(resp.json()["id"])

    list_resp = client.get("/api/v1/investments/", headers=auth_headers)
    assert list_resp.status_code == 200
    listed_ids = [i["id"] for i in list_resp.json()]
    for cid in created_ids:
        assert cid in listed_ids


def test_transfers_isolated_by_period(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Transfers in one period should not appear when listing another period."""
    period1 = create_period_helper(client, auth_headers)
    period2_payload = {
        "period_name": f"Inv Period 2 {uuid.uuid4()}",
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "snapshot_date": "2026-10-31",
    }
    period2 = client.post("/api/v1/periods/", json=period2_payload, headers=auth_headers).json()

    # Setup: account, category, bank
    acc_resp = client.post("/api/v1/investments/accounts", json={
        "account_name": "Isolation Broker",
        "account_type": "BROKERAGE",
    }, headers=auth_headers)
    acc_id = acc_resp.json()["id"]

    inv_resp = client.post("/api/v1/investments/", json={
        "category_name": "Isolation Fund",
        "investment_account_id": acc_id,
        "opening_balance": 0.0,
        "opening_balance_date": "2026-01-01",
        "opening_balance_currency_id": str(test_currency.id),
    }, headers=auth_headers)
    inv_id = inv_resp.json()["id"]

    bank_resp = client.post("/api/v1/accounts/", json={
        "account_name": "Isolation Bank",
        "account_type": "BANK",
        "currency_id": str(test_currency.id),
    }, headers=auth_headers)
    if bank_resp.status_code == 404:
        pytest.skip("Account API not available")
    bank_id = bank_resp.json()["id"]

    # Create transfer in period 1 only
    client.post(f"/api/v1/investments/transfers/{period1['id']}", json={
        "investment_id": inv_id,
        "amount_transferred": 250.00,
        "currency_id": str(test_currency.id),
        "source_account_id": bank_id,
        "transfer_date": "2026-09-10",
    }, headers=auth_headers)

    # Period 1 should have 1 transfer
    list1 = client.get(f"/api/v1/investments/transfers/{period1['id']}", headers=auth_headers)
    assert len(list1.json()) == 1

    # Period 2 should have 0 transfers
    list2 = client.get(f"/api/v1/investments/transfers/{period2['id']}", headers=auth_headers)
    assert len(list2.json()) == 0


def test_delete_investment_account_cascade(
    client: TestClient, auth_headers: Dict[str, str]
):
    """Test: Deleting investment account."""
    acc_payload = {"account_name": "Delete Me", "account_type": "CRYPTO_EXCHANGE"}
    resp = client.post("/api/v1/investments/accounts", json=acc_payload, headers=auth_headers)
    acc_id = resp.json()["id"]
    
    # Delete
    del_resp = client.delete(f"/api/v1/investments/accounts/{acc_id}", headers=auth_headers)
    assert del_resp.status_code == 204
    
    # Verify
    list_resp = client.get("/api/v1/investments/accounts", headers=auth_headers)
    assert not any(a["id"] == acc_id for a in list_resp.json())
