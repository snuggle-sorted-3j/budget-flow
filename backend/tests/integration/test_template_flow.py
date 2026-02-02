"""
Integration Tests for Template Workflow

Tests cover:
- Creating template from existing period
- Applying template to new period
- Verifying data is copied
- Managing default templates
"""
import pytest
from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory
import uuid

def create_full_period(client, auth_headers, currency_id, category_id, suffix="Source"):
    # 1. Create Period
    period_payload = {
        "period_name": f"Tmpl {suffix} {uuid.uuid4()}",
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "snapshot_date": "2026-10-31"
    }
    p_resp = client.post("/api/v1/periods/", json=period_payload, headers=auth_headers)
    period_id = p_resp.json()["id"]
    
    # 2. Add Income
    client.post(f"/api/v1/periods/{period_id}/incomes", json={
        "source_name": "Template Salary",
        "amount": 5000,
        "currency_id": str(currency_id)
    }, headers=auth_headers)
    
    # 3. Add Expense
    client.post(f"/api/v1/periods/{period_id}/expenses", json={
        "item_name": "Template Rent",
        "amount": 1500,
        "currency_id": str(currency_id),
        "category_id": str(category_id),
        "is_recurring": True
    }, headers=auth_headers)
    
    return period_id

def test_template_create_and_apply(
    client: TestClient, auth_headers: Dict[str, str], test_currency: Currency, test_category: ExpenseCategory
):
    """Test: Create -> Apply -> Verify."""
    # 1. Setup Data
    source_period_id = create_full_period(client, auth_headers, test_currency.id, test_category.id)
    
    # 2. Create Template
    tmpl_payload = {
        "template_name": "Monthly Base",
        "template_type": "FULL",
        "source_period_id": source_period_id
    }
    
    create_resp = client.post("/api/v1/templates/from-period", json=tmpl_payload, headers=auth_headers)
    assert create_resp.status_code == 200
    template_id = create_resp.json()["id"]
    
    # 3. Create Target Period
    target_payload = {
        "period_name": f"Tmpl Target {uuid.uuid4()}",
        "start_date": "2026-11-01",
        "end_date": "2026-11-30",
        "snapshot_date": "2026-11-30"
    }
    t_resp = client.post("/api/v1/periods/", json=target_payload, headers=auth_headers)
    target_period_id = t_resp.json()["id"]
    
    # 4. Apply Template
    apply_payload = {
        "target_period_id": target_period_id
    }
    apply_resp = client.post(f"/api/v1/templates/{template_id}/apply", json=apply_payload, headers=auth_headers)
    assert apply_resp.status_code == 200
    summary = apply_resp.json()
    
    # 5. Verify Data Copied
    # Incomes
    incomes = client.get(f"/api/v1/periods/{target_period_id}/incomes", headers=auth_headers)
    expenses = client.get(f"/api/v1/periods/{target_period_id}/expenses", headers=auth_headers)
    
    assert len(incomes.json()) == 1
    assert incomes.json()[0]["source_name"] == "Template Salary"
    
    assert len(expenses.json()) == 1
    assert expenses.json()[0]["item_name"] == "Template Rent"

def test_template_management(client: TestClient, auth_headers: Dict[str, str], test_currency: Currency, test_category: ExpenseCategory):
    """Test: List, Update, Delete templates."""
    sid = create_full_period(client, auth_headers, test_currency.id, test_category.id, "Mng")
    
    # Create
    resp = client.post("/api/v1/templates/from-period", json={
        "template_name": "To Manage", "template_type": "FULL", "source_period_id": sid
    }, headers=auth_headers)
    tid = resp.json()["id"]
    
    # List
    list_resp = client.get("/api/v1/templates/", headers=auth_headers)
    assert any(t["id"] == tid for t in list_resp.json())
    
    # Update (Set Default)
    patch_resp = client.patch(f"/api/v1/templates/{tid}", json={"is_default": True}, headers=auth_headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_default"] is True
    
    # Delete
    del_resp = client.delete(f"/api/v1/templates/{tid}", headers=auth_headers)
    assert del_resp.status_code == 200
    
    # Verify Gone
    list_resp_2 = client.get("/api/v1/templates/", headers=auth_headers)
    assert not any(t["id"] == tid for t in list_resp_2.json())
