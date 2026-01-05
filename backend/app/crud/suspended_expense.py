from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.suspended_expense import SuspendedExpense
from app.schemas.suspended_expense import SuspendedExpenseCreate, SuspendedExpenseUpdate

def create_suspended_expense(
    db: Session, user_id: UUID,  period_id: UUID, obj_in: SuspendedExpenseCreate
) -> SuspendedExpense:
    db_obj = SuspendedExpense(
        user_id=user_id,
        item_name=obj_in.item_name,
        amount=obj_in.amount,
        currency_id=obj_in.currency_id,
        transaction_type=obj_in.transaction_type,
        created_period_id=period_id,
        notes=obj_in.notes,
        status="PENDING",
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_suspended_expenses(db: Session, user_id: UUID) -> List[SuspendedExpense]:
    return db.scalars(
        select(SuspendedExpense).where(SuspendedExpense.user_id == user_id)
    ).all()

def get_suspended_expense(db: Session, expense_id: UUID) -> Optional[SuspendedExpense]:
    return db.get(SuspendedExpense, expense_id)

def update_suspended_expense(
    db: Session, db_obj: SuspendedExpense, obj_in: SuspendedExpenseUpdate
) -> SuspendedExpense:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_suspended_expense(db: Session, db_obj: SuspendedExpense) -> SuspendedExpense:
    db.delete(db_obj)
    db.commit()
    return db_obj
