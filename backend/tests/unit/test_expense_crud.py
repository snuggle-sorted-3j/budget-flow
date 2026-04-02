"""
Unit Tests for Expense CRUD Operations

Tests cover:
- Creating expenses with various fields
- Listing expenses by period
- Getting expense by ID
- Deleting expenses
"""

import pytest
pytestmark = pytest.mark.unit

from decimal import Decimal
from datetime import date
from uuid import uuid4
from sqlalchemy.orm import Session

from app.crud.expense import (
    create_expense,
    list_expenses_for_period,
    get_expense,
    delete_expense
)
from app.crud.period import create_period
from app.schemas.period import PeriodCreate
from app.schemas.expense import ExpenseCreate
from app.models.user import User
from app.models.currency import Currency
from app.models.expense_category import ExpenseCategory


class TestCreateExpense:
    """Test expense creation."""
    
    def test_create_expense_success(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: Successfully create an expense entry."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Expense Test Period",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            snapshot_date=date(2026, 1, 31)
        ))
        
        expense_data = ExpenseCreate(
            item_name="Groceries",
            amount=Decimal("150.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        )
        
        expense = create_expense(db, period.id, expense_data)
        
        assert expense is not None
        assert expense.item_name == "Groceries"
        assert expense.amount == Decimal("150.00")
        assert expense.currency_id == test_currency.id
        assert expense.category_id == test_category.id
        assert expense.calculation_period_id == period.id
        assert expense.id is not None

    def test_create_expense_with_all_fields(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: Create expense with all optional fields."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Full Expense Test",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            snapshot_date=date(2026, 2, 28)
        ))
        
        expense_data = ExpenseCreate(
            item_name="Office Equipment",
            amount=Decimal("599.99"),
            currency_id=test_currency.id,
            category_id=test_category.id,
            expense_date=date(2026, 2, 15),
            is_tax_deductible=True,
            notes="New monitor for home office"
        )
        
        expense = create_expense(db, period.id, expense_data)
        
        assert expense.item_name == "Office Equipment"
        assert expense.amount == Decimal("599.99")
        assert expense.expense_date == date(2026, 2, 15)
        assert expense.is_tax_deductible is True
        assert expense.notes == "New monitor for home office"

    def test_create_expense_minimal_fields(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: Create expense with only required fields."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Minimal Expense Test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            snapshot_date=date(2026, 3, 31)
        ))
        
        expense_data = ExpenseCreate(
            item_name="Coffee",
            amount=Decimal("5.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        )
        
        expense = create_expense(db, period.id, expense_data)
        
        assert expense.item_name == "Coffee"
        assert expense.amount == Decimal("5.00")
        assert expense.is_tax_deductible is False  # Default


class TestListExpenses:
    """Test expense listing."""
    
    def test_list_expenses_for_period(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: List all expenses for a specific period."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="List Test Period",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
            snapshot_date=date(2026, 4, 30)
        ))
        
        # Create multiple expenses
        for i in range(3):
            create_expense(db, period.id, ExpenseCreate(
                item_name=f"Expense {i+1}",
                amount=Decimal(f"{(i+1) * 50}.00"),
                currency_id=test_currency.id,
                category_id=test_category.id
            ))
        
        expenses = list_expenses_for_period(db, period.id)
        
        assert len(expenses) == 3
        item_names = [exp.item_name for exp in expenses]
        assert "Expense 1" in item_names
        assert "Expense 2" in item_names
        assert "Expense 3" in item_names

    def test_list_expenses_empty_period(
        self, db: Session, test_user: User
    ):
        """Test: List expenses for period with no expenses."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Empty Period",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 31),
            snapshot_date=date(2026, 5, 31)
        ))
        
        expenses = list_expenses_for_period(db, period.id)
        
        assert expenses == []

    def test_list_expenses_filters_by_period(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: Expenses from other periods are not included."""
        period1 = create_period(db, test_user.id, PeriodCreate(
            period_name="Period 1",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
            snapshot_date=date(2026, 6, 30)
        ))
        
        period2 = create_period(db, test_user.id, PeriodCreate(
            period_name="Period 2",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            snapshot_date=date(2026, 7, 31)
        ))
        
        # Add expense to period 1
        create_expense(db, period1.id, ExpenseCreate(
            item_name="Period 1 Expense",
            amount=Decimal("100.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        # Add expense to period 2
        create_expense(db, period2.id, ExpenseCreate(
            item_name="Period 2 Expense",
            amount=Decimal("200.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        # List only period 1 expenses
        expenses = list_expenses_for_period(db, period1.id)
        
        assert len(expenses) == 1
        assert expenses[0].item_name == "Period 1 Expense"

    def test_list_expenses_includes_category(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: Listed expenses include category relationship."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Category Test Period",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            snapshot_date=date(2026, 8, 31)
        ))
        
        create_expense(db, period.id, ExpenseCreate(
            item_name="Test Expense",
            amount=Decimal("75.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        expenses = list_expenses_for_period(db, period.id)
        
        assert len(expenses) == 1
        assert expenses[0].category is not None
        assert expenses[0].category.id == test_category.id


class TestGetExpense:
    """Test getting expense by ID."""
    
    def test_get_expense_success(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: Successfully get expense by ID."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Get Test Period",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            snapshot_date=date(2026, 9, 30)
        ))
        
        created = create_expense(db, period.id, ExpenseCreate(
            item_name="Test Expense",
            amount=Decimal("250.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        fetched = get_expense(db, created.id)
        
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.item_name == "Test Expense"

    def test_get_expense_not_found(self, db: Session):
        """Test: Get non-existent expense returns None."""
        result = get_expense(db, uuid4())
        assert result is None


class TestDeleteExpense:
    """Test expense deletion."""
    
    def test_delete_expense_success(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: Successfully delete an expense."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Delete Test Period",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            snapshot_date=date(2026, 10, 31)
        ))
        
        expense = create_expense(db, period.id, ExpenseCreate(
            item_name="To Delete",
            amount=Decimal("50.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        result = delete_expense(db, expense.id)
        
        assert result is True
        assert get_expense(db, expense.id) is None

    def test_delete_expense_not_found(self, db: Session):
        """Test: Delete non-existent expense returns False."""
        result = delete_expense(db, uuid4())
        assert result is False

    def test_delete_expense_removes_from_list(
        self, db: Session, test_user: User, test_currency: Currency, test_category: ExpenseCategory
    ):
        """Test: Deleted expense no longer appears in period listing."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Delete List Test",
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 30),
            snapshot_date=date(2026, 11, 30)
        ))
        
        expense1 = create_expense(db, period.id, ExpenseCreate(
            item_name="Keep",
            amount=Decimal("100.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        expense2 = create_expense(db, period.id, ExpenseCreate(
            item_name="Delete",
            amount=Decimal("50.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        # Delete expense2
        delete_expense(db, expense2.id)
        
        expenses = list_expenses_for_period(db, period.id)
        
        assert len(expenses) == 1
        assert expenses[0].item_name == "Keep"
