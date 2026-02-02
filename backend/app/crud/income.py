from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.income_entry import IncomeEntry
from app.schemas.income import IncomeCreate, IncomeUpdate


def create_income(db: Session, period_id: UUID, data: IncomeCreate) -> IncomeEntry:
    """Create a new income entry."""
    db_income = IncomeEntry(
        calculation_period_id=period_id,
        **data.model_dump()
    )
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    return db_income


def list_incomes_for_period(db: Session, period_id: UUID) -> List[IncomeEntry]:
    """List all income entries for a period with joined relationships."""
    stmt = select(IncomeEntry).options(
        joinedload(IncomeEntry.currency)
    ).where(
        IncomeEntry.calculation_period_id == period_id
    ).order_by(IncomeEntry.income_date.desc())
    return list(db.execute(stmt).scalars().unique().all())


def get_income(db: Session, income_id: UUID) -> Optional[IncomeEntry]:
    """Get an income entry by ID."""
    stmt = select(IncomeEntry).where(IncomeEntry.id == income_id)
    return db.execute(stmt).scalar_one_or_none()


def delete_income(db: Session, income_id: UUID) -> bool:
    """Delete an income entry."""
    income = get_income(db, income_id)
    if not income:
        return False
    db.delete(income)
    db.commit()
    return True


def update_income(
    db: Session, db_obj: IncomeEntry, obj_in: IncomeCreate  # Should typically handle Update schema too but simpler for now
) -> IncomeEntry:
    """Update an income entry."""
    # We can use model_dump(exclude_unset=True) from Pydantic
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
