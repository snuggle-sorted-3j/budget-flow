"""
Unit Tests for Reconciliation Service

This is the CRITICAL test module covering the core financial calculation logic
in app/services/reconciliation_service.py.

Tests cover:
- Basic balanced/unbalanced scenarios
- Previous period carry-over
- Investment transfers
- Installment payments
- Suspended expenses (in/out)
- Currency conversions
- Multi-currency scenarios
"""
import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.reconciliation_service import calculate_reconciliation
from app.models.calculation_period import CalculationPeriod
from app.models.currency import Currency
from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.income_entry import IncomeEntry
from app.models.expense_item import ExpenseItem
from app.models.investment_transfer import InvestmentTransfer
from app.models.installment_payment import InstallmentPayment
from app.models.installment_item import InstallmentItem
from app.models.suspended_expense import SuspendedExpense
from app.models.currency_conversion import CurrencyConversion


class TestReconciliationBasic:
    """Test basic reconciliation scenarios."""
    
    def test_reconciliation_balanced_basic(
        self, db: Session, test_user, test_currency, test_category
    ):
        """
        Test: Period with income - expenses = snapshot → balanced
        Setup: income=1000, expense=200, snapshot=800
        Expected: is_balanced=True, difference=0
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.income import create_income
        from app.crud.expense import create_expense
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        from app.schemas.expense import ExpenseCreate
        
        # Create period
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Balanced Test",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            snapshot_date=date(2026, 1, 31)
        ))
        
        # Create account
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Test Account",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        
        # Add income: +1000
        create_income(db, period.id, IncomeCreate(
            source_name="Salary",
            amount=Decimal("1000.00"),
            currency_id=test_currency.id
        ))
        
        # Add expense: -200
        create_expense(db, period.id, ExpenseCreate(
            item_name="Groceries",
            amount=Decimal("200.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        # Set snapshot: 800 (expected balance)
        upsert_snapshot(db, period.id, account.id, Decimal("800.00"))
        
        # Calculate reconciliation
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        assert result is not None
        assert result.overall_balanced is True
        
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.expected_balance == Decimal("800.00")
        assert summary.actual_balance == Decimal("800.00")
        assert summary.difference == Decimal("0.00")
        assert summary.is_balanced is True

    def test_reconciliation_unbalanced(
        self, db: Session, test_user, test_currency, test_category
    ):
        """
        Test: Period where snapshot doesn't match expected → unbalanced
        Setup: income=1000, expense=200, snapshot=500 (should be 800)
        Expected: is_balanced=False, difference=300
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.income import create_income
        from app.crud.expense import create_expense
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        from app.schemas.expense import ExpenseCreate
        
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Unbalanced Test",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            snapshot_date=date(2026, 2, 28)
        ))
        
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Unbalanced Account",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        
        create_income(db, period.id, IncomeCreate(
            source_name="Income",
            amount=Decimal("1000.00"),
            currency_id=test_currency.id
        ))
        
        create_expense(db, period.id, ExpenseCreate(
            item_name="Expense",
            amount=Decimal("200.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        # Wrong snapshot - should be 800
        upsert_snapshot(db, period.id, account.id, Decimal("500.00"))
        
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        assert result.overall_balanced is False
        
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.expected_balance == Decimal("800.00")
        assert summary.actual_balance == Decimal("500.00")
        assert summary.difference == Decimal("300.00")
        assert summary.is_balanced is False

    def test_reconciliation_period_not_found(self, db: Session, test_user):
        """
        Test: Invalid period_id returns None
        """
        result = calculate_reconciliation(db, test_user.id, uuid4())
        assert result is None


class TestReconciliationPeriodChaining:
    """Test reconciliation with previous period carry-over."""
    
    def test_first_period_uses_opening_balance(
        self, db: Session, test_user, test_currency
    ):
        """
        Test: First period (no previous) uses account opening balance
        Setup: Account with opening_balance=500
        Expected: starting_balance=500
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        
        # Create account WITH opening balance
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Opening Balance Account",
            account_type="BANK",
            currency_id=test_currency.id,
            opening_balance=Decimal("500.00")
        ))
        
        # Create first period (no previous)
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="First Period",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            snapshot_date=date(2026, 1, 31)
        ))
        
        # Snapshot = opening balance (no transactions)
        upsert_snapshot(db, period.id, account.id, Decimal("500.00"))
        
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.starting_balance == Decimal("500.00")
        assert summary.expected_balance == Decimal("500.00")
        assert summary.is_balanced is True

    def test_uses_previous_period_snapshot(
        self, db: Session, test_user, test_currency
    ):
        """
        Test: Second period uses previous period's snapshot as starting balance
        Setup: Period 1 snapshot=5000, Period 2 should start at 5000
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.balance_snapshot import upsert_snapshot
        from app.crud.income import create_income
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Chain Account",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        
        # Period 1 (Jan)
        period1 = create_period(db, test_user.id, PeriodCreate(
            period_name="Jan",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            snapshot_date=date(2026, 1, 31)
        ))
        
        create_income(db, period1.id, IncomeCreate(
            source_name="Jan Income",
            amount=Decimal("5000.00"),
            currency_id=test_currency.id
        ))
        
        upsert_snapshot(db, period1.id, account.id, Decimal("5000.00"))
        
        # Period 2 (Feb)
        period2 = create_period(db, test_user.id, PeriodCreate(
            period_name="Feb",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            snapshot_date=date(2026, 2, 28)
        ))
        
        create_income(db, period2.id, IncomeCreate(
            source_name="Feb Income",
            amount=Decimal("2000.00"),
            currency_id=test_currency.id
        ))
        
        # Feb snapshot: 5000 (start) + 2000 (income) = 7000
        upsert_snapshot(db, period2.id, account.id, Decimal("7000.00"))
        
        result = calculate_reconciliation(db, test_user.id, period2.id)
        
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.starting_balance == Decimal("5000.00")
        assert summary.total_income == Decimal("2000.00")
        assert summary.expected_balance == Decimal("7000.00")
        assert summary.is_balanced is True


class TestReconciliationInvestments:
    """Test reconciliation with investment transfers."""
    
    def test_investment_transfer_subtracts_from_expected(
        self, db: Session, test_user, test_currency
    ):
        """
        Test: Investment transfer reduces expected balance
        Setup: income=3000, investment_transfer=1000
        Expected: expected_balance = 0 + 3000 - 1000 = 2000
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.income import create_income
        from app.crud.investment import create_investment_account, create_investment, create_investment_transfer
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        from app.schemas.investment import InvestmentAccountCreate, InvestmentCreate, InvestmentTransferCreate
        
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Investment Source",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Investment Period",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            snapshot_date=date(2026, 3, 31)
        ))
        
        # Add income
        create_income(db, period.id, IncomeCreate(
            source_name="Salary",
            amount=Decimal("3000.00"),
            currency_id=test_currency.id
        ))
        
        # Create investment account and investment
        inv_account = create_investment_account(db, test_user.id, InvestmentAccountCreate(
            account_name="Brokerage",
            account_type="BROKERAGE"
        ))
        
        investment = create_investment(db, test_user.id, InvestmentCreate(
            category_name="Stocks",
            investment_account_id=inv_account.id,
            opening_balance=Decimal("0.00"),
            opening_balance_date=date(2026, 3, 1),
            opening_balance_currency_id=test_currency.id
        ))
        
        # Create transfer: 1000 from bank to investment
        create_investment_transfer(db, period.id, InvestmentTransferCreate(
            investment_id=investment.id,
            amount_transferred=Decimal("1000.00"),
            currency_id=test_currency.id,
            source_account_id=account.id,
            transfer_date=date(2026, 3, 15)
        ))
        
        # Snapshot: 3000 - 1000 = 2000
        upsert_snapshot(db, period.id, account.id, Decimal("2000.00"))
        
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.total_income == Decimal("3000.00")
        assert summary.expected_balance == Decimal("2000.00")
        assert summary.is_balanced is True


class TestReconciliationInstallments:
    """Test reconciliation with installment payments."""
    
    def test_installment_payment_subtracts_from_expected(
        self, db: Session, test_user, test_currency
    ):
        """
        Test: Installment payment reduces expected balance
        Setup: income=2000, installment_payment=200
        Expected: expected_balance = 0 + 2000 - 200 = 1800
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.income import create_income
        from app.crud.installment import create_installment_item, create_installment_payment
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        from app.schemas.installment import InstallmentItemCreate, InstallmentPaymentCreate
        
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Installment Account",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Installment Period",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
            snapshot_date=date(2026, 4, 30)
        ))
        
        create_income(db, period.id, IncomeCreate(
            source_name="Salary",
            amount=Decimal("2000.00"),
            currency_id=test_currency.id
        ))
        
        # Create installment item
        installment = create_installment_item(db, test_user.id, InstallmentItemCreate(
            item_name="Laptop",
            total_price=Decimal("1200.00"),
            currency_id=test_currency.id,
            initial_period_id=period.id,
            monthly_payment_amount=Decimal("200.00"),
            months_to_pay=6
        ))
        
        # Create payment
        create_installment_payment(db, installment.id, period.id, InstallmentPaymentCreate(
            payment_amount=Decimal("200.00"),
            payment_date=date(2026, 4, 15)
        ))
        
        # Snapshot: 2000 - 200 = 1800
        upsert_snapshot(db, period.id, account.id, Decimal("1800.00"))
        
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.total_installments == Decimal("200.00")
        assert summary.expected_balance == Decimal("1800.00")
        assert summary.is_balanced is True


class TestReconciliationSuspended:
    """Test reconciliation with suspended expenses (loans)."""
    
    def test_suspended_out_subtracts_from_expected(
        self, db: Session, test_user, test_currency
    ):
        """
        Test: Loan given (suspended out) reduces expected balance
        Setup: income=1500, suspended_out=300
        Expected: expected_balance = 0 + 1500 - 300 = 1200
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.income import create_income
        from app.crud.suspended_expense import create_suspended_expense
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        from app.schemas.suspended_expense import SuspendedExpenseCreate
        
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Suspended Account",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Suspended Out Period",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 31),
            snapshot_date=date(2026, 5, 31)
        ))
        
        create_income(db, period.id, IncomeCreate(
            source_name="Salary",
            amount=Decimal("1500.00"),
            currency_id=test_currency.id
        ))
        
        # Create suspended expense (loan given to friend)
        create_suspended_expense(db, test_user.id, period.id, SuspendedExpenseCreate(
            item_name="Loan to Friend",
            amount=Decimal("300.00"),
            currency_id=test_currency.id,
            transaction_type="LOAN_OUT",
        ))
        
        # Snapshot: 1500 - 300 = 1200
        upsert_snapshot(db, period.id, account.id, Decimal("1200.00"))
        
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.expected_balance == Decimal("1200.00")
        assert summary.is_balanced is True

    def test_suspended_in_adds_to_expected(
        self, db: Session, test_user, test_currency
    ):
        """
        Test: Loan settled (suspended in) increases expected balance
        Setup: Starting with loan outstanding, then settled in current period
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.income import create_income
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        from app.models.suspended_expense import SuspendedExpense
        
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Settled Account",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        
        # Previous period where loan was given
        period1 = create_period(db, test_user.id, PeriodCreate(
            period_name="Loan Given Period",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 31),
            snapshot_date=date(2026, 5, 31)
        ))
        
        create_income(db, period1.id, IncomeCreate(
            source_name="Income",
            amount=Decimal("1000.00"),
            currency_id=test_currency.id
        ))
        
        upsert_snapshot(db, period1.id, account.id, Decimal("700.00"))  # 1000 - 300 loan
        
        # Current period where loan is settled
        period2 = create_period(db, test_user.id, PeriodCreate(
            period_name="Loan Settled Period",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
            snapshot_date=date(2026, 6, 30)
        ))
        
        # Create suspended expense in period1, settle in period2
        suspended = SuspendedExpense(
            user_id=test_user.id,
            item_name="Settled Loan",
            amount=Decimal("300.00"),
            currency_id=test_currency.id,
            transaction_type="LOAN_OUT",
            created_period_id=period1.id,
            settled_period_id=period2.id,
            status="SETTLED"
        )
        db.add(suspended)
        db.commit()
        
        create_income(db, period2.id, IncomeCreate(
            source_name="June Income",
            amount=Decimal("500.00"),
            currency_id=test_currency.id
        ))
        
        # Snapshot: 700 (start) + 500 (income) + 300 (loan repaid) = 1500
        upsert_snapshot(db, period2.id, account.id, Decimal("1500.00"))
        
        result = calculate_reconciliation(db, test_user.id, period2.id)
        
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.starting_balance == Decimal("700.00")
        assert summary.total_income == Decimal("500.00")
        assert summary.expected_balance == Decimal("1500.00")
        assert summary.is_balanced is True


