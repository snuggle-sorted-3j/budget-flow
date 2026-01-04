import uuid
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory
from typing import Dict

def create_period(client, auth_headers):
    """Helper to create a period for transaction tests."""
    payload = {
        "period_name": f"Transaction Period {uuid.uuid4()}",
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
        "snapshot_date": "2026-06-30"
    }
    response = client.post("/api/v1/periods/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    return response.json()

def test_create_income_success(client: TestClient, auth_headers: Dict[str, str], test_currency: Currency):
    period = create_period(client, auth_headers)
    period_id = period["id"]
    
    payload = {
        "source_name": "Job Salary",
        "amount": 5000.50,
        "currency_id": str(test_currency.id),
        "income_date": "2026-06-15",
        "tax_applicable": True,
        "notes": "June Salary"
    }
    
    response = client.post(f"/api/v1/periods/{period_id}/incomes", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["source_name"] == payload["source_name"]
    assert float(data["amount"]) == payload["amount"]
    assert data["calculation_period_id"] == period_id

def test_create_expense_success(client: TestClient, auth_headers: Dict[str, str], test_currency: Currency, test_category: ExpenseCategory):
    period = create_period(client, auth_headers)
    period_id = period["id"]
    
    payload = {
        "item_name": "Grocery Shopping",
        "amount": 150.75,
        "currency_id": str(test_currency.id),
        "category_id": str(test_category.id),
        "expense_date": "2026-06-10",
        "is_tax_deductible": False,
        "notes": "Weekly groceries"
    }
    
    response = client.post(f"/api/v1/periods/{period_id}/expenses", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["item_name"] == payload["item_name"]
    assert float(data["amount"]) == payload["amount"]
    assert data["calculation_period_id"] == period_id
    assert data["category_id"] == str(test_category.id)

def test_create_income_invalid_currency(client: TestClient, auth_headers: Dict[str, str]):
    period = create_period(client, auth_headers)
    period_id = period["id"]
    
    payload = {
        "source_name": "Job Salary",
        "amount": 5000.50,
        "currency_id": str(uuid.uuid4()), # Non-existent currency
        "income_date": "2026-06-15"
    }
    
    response = client.post(f"/api/v1/periods/{period_id}/incomes", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Currency not found" in response.json()["detail"]

def test_create_expense_invalid_category(client: TestClient, auth_headers: Dict[str, str], test_currency: Currency):
    period = create_period(client, auth_headers)
    period_id = period["id"]
    
    payload = {
        "item_name": "Grocery Shopping",
        "amount": 150.75,
        "currency_id": str(test_currency.id),
        "category_id": str(uuid.uuid4()), # Non-existent category
        "expense_date": "2026-06-10"
    }
    
    response = client.post(f"/api/v1/periods/{period_id}/expenses", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Category not found" in response.json()["detail"]

def test_create_transaction_negative_amount(client: TestClient, auth_headers: Dict[str, str], test_currency: Currency):
    period = create_period(client, auth_headers)
    period_id = period["id"]
    
    # Negative Income
    payload = {
        "source_name": "Negative Income",
        "amount": -100.00,
        "currency_id": str(test_currency.id)
    }
    response = client.post(f"/api/v1/periods/{period_id}/incomes", json=payload, headers=auth_headers)
    assert response.status_code == 422 # Pydantic validation error

def test_list_transactions(client: TestClient, auth_headers: Dict[str, str], test_currency: Currency, test_category: ExpenseCategory):
    period = create_period(client, auth_headers)
    period_id = period["id"]
    
    # Create 2 Incomes
    for i in range(2):
        client.post(f"/api/v1/periods/{period_id}/incomes", json={
            "source_name": f"Income {i}", "amount": 1000, "currency_id": str(test_currency.id)
        }, headers=auth_headers)
        
    # Create 3 Expenses
    for i in range(3):
        client.post(f"/api/v1/periods/{period_id}/expenses", json={
            "item_name": f"Expense {i}", "amount": 50, "currency_id": str(test_currency.id), "category_id": str(test_category.id)
        }, headers=auth_headers)
        
    # List Incomes
    inc_resp = client.get(f"/api/v1/periods/{period_id}/incomes", headers=auth_headers)
    assert inc_resp.status_code == 200
    assert len(inc_resp.json()) == 2
    
    # List Expenses
    exp_resp = client.get(f"/api/v1/periods/{period_id}/expenses", headers=auth_headers)
    assert exp_resp.status_code == 200
    assert len(exp_resp.json()) == 3

def test_delete_income_success(client: TestClient, auth_headers: Dict[str, str], test_currency: Currency):
    period = create_period(client, auth_headers)
    period_id = period["id"]
    
    # Create Income
    create_resp = client.post(f"/api/v1/periods/{period_id}/incomes", json={
        "source_name": "To Delete", "amount": 100, "currency_id": str(test_currency.id)
    }, headers=auth_headers)
    income_id = create_resp.json()["id"]
    
    # Delete Income
    del_resp = client.delete(f"/api/v1/incomes/{income_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["message"] == "Income deleted successfully"
    
    # Verify Deletion
    get_resp = client.get(f"/api/v1/periods/{period_id}/incomes", headers=auth_headers)
    assert len(get_resp.json()) == 0

def test_delete_expense_success(client: TestClient, auth_headers: Dict[str, str], test_currency: Currency, test_category: ExpenseCategory):
    period = create_period(client, auth_headers)
    period_id = period["id"]
    
    # Create Expense
    create_resp = client.post(f"/api/v1/periods/{period_id}/expenses", json={
        "item_name": "To Delete", "amount": 50, "currency_id": str(test_currency.id), "category_id": str(test_category.id)
    }, headers=auth_headers)
    expense_id = create_resp.json()["id"]
    
    # Delete Expense
    del_resp = client.delete(f"/api/v1/expenses/{expense_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    
    # Verify Deletion
    get_resp = client.get(f"/api/v1/periods/{period_id}/expenses", headers=auth_headers)
    assert len(get_resp.json()) == 0

def test_delete_non_existent_transaction(client: TestClient, auth_headers: Dict[str, str]):
    # Delete Random ID
    response = client.delete(f"/api/v1/incomes/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404
