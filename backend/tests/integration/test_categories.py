import uuid
from typing import Dict
from fastapi.testclient import TestClient
from app.models.expense_category import ExpenseCategory
from app.models.currency import Currency
from sqlalchemy.orm import Session

def test_initialize_categories(client: TestClient, auth_headers: Dict[str, str]):
    response = client.post("/api/v1/expense-categories/initialize", headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert len(data) >= 7
    names = [c["category_name"] for c in data]
    assert "Food & Dining" in names
    assert "Untracked Expenses" in names

def test_create_hierarchical_category(client: TestClient, auth_headers: Dict[str, str]):
    # 1. Create Parent
    parent_payload = {"category_name": "Parent Cat", "icon": "P"}
    p_resp = client.post("/api/v1/expense-categories/", json=parent_payload, headers=auth_headers)
    assert p_resp.status_code == 201
    parent_id = p_resp.json()["id"]

    # 2. Create Child
    child_payload = {
        "category_name": "Child Cat",
        "parent_category_id": parent_id,
        "icon": "C"
    }
    c_resp = client.post("/api/v1/expense-categories/", json=child_payload, headers=auth_headers)
    assert c_resp.status_code == 201
    assert c_resp.json()["parent_category_id"] == parent_id

def test_update_category(client: TestClient, auth_headers: Dict[str, str]):
    # Create
    resp = client.post("/api/v1/expense-categories/", json={"category_name": "Old Name"}, headers=auth_headers)
    cat_id = resp.json()["id"]

    # Update
    update_resp = client.patch(f"/api/v1/expense-categories/{cat_id}", json={"category_name": "New Name"}, headers=auth_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["category_name"] == "New Name"

def test_cannot_delete_system_category(client: TestClient, auth_headers: Dict[str, str]):
    # Initialize to ensure they exist
    client.post("/api/v1/expense-categories/initialize", headers=auth_headers)
    
    # Get "Untracked Expenses"
    list_resp = client.get("/api/v1/expense-categories/", headers=auth_headers)
    system_cat = next(c for c in list_resp.json() if c["is_system_category"])
    
    # Try to delete
    del_resp = client.delete(f"/api/v1/expense-categories/{system_cat['id']}", headers=auth_headers)
    assert del_resp.status_code == 400
    assert "system category" in del_resp.json()["detail"]

def test_soft_delete_flow(client: TestClient, auth_headers: Dict[str, str]):
    # Create
    resp = client.post("/api/v1/expense-categories/", json={"category_name": "To Delete"}, headers=auth_headers)
    cat_id = resp.json()["id"]

    # Delete
    del_resp = client.delete(f"/api/v1/expense-categories/{cat_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # Verify not in default list
    list_resp = client.get("/api/v1/expense-categories/", headers=auth_headers)
    ids = [c["id"] for c in list_resp.json()]
    assert cat_id not in ids

    # Verify in inactive list
    list_all_resp = client.get("/api/v1/expense-categories/?include_inactive=true", headers=auth_headers)
    all_ids = [c["id"] for c in list_all_resp.json()]
    assert cat_id in all_ids

def test_cannot_delete_category_with_expenses(
    client: TestClient, 
    auth_headers: Dict[str, str], 
    test_currency: Currency
):
    # 1. Create Category
    cat_resp = client.post("/api/v1/expense-categories/", json={"category_name": "Has Expense"}, headers=auth_headers)
    cat_id = cat_resp.json()["id"]

    # 2. Create Period
    period_payload = {
        "period_name": f"Cat Test Period {uuid.uuid4()}",
        "start_date": "2027-01-01",
        "end_date": "2027-01-31",
        "snapshot_date": "2027-01-31"
    }
    p_resp = client.post("/api/v1/periods/", json=period_payload, headers=auth_headers)
    period_id = p_resp.json()["id"]

    # 3. Create Expense using Category
    exp_payload = {
        "item_name": "Test Item",
        "amount": 10,
        "currency_id": str(test_currency.id),
        "category_id": cat_id,
        "expense_date": "2027-01-15"
    }
    client.post(f"/api/v1/periods/{period_id}/expenses", json=exp_payload, headers=auth_headers)

    # 4. Try to delete Category
    del_resp = client.delete(f"/api/v1/expense-categories/{cat_id}", headers=auth_headers)
    assert del_resp.status_code == 400
    assert "existing expenses" in del_resp.json()["detail"]
def test_soft_delete_cascade(client: TestClient, auth_headers: Dict[str, str]):
    # 1. Create Parent
    p_resp = client.post("/api/v1/expense-categories/", json={"category_name": "Parent"}, headers=auth_headers)
    p_id = p_resp.json()["id"]

    # 2. Create Child
    c_resp = client.post("/api/v1/expense-categories/", json={"category_name": "Child", "parent_category_id": p_id}, headers=auth_headers)
    c_id = c_resp.json()["id"]

    # 3. Deactivate Parent
    client.delete(f"/api/v1/expense-categories/{p_id}", headers=auth_headers)

    # 4. Verify Child is also inactive
    list_resp = client.get("/api/v1/expense-categories/", headers=auth_headers)
    active_ids = [c["id"] for c in list_resp.json()]
    assert p_id not in active_ids
    assert c_id not in active_ids

    # 5. Verify Child is inactive in DB
    list_all_resp = client.get("/api/v1/expense-categories/?include_inactive=true", headers=auth_headers)
    inactive_child = next(c for c in list_all_resp.json() if c["id"] == c_id)
    assert inactive_child["is_active"] is False
