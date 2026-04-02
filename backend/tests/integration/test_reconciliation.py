import pytest

pytestmark = pytest.mark.integration

import uuid
from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory

def test_reconciliation_zero_start(
    client: TestClient, 
    auth_headers: Dict[str, str], 
    test_currency: Currency,
    test_category: ExpenseCategory
):
    # 1. Create Period
    period_payload = {
        "period_name": "First Period",
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "snapshot_date": "2026-01-31"
    }
    p_resp = client.post("/api/v1/periods/", json=period_payload, headers=auth_headers)
    period_id = p_resp.json()["id"]

    # 2. Create Account
    acc_resp = client.post("/api/v1/accounts/", json={
        "account_name": "Wallet", "account_type": "CASH", "currency_id": str(test_currency.id)
    }, headers=auth_headers)
    account_id = acc_resp.json()["id"]

    # 3. Add Income: +1000
    client.post(f"/api/v1/periods/{period_id}/incomes", json={
        "source_name": "Gift", "amount": 1000, "currency_id": str(test_currency.id), "income_date": "2026-01-05"
    }, headers=auth_headers)

    # 4. Add Expense: -200
    client.post(f"/api/v1/periods/{period_id}/expenses", json={
        "item_name": "Dinner", "amount": 200, "currency_id": str(test_currency.id), 
        "category_id": str(test_category.id), "expense_date": "2026-01-10"
    }, headers=auth_headers)

    # Expected: 0 + 1000 - 200 = 800
    
    # 5. Case: Unbalanced (No snapshot yet)
    rec_resp = client.get(f"/api/v1/periods/{period_id}/reconciliation", headers=auth_headers)
    data = rec_resp.json()
    assert data["overall_balanced"] is False
    summary = next(s for s in data["reconciliations"] if s["currency_ticker"] == test_currency.ticker)
    assert float(summary["expected_balance"]) == 800.0
    assert float(summary["actual_balance"]) == 0.0

    # 6. Add Snapshot: 800
    client.post(f"/api/v1/periods/{period_id}/snapshots", json=[
        {"account_id": account_id, "balance": 800}
    ], headers=auth_headers)

    # 7. Case: Balanced
    rec_resp = client.get(f"/api/v1/periods/{period_id}/reconciliation", headers=auth_headers)
    assert rec_resp.json()["overall_balanced"] is True

    # 8. Finalize
    fin_resp = client.patch(f"/api/v1/periods/{period_id}/finalize", headers=auth_headers)
    assert fin_resp.status_code == 200
    assert fin_resp.json()["status"] == "FINALIZED"

def test_reconciliation_with_previous_period(
    client: TestClient, 
    auth_headers: Dict[str, str], 
    test_currency: Currency
):
    # 1. Create Period 1 (Jan)
    p1 = client.post("/api/v1/periods/", json={
        "period_name": "Jan", "start_date": "2026-01-01", "end_date": "2026-01-31", "snapshot_date": "2026-01-31"
    }, headers=auth_headers).json()
    
    # 2. Add Account & Snapshot in Jan
    acc_resp = client.post("/api/v1/accounts/", json={
        "account_name": "Bank", "account_type": "BANK", "currency_id": str(test_currency.id)
    }, headers=auth_headers)
    account_id = acc_resp.json()["id"]
    
    client.post(f"/api/v1/periods/{p1['id']}/snapshots", json=[
        {"account_id": account_id, "balance": 5000}
    ], headers=auth_headers)

    # 3. Create Period 2 (Feb)
    p2 = client.post("/api/v1/periods/", json={
        "period_name": "Feb", "start_date": "2026-02-01", "end_date": "2026-02-28", "snapshot_date": "2026-02-28"
    }, headers=auth_headers).json()

    # 4. Check reconciliation for Feb
    # Expected Starting Balance = 5000
    rec_resp = client.get(f"/api/v1/periods/{p2['id']}/reconciliation", headers=auth_headers)
    summary = next(s for s in rec_resp.json()["reconciliations"] if s["currency_ticker"] == test_currency.ticker)
    assert float(summary["starting_balance"]) == 5000.0

def test_finalize_fails_if_unbalanced(
    client: TestClient, 
    auth_headers: Dict[str, str], 
    test_currency: Currency
):
    p = client.post("/api/v1/periods/", json={
        "period_name": "Fail Test", "start_date": "2026-03-01", "end_date": "2026-03-31", "snapshot_date": "2026-03-31"
    }, headers=auth_headers).json()
    
    # Try to finalize empty period (No snapshots, no income, no expense)
    # Usually it's balanced (0=0), but if we have an account with no snapshot it might be fine.
    # Actually if there are 0 income, 0 expense, 0 start, 0 end -> balanced.
    
    # Let's make it unbalanced
    client.post(f"/api/v1/periods/{p['id']}/incomes", json={
        "source_name": "Work", "amount": 100, "currency_id": str(test_currency.id), "income_date": "2026-03-05"
    }, headers=auth_headers)
    
    # Expected 100, actual 0 -> Unbalanced
    fin_resp = client.patch(f"/api/v1/periods/{p['id']}/finalize", headers=auth_headers)
    assert fin_resp.status_code == 400
    assert "not balanced" in fin_resp.json()["detail"]["message"]
