"""
Unit Tests for Suspended Expense CRUD Operations

Tests cover:
- Creating suspended expenses (loan given/received)
- Updating status (settled)
- Deleting suspended expenses
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.crud.suspended_expense import (
    create_suspended_expense,
    get_suspended_expenses,
    update_suspended_expense,
    delete_suspended_expense
)
from app.crud.period import create_period
from app.schemas.period import PeriodCreate
from app.schemas.suspended_expense import (
    SuspendedExpenseCreate,
    SuspendedExpenseUpdate
)
from app.models.user import User
from app.models.currency import Currency


class TestSuspendedExpenseLifecycle:
    """Test full lifecycle of suspended expenses."""
    
    def test_create_suspended_expense(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Create suspended expense (loan given)."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Susp Init", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), snapshot_date=date(2026, 1, 31)
        ))
        
        susp_data = SuspendedExpenseCreate(
            item_name="Loan to Bob",
            amount=Decimal("100.00"),
            currency_id=test_currency.id,
            transaction_type="LOAN_OUT",
            notes="To be paid back next month"
        )
        
        susp = create_suspended_expense(db, test_user.id, period.id, susp_data)
        
        assert susp.status == "PENDING"
        assert susp.amount == Decimal("100.00")
        assert susp.created_period_id == period.id

    def test_update_status_to_settled(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Update suspended expense to settled."""
        # Setup
        p1 = create_period(db, test_user.id, PeriodCreate(
            period_name="P1", start_date=date(2026, 2, 1), end_date=date(2026, 2, 28), snapshot_date=date(2026, 2, 28)
        ))
        p2 = create_period(db, test_user.id, PeriodCreate(
            period_name="P2", start_date=date(2026, 3, 1), end_date=date(2026, 3, 31), snapshot_date=date(2026, 3, 31)
        ))
        
        susp = create_suspended_expense(db, test_user.id, p1.id, SuspendedExpenseCreate(
            item_name="Loan",
            amount=Decimal("50.00"),
            currency_id=test_currency.id,
            transaction_type="LOAN_OUT"
        ))
        
        # Settle in P2
        update_data = SuspendedExpenseUpdate(
            status="SETTLED",
            settled_period_id=p2.id
        )
        
        updated = update_suspended_expense(db, susp, update_data)
        
        assert updated.status == "SETTLED"
        assert updated.settled_period_id == p2.id

    def test_delete_suspended_expense(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Delete suspended expense."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Del Test", start_date=date(2026, 4, 1), end_date=date(2026, 4, 30), snapshot_date=date(2026, 4, 30)
        ))
        
        susp = create_suspended_expense(db, test_user.id, period.id, SuspendedExpenseCreate(
            item_name="Mistake",
            amount=Decimal("10.00"),
            currency_id=test_currency.id,
            transaction_type="OTHER"
        ))
        
        delete_suspended_expense(db, susp)
        
        # Verify gone
        all_susp = get_suspended_expenses(db, test_user.id)
        assert len(all_susp) == 0
