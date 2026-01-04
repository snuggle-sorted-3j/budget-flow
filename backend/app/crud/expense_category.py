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


def list_categories(db: Session, user_id: UUID, include_inactive: bool = False) -> List[ExpenseCategory]:
    """List all expense categories for a user."""
    stmt = select(ExpenseCategory).where(
        ExpenseCategory.user_id == user_id
    )
    if not include_inactive:
        stmt = stmt.where(ExpenseCategory.is_active == True)
        
    stmt = stmt.order_by(ExpenseCategory.sort_order, ExpenseCategory.category_name)
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


def update_category(db: Session, user_id: UUID, category_id: UUID, data: ExpenseCategoryUpdate) -> Optional[ExpenseCategory]:
    """Update an expense category."""
    category = get_category(db, user_id, category_id)
    if not category:
        return None
        
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
        
    db.commit()
    db.refresh(category)
    return category


def deactivate_category(db: Session, user_id: UUID, category_id: UUID) -> Optional[ExpenseCategory]:
    """Soft delete an expense category."""
    category = get_category(db, user_id, category_id)
    if not category:
        return None
        
    category.is_active = False
    db.commit()
    db.refresh(category)
    return category


def create_system_categories(db: Session, user_id: UUID) -> List[ExpenseCategory]:
    """Create default system categories."""
    system_categories = [
        {"category_name": "Untracked Expenses", "is_system_category": True, "icon": "❓"},
        {"category_name": "Food & Dining", "is_system_category": False, "icon": "🍽️"},
        {"category_name": "Housing", "is_system_category": False, "icon": "🏠"},
        {"category_name": "Transportation", "is_system_category": False, "icon": "🚗"},
        {"category_name": "Entertainment", "is_system_category": False, "icon": "🎬"},
        {"category_name": "Healthcare", "is_system_category": False, "icon": "⚕️"},
        {"category_name": "Personal", "is_system_category": False, "icon": "👤"},
    ]
    
    created_categories = []
    for idx, cat_data in enumerate(system_categories):
        # Check if exists to avoid duplicates if re-run
        stmt = select(ExpenseCategory).where(
            ExpenseCategory.user_id == user_id,
            ExpenseCategory.category_name == cat_data["category_name"]
        )
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            new_cat = ExpenseCategory(
                user_id=user_id,
                category_name=cat_data["category_name"],
                is_system_category=cat_data["is_system_category"],
                icon=cat_data["icon"],
                sort_order=idx
            )
            db.add(new_cat)
            created_categories.append(new_cat)
            
    db.commit()
    for cat in created_categories:
        db.refresh(cat)
    return created_categories
