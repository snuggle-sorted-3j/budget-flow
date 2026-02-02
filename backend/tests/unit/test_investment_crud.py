"""
Unit Tests for Investment CRUD Operations

Tests cover:
- Investment account creation
- Investment (category) creation
- Investment transfer creation
- Listing transfers by period
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.crud.investment import (
    create_investment_account,
    create_investment,
    create_investment_transfer,
    get_investment_transfers_by_period
)
from app.crud.period import create_period
from app.crud.account import create_account
from app.schemas.period import PeriodCreate
from app.schemas.account import AccountCreate
from app.schemas.investment import (
    InvestmentAccountCreate,
    InvestmentCreate,
    InvestmentTransferCreate
)
from app.models.user import User
from app.models.currency import Currency


class TestInvestmentLifecycle:
    """Test full lifecycle of investment operations."""
    
    def test_create_investment_account(self, db: Session, test_user: User):
        """Test: Create investment account."""
        acc_data = InvestmentAccountCreate(
            account_name="Brokerage A",
            account_type="BROKERAGE",
            notes="Main stocks"
        )
        
        acc = create_investment_account(db, test_user.id, acc_data)
        
        assert acc.account_name == "Brokerage A"
        assert acc.account_type == "BROKERAGE"
        assert acc.is_active is True

    def test_create_investment_category(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Create investment category/holding."""
        acc = create_investment_account(db, test_user.id, InvestmentAccountCreate(
            account_name="Crypto Wallet", account_type="CRYPTO_EXCHANGE"
        ))
        
        inv_data = InvestmentCreate(
            category_name="Bitcoin",
            investment_account_id=acc.id,
            opening_balance=Decimal("1.5"),
            opening_balance_date=date(2026, 1, 1),
            opening_balance_currency_id=test_currency.id
        )
        
        inv = create_investment(db, test_user.id, inv_data)
        
        assert inv.category_name == "Bitcoin"
        assert inv.opening_balance == Decimal("1.5")
        assert inv.investment_account_id == acc.id

    def test_investment_transfer_flow(
        self, db: Session, test_user: User, test_currency: Currency
    ):
        """Test: Create and list investment transfers."""
        # Setup
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Inv Transfer", start_date=date(2026, 2, 1), end_date=date(2026, 2, 28), snapshot_date=date(2026, 2, 28)
        ))
        
        source_acc = create_account(db, test_user.id, AccountCreate(
            account_name="Bank", account_type="BANK", currency_id=test_currency.id
        ))
        
        inv_acc = create_investment_account(db, test_user.id, InvestmentAccountCreate(
            account_name="IRA", account_type="BROKERAGE"
        ))
        
        inv = create_investment(db, test_user.id, InvestmentCreate(
            category_name="S&P 500",
            investment_account_id=inv_acc.id,
            opening_balance=Decimal("0"),
            opening_balance_date=date(2026, 1, 1),
            opening_balance_currency_id=test_currency.id
        ))
        
        # Create transfer
        transfer_data = InvestmentTransferCreate(
            investment_id=inv.id,
            amount_transferred=Decimal("500.00"),
            currency_id=test_currency.id,
            source_account_id=source_acc.id,
            transfer_date=date(2026, 2, 15),
            units_added=Decimal("1.25")
        )
        
        transfer = create_investment_transfer(db, period.id, transfer_data)
        
        assert transfer.amount_transferred == Decimal("500.00")
        assert transfer.units_added == Decimal("1.25")
        
        # List transfers
        transfers = get_investment_transfers_by_period(db, period.id)
        assert len(transfers) == 1
        assert transfers[0].id == transfer.id
