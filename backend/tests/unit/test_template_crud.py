"""
Unit Tests for Template CRUD Operations

Tests cover:
- Creating templates from existing periods
- Applying templates to new periods (copying data)
- Managing default templates
"""

import pytest
pytestmark = pytest.mark.unit

from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.crud.template import (
    create_template_from_period,
    apply_template_to_period,
    list_templates,
    delete_template,
    set_default_template
)
from app.crud.period import create_period
from app.crud.income import create_income, list_incomes_for_period
from app.crud.expense import create_expense, list_expenses_for_period
from app.schemas.period import PeriodCreate
from app.schemas.income import IncomeCreate
from app.schemas.expense import ExpenseCreate
from app.models.user import User
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory


class TestTemplateLifecycle:
    """Test full lifecycle of templates."""
    
    def test_create_and_apply_template(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: Create template from period and apply to new period."""
        # 1. Setup Source Period with Data
        source_period = create_period(db, test_user.id, PeriodCreate(
            period_name="Source Period", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), snapshot_date=date(2026, 1, 31)
        ))
        
        create_income(db, source_period.id, IncomeCreate(
            source_name="Recurring Salary",
            amount=Decimal("5000.00"),
            currency_id=test_currency.id,
            is_recurring=True
        ))
        
        create_expense(db, source_period.id, ExpenseCreate(
            item_name="Recurring Rent",
            amount=Decimal("1000.00"),
            currency_id=test_currency.id,
            category_id=test_category.id,
            is_recurring=True
        ))
        
        # 2. Create Template
        template = create_template_from_period(
            db, test_user.id, "Monthly Standard", "FULL", source_period.id
        )
        assert template.template_name == "Monthly Standard"
        
        # 3. Create Target Period
        target_period = create_period(db, test_user.id, PeriodCreate(
            period_name="Target Period", start_date=date(2026, 2, 1), end_date=date(2026, 2, 28), snapshot_date=date(2026, 2, 28)
        ))
        
        # 4. Apply Template
        apply_template_to_period(db, test_user.id, template.id, target_period.id)
        
        # 5. Verify Data Copied
        incomes = list_incomes_for_period(db, target_period.id)
        expenses = list_expenses_for_period(db, target_period.id)
        
        assert len(incomes) == 1
        assert incomes[0].source_name == "Recurring Salary"
        assert incomes[0].amount == Decimal("5000.00")
        # should have new date or None? Usually logic sets date to None or adjusts. Check logic if fails.
        # implementation details vary, usually dates are reset or cleared.
        
        assert len(expenses) == 1
        assert expenses[0].item_name == "Recurring Rent"

    def test_manage_default_template(self, db: Session, test_user: User):
        """Test: Setting default template."""
        # Create empty template (source period requires at least created)
        p1 = create_period(db, test_user.id, PeriodCreate(
            period_name="P1", start_date=d(2026,1,1), end_date=d(2026,1,31), snapshot_date=d(2026,1,31)
        ))
        
        t1 = create_template_from_period(db, test_user.id, "T1", "FULL", p1.id)
        t2 = create_template_from_period(db, test_user.id, "T2", "FULL", p1.id)
        
        set_default_template(db, test_user.id, t1.id)
        db.refresh(t1)
        db.refresh(t2)
        assert t1.is_default is True
        assert t2.is_default is False
        
        set_default_template(db, test_user.id, t2.id)
        db.refresh(t1)
        db.refresh(t2)
        assert t1.is_default is False
        assert t2.is_default is True

def d(y, m, d):
    from datetime import date
    return date(y, m, d)
