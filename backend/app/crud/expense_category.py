from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.expense_category import ExpenseCategory
from app.schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryUpdate


def get_category(db: Session, user_id: UUID, category_id: UUID) -> Optional[ExpenseCategory]:
    """Get an expense category by ID and user ID."""
    stmt = select(ExpenseCategory).where(
        ExpenseCategory.id == category_id,
        ExpenseCategory.user_id == user_id
    )
    return db.execute(stmt).scalar_one_or_none()


def list_categories(db: Session, user_id: UUID) -> List[ExpenseCategory]:
    """List all expense categories for a user."""
    stmt = select(ExpenseCategory).where(
        ExpenseCategory.user_id == user_id
    ).order_by(ExpenseCategory.sort_order, ExpenseCategory.category_name)
    return list(db.execute(stmt).scalars().all())


def create_category(db: Session, user_id: UUID, data: ExpenseCategoryCreate) -> ExpenseCategory:
    """Create a new expense category."""
    db_category = ExpenseCategory(
        user_id=user_id,
        category_name=data.category_name,
        parent_category_id=data.parent_category_id,
        icon=data.icon,
        sort_order=data.sort_order,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
