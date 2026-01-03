from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.balance_snapshot import BalanceSnapshot
from app.models.calculation_period import CalculationPeriod


def upsert_snapshot(
    db: Session, period_id: UUID, account_id: UUID, balance: Decimal
) -> BalanceSnapshot:
    """Upsert a balance snapshot for an account in a period."""
    # First, need to get the period to get the snapshot_date
    period = db.execute(
        select(CalculationPeriod).where(CalculationPeriod.id == period_id)
    ).scalar_one()

    stmt = select(BalanceSnapshot).where(
        BalanceSnapshot.calculation_period_id == period_id,
        BalanceSnapshot.account_id == account_id
    )
    snapshot = db.execute(stmt).scalar_one_or_none()

    if snapshot:
        snapshot.balance = balance
        # Ensure snapshot date is synced with period if it somehow changed (though unlikely for period updates)
        snapshot.snapshot_date = period.snapshot_date 
    else:
        snapshot = BalanceSnapshot(
            calculation_period_id=period_id,
            account_id=account_id,
            balance=balance,
            snapshot_date=period.snapshot_date,
        )
        db.add(snapshot)
    
    db.commit()
    db.refresh(snapshot)
    return snapshot


def list_snapshots_for_period(db: Session, period_id: UUID) -> List[BalanceSnapshot]:
    """List all balance snapshots for a period."""
    stmt = select(BalanceSnapshot).where(
        BalanceSnapshot.calculation_period_id == period_id
    )
    return list(db.execute(stmt).scalars().all())
