"""
Integration tests for Tax Benefits (B2B) API endpoint.

Tests GET /api/v1/periods/{period_id}/tax-benefits
"""
import pytest
from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory


def _setup_period_with_data(client, auth_headers, currency_id, category_id):
    """Helper: create period, account, income, expenses; return (period_id, account_id)."""
    period = client.post("/api/v1/periods/", json={
        "period_name": "Tax Test Period",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "snapshot_date": "2026-03-31"
    }, headers=auth_headers).json()
    period_id = period["id"]

    acc = client.post("/api/v1/accounts/", json={
        "account_name": "B2B Account",
        "account_type": "BANK",
        "currency_id": str(currency_id)
    }, headers=auth_headers).json()

    # Tax-applicable income
    client.post(f"/api/v1/periods/{period_id}/incomes", json={
        "source_name": "Client Invoice",
        "amount": 10000,
        "currency_id": str(currency_id),
        "tax_applicable": True
    }, headers=auth_headers)

    # Non-taxable income
    client.post(f"/api/v1/periods/{period_id}/incomes", json={
        "source_name": "Gift",
        "amount": 500,
        "currency_id": str(currency_id),
        "tax_applicable": False
    }, headers=auth_headers)

    # Tax-deductible expense
    client.post(f"/api/v1/periods/{period_id}/expenses", json={
        "item_name": "Laptop",
        "amount": 3000,
        "currency_id": str(currency_id),
        "category_id": str(category_id),
        "is_tax_deductible": True
    }, headers=auth_headers)

    # Non-deductible expense
    client.post(f"/api/v1/periods/{period_id}/expenses", json={
        "item_name": "Coffee",
        "amount": 200,
        "currency_id": str(currency_id),
        "category_id": str(category_id),
        "is_tax_deductible": False
    }, headers=auth_headers)

    return period_id, acc["id"]


def test_tax_benefits_no_tax_system(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
    test_category: ExpenseCategory,
):
    """Without a B2B tax system configured, endpoint returns 204 or empty."""
    period_id, _ = _setup_period_with_data(
        client, auth_headers, test_currency.id, test_category.id
    )

    resp = client.get(f"/api/v1/periods/{period_id}/tax-benefits", headers=auth_headers)
    # Either 204 No Content or 200 with null/empty result
    assert resp.status_code in (200, 204)
    if resp.status_code == 200:
        data = resp.json()
        assert data is None or data.get("tax_system") == "NONE"


def test_tax_benefits_with_polish_b2b(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
    test_category: ExpenseCategory,
):
    """POLISH_B2B: verify calculated fields match expected values."""
    # First set user settings to POLISH_B2B 19%
    client.put("/api/v1/settings/", json={
        "tax_system": "POLISH_B2B",
        "tax_rate": "19.00",
        "default_currency_id": str(test_currency.id)
    }, headers=auth_headers)

    period_id, _ = _setup_period_with_data(
        client, auth_headers, test_currency.id, test_category.id
    )

    resp = client.get(f"/api/v1/periods/{period_id}/tax-benefits", headers=auth_headers)
    assert resp.status_code == 200

    data = resp.json()
    assert data["tax_system"] == "POLISH_B2B"
    assert float(data["tax_rate"]) == 19.0
    assert float(data["taxable_income"]) == 10000.0
    assert float(data["deductible_expenses"]) == 3000.0
    assert float(data["net_taxable_income"]) == 7000.0
    assert float(data["estimated_tax"]) == pytest.approx(1330.0)   # 7000 * 0.19
    assert float(data["tax_savings"]) == pytest.approx(570.0)       # 3000 * 0.19


def test_tax_benefits_deductible_items_listed(
    client: TestClient,
    auth_headers: Dict[str, str],
    test_currency: Currency,
    test_category: ExpenseCategory,
):
    """Response includes list of deductible expense items."""
    client.put("/api/v1/settings/", json={
        "tax_system": "POLISH_B2B",
        "tax_rate": "19.00",
        "default_currency_id": str(test_currency.id)
    }, headers=auth_headers)

    period_id, _ = _setup_period_with_data(
        client, auth_headers, test_currency.id, test_category.id
    )

    resp = client.get(f"/api/v1/periods/{period_id}/tax-benefits", headers=auth_headers)
    assert resp.status_code == 200

    items = resp.json()["deductible_items"]
    assert len(items) == 1
    assert items[0]["item_name"] == "Laptop"
    assert float(items[0]["amount"]) == 3000.0


def test_tax_benefits_requires_auth(
    client: TestClient,
    test_currency: Currency,
):
    """Endpoint requires authentication."""
    resp = client.get(f"/api/v1/periods/{test_currency.id}/tax-benefits")
    assert resp.status_code == 401


def test_tax_benefits_unknown_period(
    client: TestClient,
    auth_headers: Dict[str, str],
):
    """Unknown period_id returns 404."""
    import uuid
    resp = client.get(f"/api/v1/periods/{uuid.uuid4()}/tax-benefits", headers=auth_headers)
    assert resp.status_code == 404
