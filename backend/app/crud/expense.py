from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.expense_item import ExpenseItem
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


def create_expense(db: Session, period_id: UUID, data: ExpenseCreate) -> ExpenseItem:
    """Create a new expense entry."""
    db_expense = ExpenseItem(
        calculation_period_id=period_id,
        **data.model_dump()
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def list_expenses_for_period(db: Session, period_id: UUID) -> List[ExpenseItem]:
    """List all expense entries for a period with joined relationships."""
    stmt = select(ExpenseItem).options(
        joinedload(ExpenseItem.category),
        joinedload(ExpenseItem.currency)
    ).where(
        ExpenseItem.calculation_period_id == period_id
    ).order_by(ExpenseItem.expense_date.desc())
    return list(db.execute(stmt).scalars().unique().all())


def get_expense(db: Session, expense_id: UUID) -> Optional[ExpenseItem]:
    """Get an expense entry by ID."""
    stmt = select(ExpenseItem).where(ExpenseItem.id == expense_id)
    return db.execute(stmt).scalar_one_or_none()


def delete_expense(db: Session, expense_id: UUID) -> bool:
    """Delete an expense entry."""
    expense = get_expense(db, expense_id)
    if not expense:
        return False
    db.delete(expense)
    db.commit()
    return True


def update_expense(
    db: Session, db_obj: ExpenseItem, obj_in: ExpenseCreate
) -> ExpenseItem:
    """Update an expense entry."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
