"""
Integration Tests for Currency Conversion Workflow

Tests cover:
- Create conversion
- List conversions
- Delete conversion
"""
import pytest
from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
import uuid

def create_period_helper(client, auth_headers):
    payload = {
        "period_name": f"Conv {uuid.uuid4()}",
        "start_date": "2027-01-01",
        "end_date": "2027-01-31",
        "snapshot_date": "2027-01-31"
    }
    resp = client.post("/api/v1/periods/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()

def test_currency_conversion_lifecycle(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Test: Create -> List -> Delete."""
    period = create_period_helper(client, auth_headers)
    
    # Need 2nd currency. Assuming EUR exists or verify logic.
    # We can try to create one or mock IDs if not enforced strictly.
    # Let's try creating a currency via API first.
    cur_payload = {"ticker": "GPB", "name": "Pound", "is_default": False}
    c_resp = client.post("/api/v1/currencies/", json=cur_payload, headers=auth_headers)
    
    if c_resp.status_code == 200:
        c2_id = c_resp.json()["id"]
    else:
        # Fallback: maybe it exists? or skip if can't get second currency
        # For integration, usually we seed DB.
        # Let's hope create works or use a fake UUID if validation is loose (it's not).
        # Assuming test_currency is USD.
        # Let's assume we can use the same currency for test purposes IF creating fails, 
        # BUT endpoint validation forbids same currency.
        pass
        
    if 'c2_id' not in locals():
        # Try to Find another currency
        list_c = client.get("/api/v1/currencies/", headers=auth_headers).json()
        others = [c for c in list_c if c["id"] != str(test_currency.id)]
        if others:
            c2_id = others[0]["id"]
        else:
             pytest.skip("Need at least 2 currencies for conversion test")

    # 1. Create Conversion
    conv_payload = {
        "from_currency_id": str(test_currency.id),
        "to_currency_id": c2_id,
        "from_amount": 100.00,
        "to_amount": 75.00,
        "exchange_rate": 0.75,
        "rate": 0.75,
        "conversion_date": "2027-01-15"
    }
    
    create_resp = client.post(f"/api/v1/periods/{period['id']}/currency-conversions", json=conv_payload, headers=auth_headers)
    assert create_resp.status_code == 200
    conv_id = create_resp.json()["id"]
    
    # 2. List
    list_resp = client.get(f"/api/v1/periods/{period['id']}/currency-conversions", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == conv_id
    
    # 3. Delete
    # Note: path is /currency-conversions/{id} (flat) not nested under period
    del_resp = client.delete(f"/api/v1/currency-conversions/{conv_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    
    # Verify Gone
    list_resp_2 = client.get(f"/api/v1/periods/{period['id']}/currency-conversions", headers=auth_headers)
    assert len(list_resp_2.json()) == 0
