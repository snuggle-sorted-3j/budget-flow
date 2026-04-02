import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update

from app.models.template import Template
from app.models.expense_category import ExpenseCategory
from app.models.income_entry import IncomeEntry
from app.models.expense_item import ExpenseItem
from app.models.calculation_period import CalculationPeriod


def create_template_from_period(
    db: Session, 
    user_id: uuid.UUID, 
    template_name: str, 
    template_type: str, 
    source_period_id: uuid.UUID
) -> Template:
    """Create a template based on data from an existing period."""
    template_data = {}

    if template_type in ("EXPENSE_CATEGORIES", "FULL"):
        # Get all expense categories for the user
        categories = db.execute(
            select(ExpenseCategory).where(ExpenseCategory.user_id == user_id)
        ).scalars().all()
        
        template_data["categories"] = [
            {
                "category_name": c.category_name,
                "icon": c.icon,
                "parent_category_name": c.parent.category_name if c.parent else None,
                "is_system_category": c.is_system_category
            }
            for c in categories if c.is_active
        ]

    if template_type in ("INCOME_SOURCES", "FULL"):
        # Get distinct income source names from income_entries in the source period
        income_entries = db.execute(
            select(IncomeEntry).where(IncomeEntry.calculation_period_id == source_period_id)
        ).scalars().all()
        
        # If FULL, we might want to store recurring ones with amounts, 
        # otherwise just source names
        sources = []
        seen_names = set()
        for entry in income_entries:
            if entry.source_name not in seen_names:
                sources.append({
                    "source_name": entry.source_name,
                    "default_amount": float(entry.amount) if template_type == "FULL" and entry.is_recurring else 0.0,
                    "is_recurring": entry.is_recurring,
                    "currency_id": str(entry.currency_id)
                })
                seen_names.add(entry.source_name)
        
        template_data["income_sources"] = sources

    if template_type == "FULL":
        # Get recurring expense items from the source period
        recurring_expenses = db.execute(
            select(ExpenseItem).where(
                ExpenseItem.calculation_period_id == source_period_id,
                ExpenseItem.is_recurring == True
            )
        ).scalars().all()
        
        template_data["recurring_expenses"] = [
            {
                "item_name": e.item_name,
                "amount": float(e.amount),
                "category_name": e.category.category_name,
                "currency_id": str(e.currency_id),
                "is_tax_deductible": e.is_tax_deductible,
                "tax_category": e.tax_category,
                "expense_type": e.expense_type,
                "is_recurring": True
            }
            for e in recurring_expenses
        ]

    db_template = Template(
        user_id=user_id,
        template_name=template_name,
        template_type=template_type,
        template_data=template_data,
        is_default=False
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


def apply_template_to_period(
    db: Session, 
    user_id: uuid.UUID, 
    template_id: uuid.UUID, 
    target_period_id: uuid.UUID
) -> Dict[str, Any]:
    """Apply template data to a target period."""
    template = db.execute(
        select(Template).where(Template.id == template_id, Template.user_id == user_id)
    ).scalar_one_or_none()
    
    if not template:
        return {"error": "Template not found"}

    # Verify target period exists and belongs to the user
    target_period = db.execute(
        select(CalculationPeriod).where(
            CalculationPeriod.id == target_period_id,
            CalculationPeriod.user_id == user_id,
        )
    ).scalar_one_or_none()
    if not target_period:
        return {"error": "Target period not found"}

    data = template.template_data
    summary = {"categories": 0, "income_sources": 0, "expenses": 0}

    # 1. Handle Categories (Additive)
    if "categories" in data:
        # Create a mapping of category names to IDs for later use
        existing_cats = db.execute(
            select(ExpenseCategory).where(ExpenseCategory.user_id == user_id)
        ).scalars().all()
        cat_map = {c.category_name: c.id for c in existing_cats}
        
        # Sort so parents are created before children if we were using names
        # But for now, let's just ensure they exist
        for cat_info in data["categories"]:
            if cat_info["category_name"] not in cat_map:
                new_cat = ExpenseCategory(
                    user_id=user_id,
                    category_name=cat_info["category_name"],
                    icon=cat_info.get("icon"),
                    is_system_category=cat_info.get("is_system_category", False)
                )
                db.add(new_cat)
                db.flush()
                cat_map[new_cat.category_name] = new_cat.id
                summary["categories"] += 1
        
        # secondary pass for parents if needed? 
        # (Template stored parent_category_name)
        for cat_info in data["categories"]:
            if cat_info.get("parent_category_name"):
                cat = db.execute(select(ExpenseCategory).where(
                    ExpenseCategory.user_id == user_id, 
                    ExpenseCategory.category_name == cat_info["category_name"]
                )).scalar_one_or_none()
                parent_id = cat_map.get(cat_info["parent_category_name"])
                if cat and parent_id and cat.parent_category_id != parent_id:
                    cat.parent_category_id = parent_id
                    db.add(cat)

    # 2. Handle Income Sources
    if "income_sources" in data:
        for inc in data["income_sources"]:
            new_income = IncomeEntry(
                calculation_period_id=target_period_id,
                source_name=inc["source_name"],
                amount=inc.get("default_amount", 0.0),
                currency_id=uuid.UUID(inc["currency_id"]),
                is_recurring=inc.get("is_recurring", False)
            )
            db.add(new_income)
            summary["income_sources"] += 1

    # 3. Handle Recurring Expenses
    if "recurring_expenses" in data:
        # We need the cat_map again
        existing_cats = db.execute(
            select(ExpenseCategory).where(ExpenseCategory.user_id == user_id)
        ).scalars().all()
        cat_map = {c.category_name: c.id for c in existing_cats}

        for exp in data["recurring_expenses"]:
            cat_id = cat_map.get(exp["category_name"])
            if cat_id:
                new_exp = ExpenseItem(
                    calculation_period_id=target_period_id,
                    category_id=cat_id,
                    item_name=exp["item_name"],
                    amount=exp["amount"],
                    currency_id=uuid.UUID(exp["currency_id"]),
                    is_tax_deductible=exp.get("is_tax_deductible", False),
                    tax_category=exp.get("tax_category"),
                    expense_type=exp.get("expense_type", "REGULAR"),
                    is_recurring=True
                )
                db.add(new_exp)
                summary["expenses"] += 1

    db.commit()
    return summary


def list_templates(db: Session, user_id: uuid.UUID) -> List[Template]:
    """List all templates for a user."""
    return db.execute(
        select(Template)
        .where(Template.user_id == user_id)
        .order_by(Template.is_default.desc(), Template.created_at.desc())
    ).scalars().all()


def delete_template(db: Session, user_id: uuid.UUID, template_id: uuid.UUID) -> bool:
    """Delete a template."""
    result = db.execute(
        delete(Template).where(Template.id == template_id, Template.user_id == user_id)
    )
    db.commit()
    return result.rowcount > 0


def set_default_template(db: Session, user_id: uuid.UUID, template_id: uuid.UUID) -> bool:
    """Set a template as default and unset others."""
    # Unset all defaults for this user
    db.execute(
        update(Template)
        .where(Template.user_id == user_id)
        .values(is_default=False)
    )
    # Set the specific template as default
    result = db.execute(
        update(Template)
        .where(Template.id == template_id, Template.user_id == user_id)
        .values(is_default=True)
    )
    db.commit()
    return result.rowcount > 0


def update_template(
    db: Session, 
    user_id: uuid.UUID, 
    template_id: uuid.UUID, 
    template_name: Optional[str] = None,
    is_default: Optional[bool] = None
) -> Optional[Template]:
    """Update template metadata."""
    if is_default is True:
        set_default_template(db, user_id, template_id)
    
    stmt = update(Template).where(Template.id == template_id, Template.user_id == user_id)
    if template_name:
        stmt = stmt.values(template_name=template_name)
    
    db.execute(stmt)
    db.commit()
    
    return db.execute(
        select(Template).where(Template.id == template_id, Template.user_id == user_id)
    ).scalar_one_or_none()
