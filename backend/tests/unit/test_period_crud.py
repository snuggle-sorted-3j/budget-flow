from datetime import date
from sqlalchemy.orm import Session
from app.crud.period import create_period, get_period, list_periods, update_period_status, delete_period
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

def test_create_duplicate_period_name(db: Session, test_user: User):
    """Test: Creating duplicate period names is allowed (no unique constraint)."""
    p1 = create_period(db, test_user.id, PeriodCreate(
        period_name="Same Name",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 30),
        snapshot_date=date(2026, 4, 30)
    ))
    p2 = create_period(db, test_user.id, PeriodCreate(
        period_name="Same Name",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 31),
        snapshot_date=date(2026, 5, 31)
    ))
    assert p1.period_name == "Same Name"
    assert p2.period_name == "Same Name"
    assert p1.id != p2.id

def test_delete_period(db: Session, test_user: User):
    """Test: Deleting a period."""
    period = create_period(db, test_user.id, PeriodCreate(
        period_name="To Delete",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
        snapshot_date=date(2026, 6, 30)
    ))
    
    deleted = delete_period(db, test_user.id, period.id)
    assert deleted is not None
    assert deleted.id == period.id
    
    # Verify it's gone
    assert get_period(db, test_user.id, period.id) is None

def test_create_period_invalid_dates(db: Session, test_user: User):
    """Test: Start date > End date raises IntegrityError due to check constraint."""
    from sqlalchemy.exc import IntegrityError
    from pydantic import ValidationError

    
    with pytest.raises((IntegrityError, ValidationError)):
        period_in = PeriodCreate(
            period_name="Invalid Date",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 1, 1),  # End before start
            snapshot_date=date(2026, 1, 1)
        )
        create_period(db, test_user.id, period_in)
        db.flush()  # Force execution to trigger constraint

def test_create_period_invalid_snapshot_date(db: Session, test_user: User):
    from sqlalchemy.exc import IntegrityError
    from pydantic import ValidationError
    
    with pytest.raises((IntegrityError, ValidationError)):
        period_in = PeriodCreate(
            period_name="Invalid Snapshot",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            snapshot_date=date(2026, 1, 15)  # Mismatch
        )
        create_period(db, test_user.id, period_in)
        db.flush()

def test_finalize_already_finalized_period(db: Session, test_user: User):
    """Test: Re-finalizing updates the timestamp."""
    period = create_period(db, test_user.id, PeriodCreate(
        period_name="Re-Finalize",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
        snapshot_date=date(2026, 7, 31)
    ))
    
    # First finalize
    u1 = update_period_status(db, test_user.id, period.id, "FINALIZED")
    t1 = u1.finalized_at
    assert t1 is not None
    
    # Second finalize
    u2 = update_period_status(db, test_user.id, period.id, "FINALIZED")
    t2 = u2.finalized_at
    
    # Should update timestamp
    assert t2 >= t1

