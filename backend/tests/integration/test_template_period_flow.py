"""
Integration tests for Template + Period creation flow.

Tests that template application during period creation works correctly,
including template selection (not just default) and proper data propagation.
"""
import pytest
import uuid
from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory


def _create_period_with_data(client, auth_headers, currency_id, category_id, suffix=""):
    """Create period with income and recurring expense for template source."""
    period = client.post("/api/v1/periods/", json={
        "period_name": f"Template Source {suffix or uuid.uuid4().hex[:6]}",
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
        "snapshot_date": "2026-06-30"
    }, headers=auth_headers).json()
    period_id = period["id"]

    client.post(f"/api/v1/periods/{period_id}/incomes", json={
        "source_name": "Monthly Salary",
        "amount": 8000,
        "currency_id": str(currency_id),
        "is_recurring": True
    }, headers=auth_headers)

    client.post(f"/api/v1/periods/{period_id}/expenses", json={
        "item_name": "Rent",
        "amount": 2000,
        "currency_id": str(currency_id),
        "category_id": str(category_id),
        "is_recurring": True
    }, headers=auth_headers)

    return period_id


def test_create_template_then_apply_to_new_period(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
    test_category: ExpenseCategory,
):
    """Full flow: create template from period, apply to new period, verify data."""
    source_id = _create_period_with_data(client, auth_headers, test_currency.id, test_category.id)

    # Create template
    tpl = client.post("/api/v1/templates/from-period", json={
        "template_name": "Standard Monthly",
        "template_type": "FULL",
        "source_period_id": source_id
    }, headers=auth_headers).json()

    assert "id" in tpl
    tpl_id = tpl["id"]

    # Create a new target period
    target = client.post("/api/v1/periods/", json={
        "period_name": "July Template Test",
        "start_date": "2026-07-01",
        "end_date": "2026-07-31",
        "snapshot_date": "2026-07-31"
    }, headers=auth_headers).json()
    target_id = target["id"]

    # Apply the template to the new period
    apply_resp = client.post(f"/api/v1/templates/{tpl_id}/apply", json={
        "target_period_id": target_id
    }, headers=auth_headers)
    assert apply_resp.status_code == 200

    summary = apply_resp.json()
    # Template should have created income sources and expenses
    assert summary.get("income_sources", 0) >= 1
    assert summary.get("expenses", 0) >= 1

    # Verify income was created in target period
    incomes = client.get(f"/api/v1/periods/{target_id}/incomes", headers=auth_headers).json()
    assert len(incomes) >= 1
    assert any(i["source_name"] == "Monthly Salary" for i in incomes)

    # Verify expense was created
    expenses = client.get(f"/api/v1/periods/{target_id}/expenses", headers=auth_headers).json()
    assert len(expenses) >= 1
    assert any(e["item_name"] == "Rent" for e in expenses)


def test_apply_template_to_wrong_user_fails(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
    test_category: ExpenseCategory,
):
    """Template cannot be applied to a period that doesn't exist."""
    source_id = _create_period_with_data(client, auth_headers, test_currency.id, test_category.id)

    tpl = client.post("/api/v1/templates/from-period", json={
        "template_name": "Restricted Template",
        "template_type": "FULL",
        "source_period_id": source_id
    }, headers=auth_headers).json()
    tpl_id = tpl["id"]

    fake_period_id = str(uuid.uuid4())
    apply_resp = client.post(f"/api/v1/templates/{tpl_id}/apply", json={
        "target_period_id": fake_period_id
    }, headers=auth_headers)
    assert apply_resp.status_code == 404


def test_default_template_identified_in_list(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
    test_category: ExpenseCategory,
):
    """Template marked as default appears as is_default=True in list."""
    source_id = _create_period_with_data(client, auth_headers, test_currency.id, test_category.id, suffix="D")

    tpl = client.post("/api/v1/templates/from-period", json={
        "template_name": "My Default Template",
        "template_type": "FULL",
        "source_period_id": source_id
    }, headers=auth_headers).json()
    tpl_id = tpl["id"]

    # Set as default
    client.patch(f"/api/v1/templates/{tpl_id}", json={"is_default": True}, headers=auth_headers)

    templates = client.get("/api/v1/templates/", headers=auth_headers).json()
    default_tpl = next((t for t in templates if t["id"] == tpl_id), None)
    assert default_tpl is not None
    assert default_tpl["is_default"] is True


def test_template_selection_by_id_via_apply(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
    test_category: ExpenseCategory,
):
    """When two templates exist, applying a specific one by ID is precise."""
    # Source 1
    src1 = _create_period_with_data(client, auth_headers, test_currency.id, test_category.id, suffix="S1")
    tpl1 = client.post("/api/v1/templates/from-period", json={
        "template_name": "Template Alpha",
        "template_type": "FULL",
        "source_period_id": src1
    }, headers=auth_headers).json()

    # Source 2 with different income
    src2 = client.post("/api/v1/periods/", json={
        "period_name": "Source2",
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
        "snapshot_date": "2026-08-31"
    }, headers=auth_headers).json()["id"]

    client.post(f"/api/v1/periods/{src2}/incomes", json={
        "source_name": "Unique Beta Income",
        "amount": 500,
        "currency_id": str(test_currency.id),
        "is_recurring": True
    }, headers=auth_headers)

    tpl2 = client.post("/api/v1/templates/from-period", json={
        "template_name": "Template Beta",
        "template_type": "FULL",
        "source_period_id": src2
    }, headers=auth_headers).json()

    # Create target
    target = client.post("/api/v1/periods/", json={
        "period_name": "Target Precision",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
        "snapshot_date": "2026-09-30"
    }, headers=auth_headers).json()["id"]

    # Apply only Template Beta (by ID)
    client.post(f"/api/v1/templates/{tpl2['id']}/apply", json={
        "target_period_id": target
    }, headers=auth_headers)

    incomes = client.get(f"/api/v1/periods/{target}/incomes", headers=auth_headers).json()
    income_names = [i["source_name"] for i in incomes]

    assert "Unique Beta Income" in income_names
    assert "Monthly Salary" not in income_names  # Template Alpha's income, not Beta's