class TestReconciliationCurrencyConversion:
    """Test reconciliation with currency conversions."""
    
    def test_conversion_affects_both_currencies(self, db: Session, test_user):
        """
        Test: Currency conversion properly affects both source and target currencies
        Setup: Convert 200 USD to 185 EUR
        Expected: USD reduced by 200, EUR increased by 185
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.currency import create_currency
        from app.crud.income import create_income
        from app.crud.currency_conversion import create_currency_conversion
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.currency import CurrencyCreate
        from app.schemas.income import IncomeCreate
        from app.schemas.currency_conversion import CurrencyConversionCreate
        
        # Create USD & EUR currencies
        usd = create_currency(db, test_user.id, CurrencyCreate(
            ticker="USD",
            name="US Dollar",
            is_default=True
        ))
        
        eur = create_currency(db, test_user.id, CurrencyCreate(
            ticker="EUR",
            name="Euro",
            is_default=False
        ))
        
        # Create accounts in each currency
        usd_account = create_account(db, test_user.id, AccountCreate(
            account_name="USD Account",
            account_type="BANK",
            currency_id=usd.id
        ))
        
        eur_account = create_account(db, test_user.id, AccountCreate(
            account_name="EUR Account",
            account_type="BANK",
            currency_id=eur.id
        ))
        
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Conversion Period",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            snapshot_date=date(2026, 7, 31)
        ))
        
        # Add USD income
        create_income(db, period.id, IncomeCreate(
            source_name="USD Salary",
            amount=Decimal("1000.00"),
            currency_id=usd.id
        ))
        
        # Add EUR income
        create_income(db, period.id, IncomeCreate(
            source_name="EUR Payment",
            amount=Decimal("500.00"),
            currency_id=eur.id
        ))
        
        # Convert 200 USD to 185 EUR
        create_currency_conversion(db, CurrencyConversionCreate(
            from_currency_id=usd.id,
            to_currency_id=eur.id,
            from_amount=Decimal("200.00"),
            to_amount=Decimal("185.00"),
            conversion_date=date(2026, 7, 15),
            rate=Decimal("0.925"),

        ), period.id)
        
        # USD: 1000 - 200 = 800
        upsert_snapshot(db, period.id, usd_account.id, Decimal("800.00"))
        # EUR: 500 + 185 = 685
        upsert_snapshot(db, period.id, eur_account.id, Decimal("685.00"))
        
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        assert result.overall_balanced is True
        
        usd_summary = next(r for r in result.reconciliations if r.currency_ticker == "USD")
        assert usd_summary.total_conversions_out == Decimal("200.00")
        assert usd_summary.expected_balance == Decimal("800.00")
        assert usd_summary.is_balanced is True
        
        eur_summary = next(r for r in result.reconciliations if r.currency_ticker == "EUR")
        assert eur_summary.total_conversions_in == Decimal("185.00")
        assert eur_summary.expected_balance == Decimal("685.00")
        assert eur_summary.is_balanced is True


class TestReconciliationComplex:
    """Test complex scenarios with multiple components."""
    
    def test_complex_full_scenario(
        self, db: Session, test_user, test_currency, test_category
    ):
        """
        Test: Complex scenario with income, expenses, investments, installments, suspended
        Setup: 
          - Starting: 10000
          - Income: 5000 + 500 = 5500
          - Expenses: 1500 + 400 + 600 = 2500
          - Investment: 1000
          - Installment: 300
          - Suspended out: 200
        Expected: 10000 + 5500 - 2500 - 1000 - 300 - 200 = 11500
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.income import create_income
        from app.crud.expense import create_expense
        from app.crud.investment import create_investment_account, create_investment, create_investment_transfer
        from app.crud.installment import create_installment_item, create_installment_payment
        from app.crud.suspended_expense import create_suspended_expense
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        from app.schemas.expense import ExpenseCreate
        from app.schemas.investment import InvestmentAccountCreate, InvestmentCreate, InvestmentTransferCreate
        from app.schemas.installment import InstallmentItemCreate, InstallmentPaymentCreate
        from app.schemas.suspended_expense import SuspendedExpenseCreate
        
        # Create account with opening balance
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Complex Account",
            account_type="BANK",
            currency_id=test_currency.id,
            opening_balance=Decimal("10000.00")
        ))
        
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Complex Period",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            snapshot_date=date(2026, 8, 31)
        ))
        
        # Incomes
        create_income(db, period.id, IncomeCreate(
            source_name="Salary",
            amount=Decimal("5000.00"),
            currency_id=test_currency.id
        ))
        create_income(db, period.id, IncomeCreate(
            source_name="Side Income",
            amount=Decimal("500.00"),
            currency_id=test_currency.id
        ))
        
        # Expenses
        create_expense(db, period.id, ExpenseCreate(
            item_name="Rent",
            amount=Decimal("1500.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        create_expense(db, period.id, ExpenseCreate(
            item_name="Utilities",
            amount=Decimal("400.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        create_expense(db, period.id, ExpenseCreate(
            item_name="Food",
            amount=Decimal("600.00"),
            currency_id=test_currency.id,
            category_id=test_category.id
        ))
        
        # Investment transfer
        inv_account = create_investment_account(db, test_user.id, InvestmentAccountCreate(
            account_name="Stocks",
            account_type="BROKERAGE"
        ))
        investment = create_investment(db, test_user.id, InvestmentCreate(
            category_name="ETF",
            investment_account_id=inv_account.id,
            opening_balance=Decimal("0.00"),
            opening_balance_date=date(2026, 8, 1),
            opening_balance_currency_id=test_currency.id
        ))
        create_investment_transfer(db, period.id, InvestmentTransferCreate(
            investment_id=investment.id,
            amount_transferred=Decimal("1000.00"),
            currency_id=test_currency.id,
            source_account_id=account.id,
            transfer_date=date(2026, 8, 20)
        ))
        
        # Installment
        installment = create_installment_item(db, test_user.id, InstallmentItemCreate(
            item_name="Phone",
            total_price=Decimal("900.00"),
            currency_id=test_currency.id,
            initial_period_id=period.id,
            monthly_payment_amount=Decimal("300.00"),
            months_to_pay=3
        ))
        create_installment_payment(db, installment.id, period.id, InstallmentPaymentCreate(
            payment_amount=Decimal("300.00"),
            payment_date=date(2026, 8, 25)
        ))
        
        # Suspended expense
        create_suspended_expense(db, test_user.id, period.id, SuspendedExpenseCreate(
            item_name="Loan to Colleague",
            amount=Decimal("200.00"),
            currency_id=test_currency.id,
            transaction_type="LOAN_OUT",
        ))
        
        # Snapshot: 10000 + 5500 - 2500 - 1000 - 300 - 200 = 11500
        upsert_snapshot(db, period.id, account.id, Decimal("11500.00"))
        
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        assert result.overall_balanced is True
        
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.starting_balance == Decimal("10000.00")
        assert summary.total_income == Decimal("5500.00")
        assert summary.total_expenses == Decimal("2500.00")
        assert summary.total_installments == Decimal("300.00")
        assert summary.expected_balance == Decimal("11500.00")
        assert summary.actual_balance == Decimal("11500.00")
        assert summary.difference == Decimal("0.00")
        assert summary.is_balanced is True


class TestReconciliationEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_transactions_balanced(self, db: Session, test_user, test_currency):
        """
        Test: Period with no transactions is balanced with 0 snapshot
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        
        account = create_account(db, test_user.id, AccountCreate(
            account_name="Empty Account",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Empty Period",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            snapshot_date=date(2026, 9, 30)
        ))
        
        upsert_snapshot(db, period.id, account.id, Decimal("0.00"))
        
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        assert result.overall_balanced is True
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.expected_balance == Decimal("0.00")
        assert summary.is_balanced is True

    def test_multiple_accounts_summed(self, db: Session, test_user, test_currency):
        """
        Test: Multiple accounts in same currency are summed correctly
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.income import create_income
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        
        # Create 3 accounts in same currency
        account1 = create_account(db, test_user.id, AccountCreate(
            account_name="Account 1",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        account2 = create_account(db, test_user.id, AccountCreate(
            account_name="Account 2",
            account_type="CASH",
            currency_id=test_currency.id
        ))
        account3 = create_account(db, test_user.id, AccountCreate(
            account_name="Account 3",
            account_type="BANK",
            currency_id=test_currency.id
        ))
        
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Multi Account Period",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            snapshot_date=date(2026, 10, 31)
        ))
        
        # Total income: 3000
        create_income(db, period.id, IncomeCreate(
            source_name="Income",
            amount=Decimal("3000.00"),
            currency_id=test_currency.id
        ))
        
        # Split across accounts: 1000 + 1500 + 500 = 3000
        upsert_snapshot(db, period.id, account1.id, Decimal("1000.00"))
        upsert_snapshot(db, period.id, account2.id, Decimal("1500.00"))
        upsert_snapshot(db, period.id, account3.id, Decimal("500.00"))
        
        result = calculate_reconciliation(db, test_user.id, period.id)
        
        assert result.overall_balanced is True
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)
        assert summary.actual_balance == Decimal("3000.00")
        assert summary.is_balanced is True
