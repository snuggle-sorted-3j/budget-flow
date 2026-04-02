from fastapi.testclient import TestClient
import pytest

pytestmark = pytest.mark.integration

from app.models.user import User
from app.models.currency import Currency
from decimal import Decimal
import uuid

def test_spending_by_category_empty(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/analytics/spending-by-category", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "by_category" in data
    assert "total_expenses" in data
    assert data["total_expenses"] == 0

def test_income_vs_expenses_trend_empty(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/analytics/income-vs-expenses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "periods" in data
    assert data["totals"]["total_income"] == 0

def test_top_expenses_empty(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/analytics/top-expenses", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0

def test_net_worth_trend_empty(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/analytics/net-worth-trend", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "periods" in data
    assert data["net_change"] == 0

def test_category_trends_not_found(client: TestClient, auth_headers: dict):
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/analytics/category-trends/{random_id}", headers=auth_headers)
    assert response.status_code == 404

def test_compare_periods_not_found(client: TestClient, auth_headers: dict):
    id1 = str(uuid.uuid4())
    id2 = str(uuid.uuid4())
    response = client.get(f"/api/v1/analytics/compare-periods?period_id_1={id1}&period_id_2={id2}", headers=auth_headers)
    assert response.status_code == 404
