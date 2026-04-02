"""
Integration test fixtures.

These fixtures build on the root conftest (db, client, auth_headers, etc.)
and provide higher-level helpers for integration test workflows.
"""
import uuid

import pytest


@pytest.fixture
def create_period(client, auth_headers):
    """Factory fixture: creates a period and returns its JSON response.

    Usage:
        period = create_period()
        period = create_period(name="Custom", start="2027-02-01", end="2027-02-28")
    """
    def _create(name=None, start="2027-01-01", end="2027-01-31"):
        payload = {
            "period_name": name or f"Test Period {uuid.uuid4().hex[:8]}",
            "start_date": start,
            "end_date": end,
            "snapshot_date": end,
        }
        resp = client.post("/api/v1/periods/", json=payload, headers=auth_headers)
        assert resp.status_code == 201, f"Failed to create period: {resp.text}"
        return resp.json()
    return _create


@pytest.fixture
def create_income(client, auth_headers, test_currency):
    """Factory fixture: creates an income entry and returns its JSON response."""
    def _create(period_id, source="Test Income", amount=1000, currency_id=None):
        payload = {
            "source_name": source,
            "amount": amount,
            "currency_id": str(currency_id or test_currency.id),
        }
        resp = client.post(
            f"/api/v1/periods/{period_id}/incomes",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to create income: {resp.text}"
        return resp.json()
    return _create


@pytest.fixture
def create_expense(client, auth_headers, test_currency, test_category):
    """Factory fixture: creates an expense entry and returns its JSON response."""
    def _create(period_id, name="Test Expense", amount=500, currency_id=None, category_id=None):
        payload = {
            "item_name": name,
            "amount": amount,
            "currency_id": str(currency_id or test_currency.id),
            "category_id": str(category_id or test_category.id),
        }
        resp = client.post(
            f"/api/v1/periods/{period_id}/expenses",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to create expense: {resp.text}"
        return resp.json()
    return _create
