"""
Integration Tests for Suspended Expense Workflow

Tests cover:
- Creation (Loan Given/Received)
- Settlement (Money returned)
- Conversion to Expense (Money lost/spent)
- Deletion
"""

import pytest
pytestmark = pytest.mark.integration

from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory
import uuid

def create_period_helper(client, auth_headers, suffix="Susp"):
    payload = {
        "period_name": f"{suffix} {uuid.uuid4()}",
        "start_date": "2026-12-01",
        "end_date": "2026-12-31",
        "snapshot_date": "2026-12-31"
    }
    resp = client.post("/api/v1/periods/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()

def test_suspended_settlement_flow(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Test: Create -> Settle -> Verify."""
    p1 = create_period_helper(client, auth_headers, "P1")
    p2 = create_period_helper(client, auth_headers, "P2")
    
    # 1. Create Suspended Expense (Loan Given)
    susp_payload = {
        "item_name": "Friend Loan",
        "amount": 100.00,
        "currency_id": str(test_currency.id),
        "transaction_type": "LOAN_OUT",
        "notes": "Lent to Bob"
    }
    
    create_resp = client.post(f"/api/v1/suspended-expenses/{p1['id']}", json=susp_payload, headers=auth_headers)
    assert create_resp.status_code == 200
    susp_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "PENDING"
    
    # 2. Settle in P2
    settle_resp = client.patch(
        f"/api/v1/suspended-expenses/{susp_id}/settle/{p2['id']}", 
        headers=auth_headers
    )
    assert settle_resp.status_code == 200
    assert settle_resp.json()["status"] == "SETTLED"
    assert settle_resp.json()["settled_period_id"] == p2['id']

def test_suspended_conversion_flow(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency, test_category: ExpenseCategory
):
    """Test: Create -> Convert to Expense -> Verify."""
    p1 = create_period_helper(client, auth_headers, "P1")
    
    # 1. Create
    resp = client.post(f"/api/v1/suspended-expenses/{p1['id']}", json={
        "item_name": "Lost Money", "amount": 50, "currency_id": str(test_currency.id), "transaction_type": "LOAN_OUT"
    }, headers=auth_headers)
    susp_id = resp.json()["id"]
    
    # 2. Convert to Expense (e.g. debt forgiven / lost)
    # Using query param for category_id or body?
    # Checked openapi: convert_suspended_to_expense signature: (expense_id, period_id, category_id, ...)
    # Wait, check valid params. It's likely query params if not body model.
    # Signature: convert_suspended_to_expense(expense_id, period_id, category_id, ...)
    # API Router: @router.patch("/{expense_id}/convert") 
    # FastAPI usually expects scalars as query params unless Body() specified.
    
    convert_resp = client.patch(
        f"/api/v1/suspended-expenses/{susp_id}/convert",
        params={
            "period_id": p1['id'],
            "category_id": str(test_category.id)
        },
        headers=auth_headers
    )
    assert convert_resp.status_code == 204
    
    # 3. Verify Status
    get_resp = client.get("/api/v1/suspended-expenses/", headers=auth_headers)
    item = next(i for i in get_resp.json() if i["id"] == susp_id)
    assert item["status"] == "CONVERTED_TO_EXPENSE"
    
    # 4. Verify Expense Created
    exp_resp = client.get(f"/api/v1/periods/{p1['id']}/expenses", headers=auth_headers)
    assert any(e["item_name"] == "Lost Money" for e in exp_resp.json())

def test_delete_suspended(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency
):
    """Test: Delete."""
    p1 = create_period_helper(client, auth_headers)
    resp = client.post(f"/api/v1/suspended-expenses/{p1['id']}", json={
        "item_name": "Del", "amount": 10, "currency_id": str(test_currency.id), "transaction_type": "OTHER"
    }, headers=auth_headers)
    sid = resp.json()["id"]
    
    del_resp = client.delete(f"/api/v1/suspended-expenses/{sid}", headers=auth_headers)
    assert del_resp.status_code == 204
    
    list_resp = client.get("/api/v1/suspended-expenses/", headers=auth_headers)
    assert not any(i["id"] == sid for i in list_resp.json())
