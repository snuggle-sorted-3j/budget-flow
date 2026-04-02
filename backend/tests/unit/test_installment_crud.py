"""
Unit Tests for Installment CRUD Operations

Tests cover:
- Creating installment items
- Adding payments and verifying balance updates
- Creating payments triggering PAID_OFF status
- Deleting payments recalculating balance
"""

import pytest
pytestmark = pytest.mark.unit

from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.crud.installment import (
    create_installment_item,
    create_installment_payment,
    get_installment_item,
    delete_installment_payment,
    get_installment_payments
)
from app.crud.period import create_period
from app.schemas.period import PeriodCreate
from app.schemas.installment import InstallmentItemCreate, InstallmentPaymentCreate
from app.models.user import User
from app.models.currency import Currency


class TestInstallmentLifecycle:
    """Test full lifecycle of an installment."""
    
    def test_create_installment_item(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Create installment item initializes correctly."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Inst Init", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), snapshot_date=date(2026, 1, 31)
        ))
        
        item_data = InstallmentItemCreate(
            item_name="Smart Watch",
            total_price=Decimal("300.00"),
            currency_id=test_currency.id,
            initial_period_id=period.id,
            monthly_payment_amount=Decimal("100.00"),
            months_to_pay=3
        )
        
        item = create_installment_item(db, test_user.id, item_data)
        
        assert item.remaining_balance == Decimal("300.00")
        assert item.status == "ACTIVE"
        assert item.monthly_payment_amount == Decimal("100.00")

    def test_payment_updates_balance(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Adding payment reduces remaining balance."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Inst Pay", start_date=date(2026, 2, 1), end_date=date(2026, 2, 28), snapshot_date=date(2026, 2, 28)
        ))
        
        item = create_installment_item(db, test_user.id, InstallmentItemCreate(
            item_name="Loan",
            total_price=Decimal("1000.00"),
            currency_id=test_currency.id,
            initial_period_id=period.id,
            monthly_payment_amount=Decimal("200.00"),
            months_to_pay=5
        ))
        
        payment = create_installment_payment(db, item.id, period.id, InstallmentPaymentCreate(
            payment_amount=Decimal("200.00"),
            payment_date=date(2026, 2, 15)
        ))
        
        # Reload item from DB to get updated fields
        db.refresh(item)
        
        assert item.remaining_balance == Decimal("800.00")
        assert item.status == "ACTIVE"

    def test_full_payment_sets_paid_off(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Fully paying off installment sets status to PAID_OFF."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Inst Finish", start_date=date(2026, 3, 1), end_date=date(2026, 3, 31), snapshot_date=date(2026, 3, 31)
        ))
        
        item = create_installment_item(db, test_user.id, InstallmentItemCreate(
            item_name="Small Loan",
            total_price=Decimal("100.00"),
            currency_id=test_currency.id,
            initial_period_id=period.id,
            monthly_payment_amount=Decimal("50.00"),
            months_to_pay=2
        ))
        
        # Pay 100
        create_installment_payment(db, item.id, period.id, InstallmentPaymentCreate(
            payment_amount=Decimal("100.00"),
            payment_date=date(2026, 3, 15)
        ))
        
        db.refresh(item)
        assert item.remaining_balance == Decimal("0.00")
        assert item.status == "PAID_OFF"

    def test_delete_payment_recalculates(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Deleting payment increases remaining balance and resets status."""
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Inst Delete", start_date=date(2026, 4, 1), end_date=date(2026, 4, 30), snapshot_date=date(2026, 4, 30)
        ))
        
        item = create_installment_item(db, test_user.id, InstallmentItemCreate(
            item_name="Revert Test",
            total_price=Decimal("200.00"),
            currency_id=test_currency.id,
            initial_period_id=period.id,
            monthly_payment_amount=Decimal("200.00"),
            months_to_pay=1
        ))
        
        # Pay off completely
        payment = create_installment_payment(db, item.id, period.id, InstallmentPaymentCreate(
            payment_amount=Decimal("200.00"),
            payment_date=date(2026, 4, 15)
        ))
        
        db.refresh(item)
        assert item.status == "PAID_OFF"
        
        # Delete payment
        delete_installment_payment(db, payment)
        
        db.refresh(item)
        assert item.remaining_balance == Decimal("200.00")
        assert item.status == "ACTIVE"
