import pytest

pytestmark = pytest.mark.integration

from uuid import uuid4
from datetime import date
from io import BytesIO
import pandas as pd

from app.models.calculation_period import CalculationPeriod
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory
from app.models.expense_item import ExpenseItem
from app.models.income_entry import IncomeEntry

def test_export_period_csv_extension_and_content(client, db, test_user, auth_headers):
    # Setup data
    curr = Currency(id=uuid4(), user_id=test_user.id, ticker="USD", name="Dollar", is_default=True)
    cat = ExpenseCategory(id=uuid4(), user_id=test_user.id, category_name="Food", is_active=True)
    db.add_all([curr, cat])
    db.commit()
    
    p = CalculationPeriod(
        id=uuid4(), user_id=test_user.id, period_name="Jan 2024",
        start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        snapshot_date=date(2024, 1, 31), status="DRAFT" # Testing DRAFT period
    )
    db.add(p)
    db.commit()
    
    e = ExpenseItem(
        id=uuid4(), category_id=cat.id, calculation_period_id=p.id,
        item_name="Groceries", amount=100.0, currency_id=curr.id,
        expense_date=date(2024, 1, 5)
    )
    db.add(e)
    db.commit()

    # Request CSV
    response = client.get(f"/api/v1/export/period/{p.id}/csv", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in response.headers
    assert ".csv" in response.headers["Content-Disposition"]
    
    # Verify content
    df = pd.read_csv(BytesIO(response.content))
    assert len(df) == 1
    assert df.iloc[0]["Item/Source"] == "Groceries"

def test_export_reconciliation_pdf_extension(client, db, test_user, auth_headers):
    # Setup period
    p = CalculationPeriod(
        id=uuid4(), user_id=test_user.id, period_name="Feb 2024",
        start_date=date(2024, 2, 1), end_date=date(2024, 2, 28),
        snapshot_date=date(2024, 2, 28), status="DRAFT" # Testing DRAFT period
    )
    db.add(p)
    db.commit()

    # Request PDF
    response = client.get(f"/api/v1/export/period/{p.id}/reconciliation-report", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "Content-Disposition" in response.headers
    assert ".pdf" in response.headers["Content-Disposition"]
    assert response.content.startswith(b"%PDF")

def test_export_backup_json_extension(client, db, test_user, auth_headers):
    # Request JSON backup
    response = client.get("/api/v1/export/full-backup", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "Content-Disposition" in response.headers
    assert ".json" in response.headers["Content-Disposition"]
    
    data = response.json()
    assert "version" in data
    assert "periods" in data


def test_round_trip_via_api(client, db, test_user, auth_headers):
    """Export full backup via API, import into a new user, verify counts match."""
    import json
    import uuid as _uuid
    from app.models.user import User
    from app.core.security import create_access_token, get_password_hash

    # Setup some data for test_user
    curr = Currency(id=_uuid.uuid4(), user_id=test_user.id, ticker="USD", name="Dollar", is_default=True)
    cat = ExpenseCategory(id=_uuid.uuid4(), user_id=test_user.id, category_name="Food", is_active=True)
    db.add_all([curr, cat])
    db.commit()

    p = CalculationPeriod(
        id=_uuid.uuid4(), user_id=test_user.id, period_name="Mar 2024",
        start_date=date(2024, 3, 1), end_date=date(2024, 3, 31),
        snapshot_date=date(2024, 3, 31), status="DRAFT"
    )
    db.add(p)
    db.commit()

    e = ExpenseItem(
        id=_uuid.uuid4(), category_id=cat.id, calculation_period_id=p.id,
        item_name="Dinner", amount=50.0, currency_id=curr.id,
        expense_date=date(2024, 3, 15)
    )
    inc = IncomeEntry(
        id=_uuid.uuid4(), calculation_period_id=p.id, source_name="Freelance",
        amount=2000.0, currency_id=curr.id, income_date=date(2024, 3, 1)
    )
    db.add_all([e, inc])
    db.commit()

    # Step 1: Export
    export_resp = client.get("/api/v1/export/full-backup", headers=auth_headers)
    assert export_resp.status_code == 200
    backup_data = export_resp.json()

    # Step 2: Create user B and import
    user_b = User(
        id=_uuid.uuid4(), email=f"api-roundtrip-{_uuid.uuid4()}@test.com",
        password_hash=get_password_hash("pw123"), full_name="API User B", is_active=True
    )
    db.add(user_b)
    db.commit()

    token_b = create_access_token(data={"sub": str(user_b.id)})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    backup_bytes = json.dumps(backup_data).encode("utf-8")
    import_resp = client.post(
        "/api/v1/export/import/backup",
        headers=headers_b,
        files={"file": ("backup.json", backup_bytes, "application/json")},
    )
    assert import_resp.status_code == 200
    summary = import_resp.json()["summary"]
    assert summary["currencies_imported"] >= 1
    assert summary["categories_imported"] >= 1
    assert summary["periods_imported"] >= 1
    assert summary["income_imported"] >= 1
    assert summary["expenses_imported"] >= 1

    # Step 3: Export user B and compare
    export_b_resp = client.get("/api/v1/export/full-backup", headers=headers_b)
    assert export_b_resp.status_code == 200
    backup_b = export_b_resp.json()
    assert len(backup_b["currencies"]) == len(backup_data["currencies"])
    assert len(backup_b["periods"]) == len(backup_data["periods"])
