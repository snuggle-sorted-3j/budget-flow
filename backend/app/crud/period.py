from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.calculation_period import CalculationPeriod
from app.schemas.period import PeriodCreate


def create_period(db: Session, user_id: UUID, data: PeriodCreate) -> CalculationPeriod:
    """Create a new calculation period."""
    db_period = CalculationPeriod(
        user_id=user_id,
        period_name=data.period_name,
        start_date=data.start_date,
        end_date=data.end_date,
        snapshot_date=data.snapshot_date,
    )
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return db_period


def delete_period(db: Session, user_id: UUID, period_id: UUID) -> Optional[CalculationPeriod]:
    """Delete a calculation period."""
    period = get_period(db, user_id, period_id)
    if period:
        db.delete(period)
        db.commit()
    return period


def get_period(db: Session, user_id: UUID, period_id: UUID) -> Optional[CalculationPeriod]:
    """Get a period by ID and user ID."""
    stmt = select(CalculationPeriod).where(
        CalculationPeriod.id == period_id,
        CalculationPeriod.user_id == user_id
    )
    return db.execute(stmt).scalar_one_or_none()


def list_periods(db: Session, user_id: UUID) -> List[CalculationPeriod]:
    """List all periods for a user."""
    stmt = select(CalculationPeriod).where(
        CalculationPeriod.user_id == user_id
    ).order_by(CalculationPeriod.start_date.desc())
    return list(db.execute(stmt).scalars().all())


def update_period_status(db: Session, user_id: UUID, period_id: UUID, status: str) -> Optional[CalculationPeriod]:
    """Update period status."""
    period = get_period(db, user_id, period_id)
    if not period:
        return None

    period.status = status
    if status == "FINALIZED":
        period.finalized_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(period)
    return period
