from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from app.crud.account import create_account, list_accounts, deactivate_account
from app.crud.balance_snapshot import upsert_snapshot, list_snapshots_for_period
from app.crud.period import create_period
from app.schemas.account import AccountCreate
from app.schemas.period import PeriodCreate
from app.models.user import User
from app.models.currency import Currency
import pytest

pytestmark = pytest.mark.unit


def test_create_account(db: Session, test_user: User, test_currency: Currency):
    account_in = AccountCreate(
        account_name="Savings",
        account_type="BANK",
        currency_id=test_currency.id
    )
    account = create_account(db, test_user.id, account_in)
    assert account.account_name == "Savings"
    assert account.is_active is True

def test_upsert_snapshot(db: Session, test_user: User, test_currency: Currency):
    # Setup period and account
    period_in = PeriodCreate(
        period_name="Jan 2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        snapshot_date=date(2026, 1, 31)
    )
    period = create_period(db, test_user.id, period_in)
    
    account_in = AccountCreate(
        account_name="Wallet",
        account_type="CASH",
        currency_id=test_currency.id
    )
    account = create_account(db, test_user.id, account_in)
    
    # Test Create (Insert)
    balance = Decimal("100.50")
    snapshot = upsert_snapshot(db, period.id, account.id, balance)
    assert snapshot.balance == balance
    assert snapshot.snapshot_date == period.snapshot_date
    
    # Test Update
    new_balance = Decimal("150.75")
    updated_snapshot = upsert_snapshot(db, period.id, account.id, new_balance)
    assert updated_snapshot.id == snapshot.id
    assert updated_snapshot.balance == new_balance

def test_list_snapshots_for_period(db: Session, test_user: User, test_currency: Currency):
    period = create_period(db, test_user.id, PeriodCreate(
        period_name="Snap List", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), snapshot_date=date(2026, 1, 31)
    ))
    acc = create_account(db, test_user.id, AccountCreate(
        account_name="Acc", account_type="CASH", currency_id=test_currency.id
    ))
    
    upsert_snapshot(db, period.id, acc.id, Decimal("50.00"))
    
    snapshots = list_snapshots_for_period(db, period.id)
    assert len(snapshots) == 1
    assert snapshots[0].account_id == acc.id

def test_snapshot_update_replaces_existing(db: Session, test_user: User, test_currency: Currency):
    """Test: Upserting snapshot twice updates the existing record instead of creating new one."""
    period = create_period(db, test_user.id, PeriodCreate(
        period_name="Update Test", start_date=date(2026, 2, 1), end_date=date(2026, 2, 28), snapshot_date=date(2026, 2, 28)
    ))
    acc = create_account(db, test_user.id, AccountCreate(
        account_name="Acc", account_type="CASH", currency_id=test_currency.id
    ))
    
    # First insert
    s1 = upsert_snapshot(db, period.id, acc.id, Decimal("100.00"))
    
    # Second insert (update)
    s2 = upsert_snapshot(db, period.id, acc.id, Decimal("200.00"))
    
    assert s1.id == s2.id
    assert s2.balance == Decimal("200.00")
    
    # Verify count
    snapshots = list_snapshots_for_period(db, period.id)
    assert len(snapshots) == 1

def test_snapshot_with_zero_balance(db: Session, test_user: User, test_currency: Currency):
    """Test: Snapshot allows zero balance."""
    period = create_period(db, test_user.id, PeriodCreate(
        period_name="Zero Test", start_date=date(2026, 3, 1), end_date=date(2026, 3, 31), snapshot_date=date(2026, 3, 31)
    ))
    acc = create_account(db, test_user.id, AccountCreate(
        account_name="Zero Acc", account_type="CASH", currency_id=test_currency.id
    ))
    
    s = upsert_snapshot(db, period.id, acc.id, Decimal("0.00"))
    assert s.balance == Decimal("0.00")

def test_snapshot_for_inactive_account(db: Session, test_user: User, test_currency: Currency):
    """Test: Can create snapshot even for inactive account (historical record preservation)."""
    period = create_period(db, test_user.id, PeriodCreate(
        period_name="Inactive Test", start_date=date(2026, 4, 1), end_date=date(2026, 4, 30), snapshot_date=date(2026, 4, 30)
    ))
    acc = create_account(db, test_user.id, AccountCreate(
        account_name="Inactive Acc", account_type="CASH", currency_id=test_currency.id
    ))
    
    # Deactivate account (using direct update provided in crud or model manipulation)
    acc.is_active = False
    db.commit()
    
    # Should still succeed
    s = upsert_snapshot(db, period.id, acc.id, Decimal("500.00"))
    assert s.balance == Decimal("500.00")

