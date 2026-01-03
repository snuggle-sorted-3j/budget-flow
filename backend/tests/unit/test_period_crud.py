from datetime import date
from sqlalchemy.orm import Session
from app.crud.period import create_period, get_period, list_periods, update_period_status
from app.schemas.period import PeriodCreate
from app.models.user import User
import pytest

def test_create_period(db: Session, test_user: User):
    period_in = PeriodCreate(
        period_name="Test Period",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        snapshot_date=date(2026, 1, 31)
    )
    period = create_period(db, test_user.id, period_in)
    assert period.period_name == "Test Period"
    assert period.user_id == test_user.id
    assert period.status == "DRAFT"

def test_get_period(db: Session, test_user: User):
    period_in = PeriodCreate(
        period_name="Get Test",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 28),
        snapshot_date=date(2026, 2, 28)
    )
    created = create_period(db, test_user.id, period_in)
    
    fetched = get_period(db, test_user.id, created.id)
    assert fetched is not None
    assert fetched.id == created.id

def test_list_periods(db: Session, test_user: User):
    create_period(db, test_user.id, PeriodCreate(
        period_name="P1", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), snapshot_date=date(2026, 1, 31)
    ))
    create_period(db, test_user.id, PeriodCreate(
        period_name="P2", start_date=date(2026, 2, 1), end_date=date(2026, 2, 28), snapshot_date=date(2026, 2, 28)
    ))
    
    periods = list_periods(db, test_user.id)
    assert len(periods) >= 2

def test_update_period_status(db: Session, test_user: User):
    period_in = PeriodCreate(
        period_name="Status Test",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
        snapshot_date=date(2026, 3, 31)
    )
    period = create_period(db, test_user.id, period_in)
    
    updated = update_period_status(db, test_user.id, period.id, "FINALIZED")
    assert updated.status == "FINALIZED"
    assert updated.finalized_at is not None
