"""
Unit Tests for Income CRUD Operations

Tests cover:
- Creating incomes with various fields
- Listing incomes by period
- Getting income by ID
- Deleting incomes
"""

import pytest
pytestmark = pytest.mark.unit

from decimal import Decimal
from datetime import date
from uuid import uuid4
from sqlalchemy.orm import Session

from app.crud.income import (
    create_income,
    list_incomes_for_period,
    get_income,
    delete_income
)
from app.crud.period import create_period
from app.schemas.period import PeriodCreate
from app.schemas.income import IncomeCreate
from app.models.user import User
from app.models.currency import Currency


class TestCreateIncome:
    """Test income creation."""
    
    def test_create_income_success(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Successfully create an income entry."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Income Test Period",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            snapshot_date=date(2026, 1, 31)
        ))
        
        income_data = IncomeCreate(
            source_name="Salary",
            amount=Decimal("5000.00"),
            currency_id=test_currency.id
        )
        
        income = create_income(db, period.id, income_data)
        
        assert income is not None
        assert income.source_name == "Salary"
        assert income.amount == Decimal("5000.00")
        assert income.currency_id == test_currency.id
        assert income.calculation_period_id == period.id
        assert income.id is not None

    def test_create_income_with_all_fields(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Create income with all optional fields."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Full Income Test",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            snapshot_date=date(2026, 2, 28)
        ))
        
        income_data = IncomeCreate(
            source_name="Freelance Project",
            amount=Decimal("2500.50"),
            currency_id=test_currency.id,
            income_date=date(2026, 2, 15),
            tax_applicable=True,
            notes="Web development project for client ABC"
        )
        
        income = create_income(db, period.id, income_data)
        
        assert income.source_name == "Freelance Project"
        assert income.amount == Decimal("2500.50")
        assert income.income_date == date(2026, 2, 15)
        assert income.tax_applicable is True
        assert income.notes == "Web development project for client ABC"

    def test_create_income_minimal_fields(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Create income with only required fields."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Minimal Income Test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            snapshot_date=date(2026, 3, 31)
        ))
        
        income_data = IncomeCreate(
            source_name="Gift",
            amount=Decimal("100.00"),
            currency_id=test_currency.id
        )
        
        income = create_income(db, period.id, income_data)
        
        assert income.source_name == "Gift"
        assert income.amount == Decimal("100.00")
        assert income.tax_applicable is False  # Default


class TestListIncomes:
    """Test income listing."""
    
    def test_list_incomes_for_period(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: List all incomes for a specific period."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="List Test Period",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
            snapshot_date=date(2026, 4, 30)
        ))
        
        # Create multiple incomes
        for i in range(3):
            create_income(db, period.id, IncomeCreate(
                source_name=f"Income {i+1}",
                amount=Decimal(f"{(i+1) * 1000}.00"),
                currency_id=test_currency.id
            ))
        
        incomes = list_incomes_for_period(db, period.id)
        
        assert len(incomes) == 3
        source_names = [inc.source_name for inc in incomes]
        assert "Income 1" in source_names
        assert "Income 2" in source_names
        assert "Income 3" in source_names

    def test_list_incomes_empty_period(
        self, db: Session, test_user: User
    ):
        """Test: List incomes for period with no incomes."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Empty Period",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 31),
            snapshot_date=date(2026, 5, 31)
        ))
        
        incomes = list_incomes_for_period(db, period.id)
        
        assert incomes == []

    def test_list_incomes_filters_by_period(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Incomes from other periods are not included."""
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
        
        # Add income to period 1
        create_income(db, period1.id, IncomeCreate(
            source_name="Period 1 Income",
            amount=Decimal("1000.00"),
            currency_id=test_currency.id
        ))
        
        # Add income to period 2
        create_income(db, period2.id, IncomeCreate(
            source_name="Period 2 Income",
            amount=Decimal("2000.00"),
            currency_id=test_currency.id
        ))
        
        # List only period 1 incomes
        incomes = list_incomes_for_period(db, period1.id)
        
        assert len(incomes) == 1
        assert incomes[0].source_name == "Period 1 Income"


class TestGetIncome:
    """Test getting income by ID."""
    
    def test_get_income_success(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Successfully get income by ID."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Get Test Period",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            snapshot_date=date(2026, 8, 31)
        ))
        
        created = create_income(db, period.id, IncomeCreate(
            source_name="Test Income",
            amount=Decimal("1500.00"),
            currency_id=test_currency.id
        ))
        
        fetched = get_income(db, created.id)
        
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.source_name == "Test Income"

    def test_get_income_not_found(self, db: Session):
        """Test: Get non-existent income returns None."""
        result = get_income(db, uuid4())
        assert result is None


class TestDeleteIncome:
    """Test income deletion."""
    
    def test_delete_income_success(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Successfully delete an income."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Delete Test Period",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            snapshot_date=date(2026, 9, 30)
        ))
        
        income = create_income(db, period.id, IncomeCreate(
            source_name="To Delete",
            amount=Decimal("500.00"),
            currency_id=test_currency.id
        ))
        
        result = delete_income(db, income.id)
        
        assert result is True
        assert get_income(db, income.id) is None

    def test_delete_income_not_found(self, db: Session):
        """Test: Delete non-existent income returns False."""
        result = delete_income(db, uuid4())
        assert result is False

    def test_delete_income_removes_from_list(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Deleted income no longer appears in period listing."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Delete List Test",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            snapshot_date=date(2026, 10, 31)
        ))
        
        income1 = create_income(db, period.id, IncomeCreate(
            source_name="Keep",
            amount=Decimal("1000.00"),
            currency_id=test_currency.id
        ))
        
        income2 = create_income(db, period.id, IncomeCreate(
            source_name="Delete",
            amount=Decimal("500.00"),
            currency_id=test_currency.id
        ))
        
        # Delete income2
        delete_income(db, income2.id)
        
        incomes = list_incomes_for_period(db, period.id)
        
        assert len(incomes) == 1
        assert incomes[0].source_name == "Keep"
