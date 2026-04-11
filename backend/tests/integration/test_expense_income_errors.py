"""
Integration tests covering error paths in expenses and incomes endpoints.
Targets uncovered lines: 404/400/403 error responses.
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_period(client, headers):
    resp = client.post("/api/v1/periods/", json={
        "period_name": f"ErrPeriod-{uuid.uuid4().hex[:6]}",
        "start_date": "2026-02-01",
        "end_date": "2026-02-28",
        "snapshot_date": "2026-02-28"
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_expense(client, headers, period_id, category_id, currency_id, name="TestExpense"):
    resp = client.post(f"/api/v1/periods/{period_id}/expenses", json={
        "item_name": name,
        "amount": "100.00",
        "currency_id": str(currency_id),
        "category_id": str(category_id),
        "expense_date": "2026-02-10"
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_income(client, headers, period_id, currency_id, source="Salary"):
    resp = client.post(f"/api/v1/periods/{period_id}/incomes", json={
        "source_name": source,
        "amount": "500.00",
        "currency_id": str(currency_id),
        "income_date": "2026-02-15"
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Expense Error Paths
# ---------------------------------------------------------------------------

class TestExpenseErrorPaths:

    def test_create_expense_period_not_found(
        self, client: TestClient, auth_headers: Dict, test_currency, test_category
    ):
        """Create expense in non-existent period returns 404."""
        resp = client.post(f"/api/v1/periods/{uuid.uuid4()}/expenses", json={
            "item_name": "X",
            "amount": "10.00",
            "currency_id": str(test_currency.id),
            "category_id": str(test_category.id),
            "expense_date": "2026-02-10"
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_create_expense_invalid_currency(
        self, client: TestClient, auth_headers: Dict, test_category
    ):
        """Create expense with non-existent currency returns 400."""
        period = _create_period(client, auth_headers)
        resp = client.post(f"/api/v1/periods/{period['id']}/expenses", json={
            "item_name": "X",
            "amount": "10.00",
            "currency_id": str(uuid.uuid4()),
            "category_id": str(test_category.id),
            "expense_date": "2026-02-10"
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_list_expenses_period_not_found(
        self, client: TestClient, auth_headers: Dict
    ):
        """List expenses for non-existent period returns 404."""
        resp = client.get(
            f"/api/v1/periods/{uuid.uuid4()}/expenses",
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_update_expense_not_found(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """Update non-existent expense returns 404."""
        resp = client.patch(f"/api/v1/expenses/{uuid.uuid4()}", json={
            "amount": "999.00"
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_update_expense_wrong_user_returns_403(
        self, client: TestClient, auth_headers: Dict, test_currency, test_category, db
    ):
        """Update expense belonging to another user returns 403."""
        period = _create_period(client, auth_headers)
        expense = _create_expense(
            client, auth_headers, period["id"], test_category.id, test_currency.id
        )

        # Create another user
        from app.models.user import User
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"exp-other-{uuid.uuid4()}@test.com",
            password_hash=get_password_hash("pw"),
            full_name="Other",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.patch(f"/api/v1/expenses/{expense['id']}", json={
            "amount": "999.00"
        }, headers=other_headers)
        assert resp.status_code == 403

    def test_update_expense_finalized_period_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency, test_category, db
    ):
        """Update expense in finalized period returns 400."""
        period = _create_period(client, auth_headers)
        expense = _create_expense(
            client, auth_headers, period["id"], test_category.id, test_currency.id
        )

        from app.models.calculation_period import CalculationPeriod
        p = db.get(CalculationPeriod, period["id"])
        p.status = "FINALIZED"
        db.commit()

        resp = client.patch(f"/api/v1/expenses/{expense['id']}", json={
            "amount": "999.00"
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_update_expense_invalid_category_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency, test_category
    ):
        """Update expense with invalid category returns 400."""
        period = _create_period(client, auth_headers)
        expense = _create_expense(
            client, auth_headers, period["id"], test_category.id, test_currency.id
        )

        resp = client.patch(f"/api/v1/expenses/{expense['id']}", json={
            "category_id": str(uuid.uuid4())
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_update_expense_invalid_currency_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency, test_category
    ):
        """Update expense with invalid currency returns 400."""
        period = _create_period(client, auth_headers)
        expense = _create_expense(
            client, auth_headers, period["id"], test_category.id, test_currency.id
        )

        resp = client.patch(f"/api/v1/expenses/{expense['id']}", json={
            "currency_id": str(uuid.uuid4())
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_delete_expense_not_found(self, client: TestClient, auth_headers: Dict):
        """Delete non-existent expense returns 404."""
        resp = client.delete(f"/api/v1/expenses/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_expense_wrong_user_returns_403(
        self, client: TestClient, auth_headers: Dict, test_currency, test_category, db
    ):
        """Delete expense belonging to another user returns 403."""
        period = _create_period(client, auth_headers)
        expense = _create_expense(
            client, auth_headers, period["id"], test_category.id, test_currency.id
        )

        from app.models.user import User
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"del-other-{uuid.uuid4()}@test.com",
            password_hash=get_password_hash("pw"),
            full_name="Other",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.delete(f"/api/v1/expenses/{expense['id']}", headers=other_headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Income Error Paths
# ---------------------------------------------------------------------------

class TestIncomeErrorPaths:

    def test_create_income_period_not_found(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """Create income in non-existent period returns 404."""
        resp = client.post(f"/api/v1/periods/{uuid.uuid4()}/incomes", json={
            "source_name": "X",
            "amount": "100.00",
            "currency_id": str(test_currency.id),
            "income_date": "2026-02-10"
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_create_income_finalized_period_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency, db
    ):
        """Create income in finalized period returns 400."""
        period = _create_period(client, auth_headers)

        from app.models.calculation_period import CalculationPeriod
        p = db.get(CalculationPeriod, period["id"])
        p.status = "FINALIZED"
        db.commit()

        resp = client.post(f"/api/v1/periods/{period['id']}/incomes", json={
            "source_name": "X",
            "amount": "100.00",
            "currency_id": str(test_currency.id),
            "income_date": "2026-02-10"
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_list_incomes_period_not_found(
        self, client: TestClient, auth_headers: Dict
    ):
        """List incomes for non-existent period returns 404."""
        resp = client.get(
            f"/api/v1/periods/{uuid.uuid4()}/incomes",
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_update_income_not_found(self, client: TestClient, auth_headers: Dict):
        """Update non-existent income returns 404."""
        resp = client.patch(f"/api/v1/incomes/{uuid.uuid4()}", json={
            "amount": "999.00"
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_update_income_wrong_user_returns_403(
        self, client: TestClient, auth_headers: Dict, test_currency, db
    ):
        """Update income belonging to another user returns 403."""
        period = _create_period(client, auth_headers)
        income = _create_income(client, auth_headers, period["id"], test_currency.id)

        from app.models.user import User
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"inc-other-{uuid.uuid4()}@test.com",
            password_hash=get_password_hash("pw"),
            full_name="Other",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.patch(f"/api/v1/incomes/{income['id']}", json={
            "amount": "999.00"
        }, headers=other_headers)
        assert resp.status_code == 403

    def test_update_income_finalized_period_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency, db
    ):
        """Update income in finalized period returns 400."""
        period = _create_period(client, auth_headers)
        income = _create_income(client, auth_headers, period["id"], test_currency.id)

        from app.models.calculation_period import CalculationPeriod
        p = db.get(CalculationPeriod, period["id"])
        p.status = "FINALIZED"
        db.commit()

        resp = client.patch(f"/api/v1/incomes/{income['id']}", json={
            "amount": "999.00"
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_update_income_invalid_currency_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency
    ):
        """Update income with invalid currency returns 400."""
        period = _create_period(client, auth_headers)
        income = _create_income(client, auth_headers, period["id"], test_currency.id)

        resp = client.patch(f"/api/v1/incomes/{income['id']}", json={
            "currency_id": str(uuid.uuid4())
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_delete_income_not_found(self, client: TestClient, auth_headers: Dict):
        """Delete non-existent income returns 404."""
        resp = client.delete(f"/api/v1/incomes/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_income_wrong_user_returns_403(
        self, client: TestClient, auth_headers: Dict, test_currency, db
    ):
        """Delete income belonging to another user returns 403."""
        period = _create_period(client, auth_headers)
        income = _create_income(client, auth_headers, period["id"], test_currency.id)

        from app.models.user import User
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"del-inc-{uuid.uuid4()}@test.com",
            password_hash=get_password_hash("pw"),
            full_name="Other",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.delete(f"/api/v1/incomes/{income['id']}", headers=other_headers)
        assert resp.status_code == 403

    def test_delete_income_finalized_period_returns_400(
        self, client: TestClient, auth_headers: Dict, test_currency, db
    ):
        """Delete income in finalized period returns 400."""
        period = _create_period(client, auth_headers)
        income = _create_income(client, auth_headers, period["id"], test_currency.id)

        from app.models.calculation_period import CalculationPeriod
        p = db.get(CalculationPeriod, period["id"])
        p.status = "FINALIZED"
        db.commit()

        resp = client.delete(f"/api/v1/incomes/{income['id']}", headers=auth_headers)
        assert resp.status_code == 400
