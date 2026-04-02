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
pytestmark = pytest.mark.integration

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

def test_installment_paid_off_flow(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Paying the full amount should mark the installment as PAID_OFF."""
    period = create_period_helper(client, auth_headers)

    # Create item with small total
    create_resp = client.post("/api/v1/installments/items", json={
        "item_name": "Cheap Accessory",
        "total_price": 300.00,
        "currency_id": str(test_currency.id),
        "initial_period_id": period["id"],
        "monthly_payment_amount": 300.00,
        "months_to_pay": 1,
    }, headers=auth_headers)
    assert create_resp.status_code == 200
    item_id = create_resp.json()["id"]

    # Pay full amount in one go
    client.post(
        f"/api/v1/installments/items/{item_id}/payments",
        params={"period_id": period["id"]},
        json={"payment_amount": 300.00, "payment_date": "2026-08-15"},
        headers=auth_headers,
    )

    # Verify status changed to PAID_OFF
    items = client.get("/api/v1/installments/items", headers=auth_headers).json()
    item = next(i for i in items if i["id"] == item_id)
    assert float(item["remaining_balance"]) == 0
    assert item["status"] == "PAID_OFF"


def test_installment_multiple_payments(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Multiple payments should cumulatively reduce the remaining balance."""
    period = create_period_helper(client, auth_headers)

    create_resp = client.post("/api/v1/installments/items", json={
        "item_name": "Phone Plan",
        "total_price": 600.00,
        "currency_id": str(test_currency.id),
        "initial_period_id": period["id"],
        "monthly_payment_amount": 100.00,
        "months_to_pay": 6,
    }, headers=auth_headers)
    item_id = create_resp.json()["id"]

    # Make 3 payments of 100 each
    for day in [5, 10, 15]:
        resp = client.post(
            f"/api/v1/installments/items/{item_id}/payments",
            params={"period_id": period["id"]},
            json={"payment_amount": 100.00, "payment_date": f"2026-08-{day:02d}"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    # Verify balance is 600 - 300 = 300
    items = client.get("/api/v1/installments/items", headers=auth_headers).json()
    item = next(i for i in items if i["id"] == item_id)
    assert float(item["remaining_balance"]) == 300.00
    assert item["status"] == "ACTIVE"


def test_installment_list_payments(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Listing payments for an item returns all associated payments."""
    period = create_period_helper(client, auth_headers)

    create_resp = client.post("/api/v1/installments/items", json={
        "item_name": "Furniture",
        "total_price": 900.00,
        "currency_id": str(test_currency.id),
        "initial_period_id": period["id"],
        "monthly_payment_amount": 300.00,
        "months_to_pay": 3,
    }, headers=auth_headers)
    item_id = create_resp.json()["id"]

    # Add 2 payments
    for day, note in [(5, "First"), (20, "Second")]:
        client.post(
            f"/api/v1/installments/items/{item_id}/payments",
            params={"period_id": period["id"]},
            json={"payment_amount": 300.00, "payment_date": f"2026-08-{day:02d}", "notes": note},
            headers=auth_headers,
        )

    payments_resp = client.get(
        f"/api/v1/installments/items/{item_id}/payments", headers=auth_headers
    )
    assert payments_resp.status_code == 200
    assert len(payments_resp.json()) == 2


def test_installment_update_item(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Updating an installment item's metadata works correctly."""
    period = create_period_helper(client, auth_headers)

    create_resp = client.post("/api/v1/installments/items", json={
        "item_name": "Old Name",
        "total_price": 400.00,
        "currency_id": str(test_currency.id),
        "initial_period_id": period["id"],
        "monthly_payment_amount": 100.00,
        "months_to_pay": 4,
    }, headers=auth_headers)
    item_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/installments/items/{item_id}",
        json={"item_name": "Updated Name", "notes": "Changed my mind"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["item_name"] == "Updated Name"


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
