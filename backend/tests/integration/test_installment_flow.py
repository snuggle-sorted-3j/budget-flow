"""
Integration Tests for Installment Workflow

Tests cover:
- Creating installment items
- Listing items
- Adding payments
- Verifying payments update balance
- Deleting payments
"""
import pytest
from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
import uuid

def create_period_helper(client, auth_headers):
    payload = {
        "period_name": f"Inst Period {uuid.uuid4()}",
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
        "snapshot_date": "2026-08-31"
    }
    resp = client.post("/api/v1/periods/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()

def test_installment_full_lifecycle(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Test: Create item -> Add Payment -> Verify Balance -> Delete Payment."""
    period = create_period_helper(client, auth_headers)
    
    # 1. Create Installment Item
    item_payload = {
        "item_name": "New Laptop",
        "total_price": 1200.00,
        "currency_id": str(test_currency.id),
        "initial_period_id": period["id"],
        "monthly_payment_amount": 100.00,
        "months_to_pay": 12,
        "notes": "Work laptop"
    }
    
    create_resp = client.post("/api/v1/installments/items", json=item_payload, headers=auth_headers)
    assert create_resp.status_code == 200
    item = create_resp.json()
    item_id = item["id"]
    
    assert float(item["remaining_balance"]) == 1200.00
    assert item["status"] == "ACTIVE"
    
    # 2. Add Payment via API
    # Note: Endpoint is POST /items/{id}/payments with period_id query param
    payment_payload = {
        "payment_amount": 200.00,
        "payment_date": "2026-08-15",
        "notes": "First chunk"
    }
    
    pay_resp = client.post(
        f"/api/v1/installments/items/{item_id}/payments", 
        params={"period_id": period["id"]},
        json=payment_payload, 
        headers=auth_headers
    )
    assert pay_resp.status_code == 200
    
    # 3. Verify Item Balance Updated
    # Need to fetch item again
    get_items = client.get("/api/v1/installments/items", headers=auth_headers)
    assert get_items.status_code == 200
    updated_item = next(i for i in get_items.json() if i["id"] == item_id)
    
    assert float(updated_item["remaining_balance"]) == 1000.00 # 1200 - 200
    
    # 4. Delete Payment
    payment_id = pay_resp.json()["id"]
    del_resp = client.delete(f"/api/v1/installments/payments/{payment_id}", headers=auth_headers)
    assert del_resp.status_code == 204
    
    # 5. Verify Balance Reverted
    get_items_2 = client.get("/api/v1/installments/items", headers=auth_headers)
    reverted_item = next(i for i in get_items_2.json() if i["id"] == item_id)
    assert float(reverted_item["remaining_balance"]) == 1200.00

def test_installment_list_filtering(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Test: Filter installments by status."""
    period = create_period_helper(client, auth_headers)
    
    # Create Active Item
    client.post("/api/v1/installments/items", json={
        "item_name": "Active Loan",
        "total_price": 500.00,
        "currency_id": str(test_currency.id),
        "initial_period_id": period["id"],
        "monthly_payment_amount": 50.00,
        "months_to_pay": 10
    }, headers=auth_headers)
    
    # Filter Active
    resp = client.get("/api/v1/installments/items?status=ACTIVE", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert all(i["status"] == "ACTIVE" for i in resp.json())
