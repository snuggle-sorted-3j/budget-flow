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


class TestReconciliationKillMutants:
    """
    Targeted tests written to kill surviving mutmut mutants.

    Each test uses ≥2 items per category so that `+= last` mutations
    produce a wrong total (not equal to the sum of all items).
    """

    # ------------------------------------------------------------------ #
    # Mutant 20: actual_balance += snap.balance  →  -= snap.balance       #
    # ------------------------------------------------------------------ #
    def test_actual_balance_sums_multiple_snapshots(
        self, db: Session, test_user, test_currency
    ):
        """
        Two accounts each with a distinct snapshot; actual_balance must equal
        their SUM (kills the += → -= mutation on actual_balance accumulation).
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate

        a1 = create_account(db, test_user.id, AccountCreate(
            account_name="Snap A", account_type="BANK", currency_id=test_currency.id
        ))
        a2 = create_account(db, test_user.id, AccountCreate(
            account_name="Snap B", account_type="CASH", currency_id=test_currency.id
        ))

        period = create_period(db, test_user.id, PeriodCreate(
            period_name="ActualBalMutant",
            start_date=date(2027, 1, 1), end_date=date(2027, 1, 31),
            snapshot_date=date(2027, 1, 31)
        ))

        upsert_snapshot(db, period.id, a1.id, Decimal("1300.00"))
        upsert_snapshot(db, period.id, a2.id, Decimal("700.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)
        summary = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        # Sum must be 2000; mutation (−=) would produce −2000
        assert summary.actual_balance == Decimal("2000.00")

    # ------------------------------------------------------------------ #
    # Mutant 24: Account.currency_id != currency.id (wrong filter)        #
    # ------------------------------------------------------------------ #
    def test_previous_period_starting_balance_only_same_currency(
        self, db: Session, test_user
    ):
        """
        Two currencies, two accounts. Starting balance for currency A must
        only include the currency-A account snapshot from the previous period
        (kills mutant that flips == to != in the currency filter).
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.currency import create_currency
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.currency import CurrencyCreate

        cur_a = create_currency(db, test_user.id, CurrencyCreate(
            ticker="KLA", name="Killa", is_default=True
        ))
        cur_b = create_currency(db, test_user.id, CurrencyCreate(
            ticker="KLB", name="KillaB", is_default=False
        ))

        acc_a = create_account(db, test_user.id, AccountCreate(
            account_name="AccA", account_type="BANK", currency_id=cur_a.id
        ))
        acc_b = create_account(db, test_user.id, AccountCreate(
            account_name="AccB", account_type="BANK", currency_id=cur_b.id
        ))

        p1 = create_period(db, test_user.id, PeriodCreate(
            period_name="CurrencyFilterP1",
            start_date=date(2027, 2, 1), end_date=date(2027, 2, 28),
            snapshot_date=date(2027, 2, 28)
        ))
        upsert_snapshot(db, p1.id, acc_a.id, Decimal("4000.00"))
        upsert_snapshot(db, p1.id, acc_b.id, Decimal("9000.00"))

        p2 = create_period(db, test_user.id, PeriodCreate(
            period_name="CurrencyFilterP2",
            start_date=date(2027, 3, 1), end_date=date(2027, 3, 31),
            snapshot_date=date(2027, 3, 31)
        ))
        upsert_snapshot(db, p2.id, acc_a.id, Decimal("4000.00"))
        upsert_snapshot(db, p2.id, acc_b.id, Decimal("9000.00"))

        result = calculate_reconciliation(db, test_user.id, p2.id)

        kla = next(r for r in result.reconciliations if r.currency_ticker == "KLA")
        klb = next(r for r in result.reconciliations if r.currency_ticker == "KLB")

        # Each currency's starting balance must come from its own account only
        assert kla.starting_balance == Decimal("4000.00")
        assert klb.starting_balance == Decimal("9000.00")

    # ------------------------------------------------------------------ #
    # Mutant 26: starting_balance = snap.balance  (overwrites instead of +=)
    # ------------------------------------------------------------------ #
    def test_previous_period_starting_balance_sums_multiple_accounts(
        self, db: Session, test_user, test_currency
    ):
        """
        Two accounts in same currency in previous period; starting balance must
        equal their SUM (kills += → = mutation on starting_balance from prev period).
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate

        a1 = create_account(db, test_user.id, AccountCreate(
            account_name="Prev1", account_type="BANK", currency_id=test_currency.id
        ))
        a2 = create_account(db, test_user.id, AccountCreate(
            account_name="Prev2", account_type="CASH", currency_id=test_currency.id
        ))

        p1 = create_period(db, test_user.id, PeriodCreate(
            period_name="PrevSumP1",
            start_date=date(2027, 4, 1), end_date=date(2027, 4, 30),
            snapshot_date=date(2027, 4, 30)
        ))
        upsert_snapshot(db, p1.id, a1.id, Decimal("2500.00"))
        upsert_snapshot(db, p1.id, a2.id, Decimal("1500.00"))  # total: 4000

        p2 = create_period(db, test_user.id, PeriodCreate(
            period_name="PrevSumP2",
            start_date=date(2027, 5, 1), end_date=date(2027, 5, 31),
            snapshot_date=date(2027, 5, 31)
        ))
        # No transactions; snapshot equals starting balance
        upsert_snapshot(db, p2.id, a1.id, Decimal("2500.00"))
        upsert_snapshot(db, p2.id, a2.id, Decimal("1500.00"))

        result = calculate_reconciliation(db, test_user.id, p2.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        # starting_balance = 2500 + 1500 = 4000 (not 1500 if last-only bug)
        assert s.starting_balance == Decimal("4000.00")
        assert s.is_balanced is True

    # ------------------------------------------------------------------ #
    # Mutant 32: starting_balance = Decimal(str(acc.opening_balance))     #
    #            (overwrites instead of +=, first-period opening balances) #
    # ------------------------------------------------------------------ #
    def test_opening_balance_sums_multiple_accounts(
        self, db: Session, test_user, test_currency
    ):
        """
        First period, two accounts with opening balances; starting_balance
        must be their SUM (kills += → = on opening_balance accumulation).
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate

        a1 = create_account(db, test_user.id, AccountCreate(
            account_name="Opening1", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("1200.00")
        ))
        a2 = create_account(db, test_user.id, AccountCreate(
            account_name="Opening2", account_type="CASH",
            currency_id=test_currency.id, opening_balance=Decimal("800.00")
        ))

        period = create_period(db, test_user.id, PeriodCreate(
            period_name="OpeningBalSum",
            start_date=date(2027, 6, 1), end_date=date(2027, 6, 30),
            snapshot_date=date(2027, 6, 30)
        ))
        upsert_snapshot(db, period.id, a1.id, Decimal("1200.00"))
        upsert_snapshot(db, period.id, a2.id, Decimal("800.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        # starting_balance = 1200 + 800 = 2000 (not 800 if last-only bug)
        assert s.starting_balance == Decimal("2000.00")
        assert s.is_balanced is True

    # ------------------------------------------------------------------ #
    # Mutant 53: total_transfers = t.amount_transferred  (overwrites +=)  #
    # ------------------------------------------------------------------ #
    def test_multiple_investment_transfers_summed(
        self, db: Session, test_user, test_currency
    ):
        """
        Two investment transfers in same period; total must be their SUM
        (kills += → = mutation on total_transfers accumulation).
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.income import create_income
        from app.crud.investment import (
            create_investment_account, create_investment, create_investment_transfer
        )
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate
        from app.schemas.income import IncomeCreate
        from app.schemas.investment import (
            InvestmentAccountCreate, InvestmentCreate, InvestmentTransferCreate
        )

        account = create_account(db, test_user.id, AccountCreate(
            account_name="MultiTransferSrc", account_type="BANK",
            currency_id=test_currency.id
        ))

        period = create_period(db, test_user.id, PeriodCreate(
            period_name="MultiTransfer",
            start_date=date(2027, 7, 1), end_date=date(2027, 7, 31),
            snapshot_date=date(2027, 7, 31)
        ))

        create_income(db, period.id, IncomeCreate(
            source_name="Income", amount=Decimal("5000.00"),
            currency_id=test_currency.id
        ))

        inv_acc = create_investment_account(db, test_user.id, InvestmentAccountCreate(
            account_name="Broker", account_type="BROKERAGE"
        ))
        inv1 = create_investment(db, test_user.id, InvestmentCreate(
            category_name="ETF1", investment_account_id=inv_acc.id,
            opening_balance=Decimal("0.00"), opening_balance_date=date(2027, 7, 1),
            opening_balance_currency_id=test_currency.id
        ))
        inv2 = create_investment(db, test_user.id, InvestmentCreate(
            category_name="ETF2", investment_account_id=inv_acc.id,
            opening_balance=Decimal("0.00"), opening_balance_date=date(2027, 7, 1),
            opening_balance_currency_id=test_currency.id
        ))

        create_investment_transfer(db, period.id, InvestmentTransferCreate(
            investment_id=inv1.id, amount_transferred=Decimal("600.00"),
            currency_id=test_currency.id, source_account_id=account.id,
            transfer_date=date(2027, 7, 10)
        ))
        create_investment_transfer(db, period.id, InvestmentTransferCreate(
            investment_id=inv2.id, amount_transferred=Decimal("400.00"),
            currency_id=test_currency.id, source_account_id=account.id,
            transfer_date=date(2027, 7, 20)
        ))

        # expected: 0 + 5000 - 600 - 400 = 4000
        upsert_snapshot(db, period.id, account.id, Decimal("4000.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        # total_transfers must be 1000 (not just 400 from the last transfer)
        assert s.expected_balance == Decimal("4000.00")
        assert s.is_balanced is True

    # ------------------------------------------------------------------ #
    # Mutant 60: status filter "CONVERTED_TO_EXPENSE" → "XXCONVERTED..."  #
    # Mutant 62: total_suspended_out = s.amount  (overwrites +=)          #
    # ------------------------------------------------------------------ #
    def test_converted_to_expense_excluded_from_suspended_out(
        self, db: Session, test_user, test_currency
    ):
        """
        A CONVERTED_TO_EXPENSE item must NOT be counted as suspended_out.
        Two PENDING items must both be counted (kills mutant 60 + 62).
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
            account_name="SuspOutAcc", account_type="BANK",
            currency_id=test_currency.id
        ))

        period = create_period(db, test_user.id, PeriodCreate(
            period_name="SuspOutFilter",
            start_date=date(2027, 8, 1), end_date=date(2027, 8, 31),
            snapshot_date=date(2027, 8, 31)
        ))

        create_income(db, period.id, IncomeCreate(
            source_name="Income", amount=Decimal("3000.00"),
            currency_id=test_currency.id
        ))

        # Two PENDING loans — both should count as suspended_out
        pending1 = SuspendedExpense(
            user_id=test_user.id, item_name="Loan1", amount=Decimal("200.00"),
            currency_id=test_currency.id, transaction_type="LOAN_OUT",
            created_period_id=period.id, status="PENDING"
        )
        pending2 = SuspendedExpense(
            user_id=test_user.id, item_name="Loan2", amount=Decimal("300.00"),
            currency_id=test_currency.id, transaction_type="LOAN_OUT",
            created_period_id=period.id, status="PENDING"
        )
        # This one is CONVERTED_TO_EXPENSE — must NOT count
        converted = SuspendedExpense(
            user_id=test_user.id, item_name="ConvertedLoan",
            amount=Decimal("9999.00"),
            currency_id=test_currency.id, transaction_type="LOAN_OUT",
            created_period_id=period.id, status="CONVERTED_TO_EXPENSE"
        )
        db.add_all([pending1, pending2, converted])
        db.commit()

        # expected: 0 + 3000 - 200 - 300 = 2500 (CONVERTED_TO_EXPENSE not deducted)
        upsert_snapshot(db, period.id, account.id, Decimal("2500.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        assert s.is_balanced is True
        assert s.expected_balance == Decimal("2500.00")

    # ------------------------------------------------------------------ #
    # Mutant 71: total_suspended_in = s.amount  (overwrites +=)           #
    # ------------------------------------------------------------------ #
    def test_multiple_suspended_in_summed(
        self, db: Session, test_user, test_currency
    ):
        """
        Two settled loans in same period; total_suspended_in must equal
        their SUM (kills += → = mutation).
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
            account_name="SuspInAcc", account_type="BANK",
            currency_id=test_currency.id
        ))

        period = create_period(db, test_user.id, PeriodCreate(
            period_name="SuspInSum",
            start_date=date(2027, 9, 1), end_date=date(2027, 9, 30),
            snapshot_date=date(2027, 9, 30)
        ))

        create_income(db, period.id, IncomeCreate(
            source_name="Sep Income", amount=Decimal("1000.00"),
            currency_id=test_currency.id
        ))

        # Two loans created in a prior period, both settled in this period
        settled1 = SuspendedExpense(
            user_id=test_user.id, item_name="SIn1", amount=Decimal("150.00"),
            currency_id=test_currency.id, transaction_type="LOAN_OUT",
            created_period_id=period.id,
            settled_period_id=period.id, status="SETTLED"
        )
        settled2 = SuspendedExpense(
            user_id=test_user.id, item_name="SIn2", amount=Decimal("250.00"),
            currency_id=test_currency.id, transaction_type="LOAN_OUT",
            created_period_id=period.id,
            settled_period_id=period.id, status="SETTLED"
        )
        db.add_all([settled1, settled2])
        db.commit()

        # expected: 0 + 1000 + 150 + 250 - 150 - 250 (also suspended_out) = 1000
        # Wait: settled loans were also created_period_id=period, so they count as suspended_out too
        # expected = 0 + 1000 - (150+250) + (150+250) = 1000
        upsert_snapshot(db, period.id, account.id, Decimal("1000.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        assert s.is_balanced is True

    # ------------------------------------------------------------------ #
    # Mutants 77-78: total_installments = ip.payment_amount or -= (wrong) #
    # ------------------------------------------------------------------ #
    def test_multiple_installment_payments_summed(
        self, db: Session, test_user, test_currency
    ):
        """
        Two installment payments in same period; total must equal their SUM
        (kills both += → = and += → -= mutations).
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
            account_name="InstMultiAcc", account_type="BANK",
            currency_id=test_currency.id
        ))

        period = create_period(db, test_user.id, PeriodCreate(
            period_name="InstMultiPay",
            start_date=date(2027, 10, 1), end_date=date(2027, 10, 31),
            snapshot_date=date(2027, 10, 31)
        ))

        create_income(db, period.id, IncomeCreate(
            source_name="Income", amount=Decimal("4000.00"),
            currency_id=test_currency.id
        ))

        inst1 = create_installment_item(db, test_user.id, InstallmentItemCreate(
            item_name="Laptop", total_price=Decimal("1200.00"),
            currency_id=test_currency.id, initial_period_id=period.id,
            monthly_payment_amount=Decimal("300.00"), months_to_pay=4
        ))
        inst2 = create_installment_item(db, test_user.id, InstallmentItemCreate(
            item_name="Phone", total_price=Decimal("600.00"),
            currency_id=test_currency.id, initial_period_id=period.id,
            monthly_payment_amount=Decimal("200.00"), months_to_pay=3
        ))

        create_installment_payment(db, inst1.id, period.id, InstallmentPaymentCreate(
            payment_amount=Decimal("300.00"), payment_date=date(2027, 10, 5)
        ))
        create_installment_payment(db, inst2.id, period.id, InstallmentPaymentCreate(
            payment_amount=Decimal("200.00"), payment_date=date(2027, 10, 10)
        ))

        # expected: 0 + 4000 - 300 - 200 = 3500
        upsert_snapshot(db, period.id, account.id, Decimal("3500.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        # total_installments = 500 (not 200 or -300 from wrong mutations)
        assert s.total_installments == Decimal("500.00")
        assert s.is_balanced is True

    # ------------------------------------------------------------------ #
    # Mutant 86: total_conversions_out = co.from_amount  (overwrites +=)  #
    # Mutant 91: total_conversions_in  = ci.to_amount    (overwrites +=)  #
    # ------------------------------------------------------------------ #
    def test_multiple_currency_conversions_summed(self, db: Session, test_user):
        """
        Two conversions in each direction; totals must be SUM of all items
        (kills += → = mutations on both conversion accumulators).
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

        usd = create_currency(db, test_user.id, CurrencyCreate(
            ticker="USD2", name="US Dollar", is_default=True
        ))
        eur = create_currency(db, test_user.id, CurrencyCreate(
            ticker="EUR2", name="Euro", is_default=False
        ))

        usd_acc = create_account(db, test_user.id, AccountCreate(
            account_name="USD2Acc", account_type="BANK", currency_id=usd.id
        ))
        eur_acc = create_account(db, test_user.id, AccountCreate(
            account_name="EUR2Acc", account_type="BANK", currency_id=eur.id
        ))

        period = create_period(db, test_user.id, PeriodCreate(
            period_name="MultiConv",
            start_date=date(2027, 11, 1), end_date=date(2027, 11, 30),
            snapshot_date=date(2027, 11, 30)
        ))

        create_income(db, period.id, IncomeCreate(
            source_name="USD Inc", amount=Decimal("2000.00"), currency_id=usd.id
        ))
        create_income(db, period.id, IncomeCreate(
            source_name="EUR Inc", amount=Decimal("1000.00"), currency_id=eur.id
        ))

        # Two conversions FROM USD → EUR
        create_currency_conversion(db, CurrencyConversionCreate(
            from_currency_id=usd.id, to_currency_id=eur.id,
            from_amount=Decimal("300.00"), to_amount=Decimal("270.00"),
            conversion_date=date(2027, 11, 5), rate=Decimal("0.90")
        ), period.id)
        create_currency_conversion(db, CurrencyConversionCreate(
            from_currency_id=usd.id, to_currency_id=eur.id,
            from_amount=Decimal("200.00"), to_amount=Decimal("180.00"),
            conversion_date=date(2027, 11, 15), rate=Decimal("0.90")
        ), period.id)

        # USD: 0 + 2000 - 300 - 200 = 1500
        # EUR: 0 + 1000 + 270 + 180 = 1450
        upsert_snapshot(db, period.id, usd_acc.id, Decimal("1500.00"))
        upsert_snapshot(db, period.id, eur_acc.id, Decimal("1450.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)

        usd_s = next(r for r in result.reconciliations if r.currency_ticker == "USD2")
        eur_s = next(r for r in result.reconciliations if r.currency_ticker == "EUR2")

        # total_conversions_out must be 500 (not just 200 if last-only bug)
        assert usd_s.total_conversions_out == Decimal("500.00")
        assert usd_s.is_balanced is True

        # total_conversions_in must be 450 (not just 180 if last-only bug)
        assert eur_s.total_conversions_in == Decimal("450.00")
        assert eur_s.is_balanced is True

    # ------------------------------------------------------------------ #
    # Mutant 6-7: snapshot_date <= start_date (boundary: same day)        #
    # ------------------------------------------------------------------ #
    def test_period_with_snapshot_date_equal_to_next_start_not_used_as_previous(
        self, db: Session, test_user, test_currency
    ):
        """
        A period whose snapshot_date equals the next period's start_date must
        NOT be treated as the previous period (strict < query).
        The second period should therefore use opening_balance (first period
        semantics), not the earlier period's snapshot.
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate

        # Account with zero opening balance
        account = create_account(db, test_user.id, AccountCreate(
            account_name="BoundaryAcc", account_type="BANK",
            currency_id=test_currency.id
        ))

        # Period whose snapshot_date == Feb 1 (same as next period's start)
        p1 = create_period(db, test_user.id, PeriodCreate(
            period_name="BoundaryP1",
            start_date=date(2027, 1, 1), end_date=date(2027, 2, 1),
            snapshot_date=date(2027, 2, 1)
        ))
        upsert_snapshot(db, p1.id, account.id, Decimal("5000.00"))

        # Period starting on Feb 1 — should NOT pick p1 as previous (< not <=)
        p2 = create_period(db, test_user.id, PeriodCreate(
            period_name="BoundaryP2",
            start_date=date(2027, 2, 1), end_date=date(2027, 2, 28),
            snapshot_date=date(2027, 2, 28)
        ))
        # No transactions; snapshot = 0 (opening balance of account)
        upsert_snapshot(db, p2.id, account.id, Decimal("0.00"))

        result = calculate_reconciliation(db, test_user.id, p2.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        # With strict <: p1.snapshot_date (Feb 1) is NOT < p2.start_date (Feb 1)
        # so p2 is treated as first period → starting_balance = opening_balance = 0
        assert s.starting_balance == Decimal("0.00")
        assert s.is_balanced is True


class TestReconciliationKillMutants2:
    """
    Second round kill-tests for remaining surviving mutants after first mutmut run.

    Targets:
    - Mutant 7:  .limit(2) — 3 periods triggers scalar_one_or_none MultipleResultsFound
    - Mutant 12: overall_balanced = False initial value
    - Mutant 19: actual_balance = snap.balance  (not += )
    - Mutant 40: total_income -= inc.amount
    - Mutant 66: settled_period_id != current  (brings in wrong-period items)
    - Mutant 68/69: status != "SETTLED" / "XXSETTLEDXX" (brings in non-settled items)
    - Mutant 72: total_suspended_in -= s.amount
    - Mutant 92: total_conversions_in -= ci.to_amount
    """

    # ------------------------------------------------------------------ #
    # Mutant 12: overall_balanced starts False — balanced period must return True
    # ------------------------------------------------------------------ #
    def test_overall_balanced_true_when_all_currencies_balanced(
        self, db: Session, test_user, test_currency
    ):
        """
        A perfectly balanced single-currency period must return overall_balanced=True.
        Kills mutant 12 (overall_balanced = False initial value).
        """
        from app.crud.period import create_period
        from app.crud.account import create_account
        from app.crud.balance_snapshot import upsert_snapshot
        from app.schemas.period import PeriodCreate
        from app.schemas.account import AccountCreate

        account = create_account(db, test_user.id, AccountCreate(
            account_name="BalanceTrue", account_type="BANK",
            currency_id=test_currency.id
        ))
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="BalTrue",
            start_date=date(2028, 1, 1), end_date=date(2028, 1, 31),
            snapshot_date=date(2028, 1, 31)
        ))
        upsert_snapshot(db, period.id, account.id, Decimal("0.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)

        # Must be True, not False (kills initial = False mutation)
        assert result.overall_balanced is True

    # ------------------------------------------------------------------ #
    # Mutant 66: settled_period_id != current_period.id  (wrong period filter)
    # ------------------------------------------------------------------ #
    def test_suspended_in_only_counts_items_settled_in_current_period(
        self, db: Session, test_user, test_currency
    ):
        """
        An item settled in a DIFFERENT period must NOT appear in total_suspended_in
        for the current period. (Kills mutant 66: != flips which period is queried.)
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
            account_name="SuspInPeriodAcc", account_type="BANK",
            currency_id=test_currency.id
        ))

        p1 = create_period(db, test_user.id, PeriodCreate(
            period_name="SuspInP1",
            start_date=date(2028, 2, 1), end_date=date(2028, 2, 28),
            snapshot_date=date(2028, 2, 28)
        ))
        p2 = create_period(db, test_user.id, PeriodCreate(
            period_name="SuspInP2",
            start_date=date(2028, 3, 1), end_date=date(2028, 3, 31),
            snapshot_date=date(2028, 3, 31)
        ))

        # Income in p2
        create_income(db, p2.id, IncomeCreate(
            source_name="P2Income", amount=Decimal("1000.00"),
            currency_id=test_currency.id
        ))

        # Loan settled in p1 (NOT p2 — should NOT count toward p2's suspended_in)
        settled_in_p1 = SuspendedExpense(
            user_id=test_user.id, item_name="SettledInP1",
            amount=Decimal("9999.00"),
            currency_id=test_currency.id, transaction_type="LOAN_OUT",
            created_period_id=p1.id,
            settled_period_id=p1.id, status="SETTLED"
        )
        # Loan settled in p2 — should count
        settled_in_p2 = SuspendedExpense(
            user_id=test_user.id, item_name="SettledInP2",
            amount=Decimal("200.00"),
            currency_id=test_currency.id, transaction_type="LOAN_OUT",
            created_period_id=p1.id,
            settled_period_id=p2.id, status="SETTLED"
        )
        db.add_all([settled_in_p1, settled_in_p2])
        db.commit()

        # expected p2: 5000 (prev snapshot from p1=0 since no snap) + 1000 + 200 = 1200
        # But p1 has no snapshot so p2's starting = opening balance = 0
        # Actually: p1 snapshot = 0+9999-9999 = 0 (p1 balanced)
        # p2: start=0 + 1000 + 200 (suspended_in) = 1200
        upsert_snapshot(db, p1.id, account.id, Decimal("0.00"))
        upsert_snapshot(db, p2.id, account.id, Decimal("1200.00"))

        result = calculate_reconciliation(db, test_user.id, p2.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        # suspended_in for p2 must be 200 (only SettledInP2), NOT 9999+200=10199
        assert s.is_balanced is True

    # ------------------------------------------------------------------ #
    # Mutant 68/69: status filter on suspended_in
    # "status != SETTLED" or "XXSETTLEDXX" means PENDING items are counted as in
    # ------------------------------------------------------------------ #
    def test_suspended_in_only_settled_status_counted(
        self, db: Session, test_user, test_currency
    ):
        """
        Only SETTLED items (settled in current period) add to total_suspended_in.
        PENDING items must NOT be counted (kills mutants 68 and 69).
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
            account_name="SuspStatusAcc", account_type="BANK",
            currency_id=test_currency.id
        ))
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="SuspStatusPeriod",
            start_date=date(2028, 4, 1), end_date=date(2028, 4, 30),
            snapshot_date=date(2028, 4, 30)
        ))

        create_income(db, period.id, IncomeCreate(
            source_name="April Income", amount=Decimal("2000.00"),
            currency_id=test_currency.id
        ))

        # PENDING loan (created here) — appears in suspended_out but NOT suspended_in
        pending = SuspendedExpense(
            user_id=test_user.id, item_name="PendingLoan", amount=Decimal("9999.00"),
            currency_id=test_currency.id, transaction_type="LOAN_OUT",
            created_period_id=period.id, status="PENDING"
        )
        # SETTLED loan from a previous period, settled here
        settled = SuspendedExpense(
            user_id=test_user.id, item_name="SettledLoan", amount=Decimal("300.00"),
            currency_id=test_currency.id, transaction_type="LOAN_OUT",
            created_period_id=period.id,
            settled_period_id=period.id, status="SETTLED"
        )
        db.add_all([pending, settled])
        db.commit()

        # expected: 0 + 2000 - 9999 (pending out) - 300 (settled out created here)
        #           + 300 (settled in) = 0 + 2000 - 9999 - 300 + 300 = -7999
        # With correct behavior: total_suspended_in = 300 (SETTLED only)
        # If mutant fires (status != "SETTLED"): picks up PENDING→ total_suspended_in=9999
        # expected_balance would be wildly different
        # Set snapshot to the correct expected value
        # 2000 - 9999 - 300 + 300 = -7999... that's negative and unbalanced.
        # Let's change: use only the SETTLED loan (no PENDING)
        # Better setup: no pending loans, one settled loan so the check is cleaner
        # Actually let's just verify total_suspended_in is 300 not 9999
        result = calculate_reconciliation(db, test_user.id, period.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        # total_suspended_in must be exactly 300 (the SETTLED item)
        # If mutant flips to != "SETTLED", it would pick up PENDING (9999)
        # We don't have a ReconciliationSummary.total_suspended_in field exposed...
        # Use expected_balance to infer: 0 + 2000 - (9999+300) + 300 = -7999
        assert s.expected_balance == Decimal("-7999.00")

    # ------------------------------------------------------------------ #
    # Mutant 72: total_suspended_in -= s.amount
    # ------------------------------------------------------------------ #
    def test_suspended_in_subtraction_mutation(
        self, db: Session, test_user, test_currency
    ):
        """
        Two settled loans returning money; their total adds to expected_balance.
        If -= is applied instead of +=, the balance would be wrong.
        (Kills mutant 72 which changes += to -=.)
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
            account_name="SuspInMinusAcc", account_type="BANK",
            currency_id=test_currency.id
        ))
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="SuspInMinus",
            start_date=date(2028, 5, 1), end_date=date(2028, 5, 31),
            snapshot_date=date(2028, 5, 31)
        ))
        create_income(db, period.id, IncomeCreate(
            source_name="May Income", amount=Decimal("1000.00"),
            currency_id=test_currency.id
        ))
        # Two settled loans returning money
        for amt in [Decimal("400.00"), Decimal("600.00")]:
            db.add(SuspendedExpense(
                user_id=test_user.id, item_name=f"Settled {amt}",
                amount=amt, currency_id=test_currency.id,
                transaction_type="LOAN_OUT",
                created_period_id=period.id,
                settled_period_id=period.id, status="SETTLED"
            ))
        db.commit()

        # expected: 0 + 1000 - (400+600) + (400+600) = 1000
        # With -= mutation: 0 + 1000 - 1000 - 1000 = -1000
        upsert_snapshot(db, period.id, account.id, Decimal("1000.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)
        s = next(r for r in result.reconciliations if r.currency_ticker == test_currency.ticker)

        # expected_balance = 1000; if -= bug, it would be -1000
        assert s.expected_balance == Decimal("1000.00")
        assert s.is_balanced is True

    # ------------------------------------------------------------------ #
    # Mutant 92: total_conversions_in -= ci.to_amount
    # ------------------------------------------------------------------ #
    def test_conversions_in_subtraction_mutation(self, db: Session, test_user):
        """
        Two conversions TO a currency; their total adds to expected_balance.
        If -= is applied, expected_balance would be negative.
        (Kills mutant 92: += → -=.)
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

        usd = create_currency(db, test_user.id, CurrencyCreate(
            ticker="USD3", name="USD3", is_default=True
        ))
        eur = create_currency(db, test_user.id, CurrencyCreate(
            ticker="EUR3", name="EUR3", is_default=False
        ))
        usd_acc = create_account(db, test_user.id, AccountCreate(
            account_name="USD3Acc", account_type="BANK", currency_id=usd.id
        ))
        eur_acc = create_account(db, test_user.id, AccountCreate(
            account_name="EUR3Acc", account_type="BANK", currency_id=eur.id
        ))
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="ConvInMinus",
            start_date=date(2028, 6, 1), end_date=date(2028, 6, 30),
            snapshot_date=date(2028, 6, 30)
        ))
        create_income(db, period.id, IncomeCreate(
            source_name="USD3 Inc", amount=Decimal("2000.00"), currency_id=usd.id
        ))
        create_income(db, period.id, IncomeCreate(
            source_name="EUR3 Inc", amount=Decimal("100.00"), currency_id=eur.id
        ))
        # Two conversions FROM USD TO EUR
        create_currency_conversion(db, CurrencyConversionCreate(
            from_currency_id=usd.id, to_currency_id=eur.id,
            from_amount=Decimal("500.00"), to_amount=Decimal("450.00"),
            conversion_date=date(2028, 6, 5), rate=Decimal("0.90")
        ), period.id)
        create_currency_conversion(db, CurrencyConversionCreate(
            from_currency_id=usd.id, to_currency_id=eur.id,
            from_amount=Decimal("300.00"), to_amount=Decimal("270.00"),
            conversion_date=date(2028, 6, 15), rate=Decimal("0.90")
        ), period.id)

        # EUR: 0 + 100 + 450 + 270 = 820
        # If -= mutation: 0 + 100 - 450 - 270 = -620
        upsert_snapshot(db, period.id, usd_acc.id, Decimal("1200.00"))  # 2000-500-300
        upsert_snapshot(db, period.id, eur_acc.id, Decimal("820.00"))

        result = calculate_reconciliation(db, test_user.id, period.id)
        eur_s = next(r for r in result.reconciliations if r.currency_ticker == "EUR3")

        # total_conversions_in must be 720 (450+270), expected_balance 820
        assert eur_s.total_conversions_in == Decimal("720.00")
        assert eur_s.is_balanced is True


class TestTaxBenefitsIntegration:
    """
    Integration tests for calculate_tax_benefits() using real DB.
    Kills mutants that mock-based tests cannot catch (WHERE clause mutations).

    Mutants targeted:
    - 110: CalculationPeriod.id != period_id   (wrong period filter)
    - 114: UserSettings.user_id != user_id     (wrong user filter)
    - 117: tax_system != "NONE" returns None   (inverted guard)
    - 124: IncomeEntry.calculation_period_id != period_id
    - 128: taxable_income = inc.amount         (overwrites instead of +=)
    - 130: ExpenseItem.calculation_period_id != period_id
    - 134: deductible_items = None             (breaks append)
    - 135: deductible_expenses = exp.amount    (overwrites instead of +=)
    - 142: estimated_tax = net_taxable / rate_fraction  (division instead of *)
    """

    def _make_user_with_tax_settings(self, db, tax_system="POLISH_B2B", tax_rate="19.00"):
        """Create a fresh user with a default currency and UserSettings."""
        import uuid
        from app.core.security import get_password_hash
        from app.models.user import User
        from app.models.currency import Currency
        from app.models.user_settings import UserSettings

        user = User(
            id=uuid.uuid4(),
            email=f"taxtest-{uuid.uuid4()}@example.com",
            password_hash=get_password_hash("testpw"),
            full_name="Tax Test User",
            is_active=True
        )
        db.add(user)
        db.flush()

        # UserSettings requires a valid default_currency_id
        default_cur = Currency(
            id=uuid.uuid4(), user_id=user.id,
            ticker=f"TC{str(uuid.uuid4())[:4].upper()}",
            name="Tax Default Currency", is_default=True
        )
        db.add(default_cur)
        db.flush()

        settings = UserSettings(
            user_id=user.id,
            default_currency_id=default_cur.id,
            tax_system=tax_system,
            tax_rate=Decimal(tax_rate),
        )
        db.add(settings)
        db.commit()
        db.refresh(user)
        return user

    def test_tax_benefits_only_counts_income_from_correct_period(
        self, db: Session
    ):
        """
        Income in a DIFFERENT period must NOT be summed into taxable_income.
        Kills mutant 124 (period_id != period_id filter).
        """
        from app.crud.period import create_period
        from app.crud.currency import create_currency
        from app.crud.income import create_income
        from app.schemas.period import PeriodCreate
        from app.schemas.currency import CurrencyCreate
        from app.schemas.income import IncomeCreate
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.income_entry import IncomeEntry

        user = self._make_user_with_tax_settings(db)
        cur = create_currency(db, user.id, CurrencyCreate(
            ticker="PLN", name="Polish Zloty", is_default=True
        ))

        p1 = create_period(db, user.id, PeriodCreate(
            period_name="TaxP1",
            start_date=date(2028, 7, 1), end_date=date(2028, 7, 31),
            snapshot_date=date(2028, 7, 31)
        ))
        p2 = create_period(db, user.id, PeriodCreate(
            period_name="TaxP2",
            start_date=date(2028, 8, 1), end_date=date(2028, 8, 31),
            snapshot_date=date(2028, 8, 31)
        ))

        # Income in P1 — should NOT be counted when calculating P2
        inc1 = IncomeEntry(
            calculation_period_id=p1.id,
            source_name="P1Income",
            amount=Decimal("99999.00"),
            currency_id=cur.id,
            tax_applicable=True
        )
        # Income in P2 — should be counted
        inc2 = IncomeEntry(
            calculation_period_id=p2.id,
            source_name="P2Income",
            amount=Decimal("5000.00"),
            currency_id=cur.id,
            tax_applicable=True
        )
        db.add_all([inc1, inc2])
        db.commit()

        result = calculate_tax_benefits(db=db, user_id=user.id, period_id=p2.id)

        assert result is not None
        # taxable_income must be 5000, NOT 99999+5000=104999
        assert result["taxable_income"] == Decimal("5000.00")
        # estimated_tax: 5000 * 0.19 = 950
        assert result["estimated_tax"] == Decimal("950.00")

    def test_tax_benefits_only_counts_expenses_from_correct_period(
        self, db: Session
    ):
        """
        Deductible expenses from a DIFFERENT period must NOT be summed.
        Kills mutant 130 (ExpenseItem period_id != period_id filter).
        """
        from app.crud.period import create_period
        from app.crud.currency import create_currency
        from app.crud.expense import create_expense
        from app.schemas.period import PeriodCreate
        from app.schemas.currency import CurrencyCreate
        from app.schemas.expense import ExpenseCreate
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.expense_item import ExpenseItem
        from app.models.expense_category import ExpenseCategory
        import uuid

        user = self._make_user_with_tax_settings(db)
        cur = create_currency(db, user.id, CurrencyCreate(
            ticker="PLN2", name="PLN2", is_default=True
        ))

        cat = ExpenseCategory(
            id=uuid.uuid4(), user_id=user.id,
            category_name="TaxCat", icon="💼", sort_order=1
        )
        db.add(cat)
        db.commit()

        p1 = create_period(db, user.id, PeriodCreate(
            period_name="TaxExpP1",
            start_date=date(2028, 9, 1), end_date=date(2028, 9, 30),
            snapshot_date=date(2028, 9, 30)
        ))
        p2 = create_period(db, user.id, PeriodCreate(
            period_name="TaxExpP2",
            start_date=date(2028, 10, 1), end_date=date(2028, 10, 31),
            snapshot_date=date(2028, 10, 31)
        ))

        # Deductible expense in P1 — must NOT count when calculating P2
        exp1 = ExpenseItem(
            calculation_period_id=p1.id,
            item_name="P1Deductible",
            amount=Decimal("99999.00"),
            currency_id=cur.id,
            category_id=cat.id,
            is_tax_deductible=True
        )
        # Deductible expense in P2 — should count
        exp2 = ExpenseItem(
            calculation_period_id=p2.id,
            item_name="P2Deductible",
            amount=Decimal("1000.00"),
            currency_id=cur.id,
            category_id=cat.id,
            is_tax_deductible=True
        )
        db.add_all([exp1, exp2])
        db.commit()

        result = calculate_tax_benefits(db=db, user_id=user.id, period_id=p2.id)

        assert result is not None
        # deductible_expenses must be 1000, NOT 99999+1000=100999
        assert result["deductible_expenses"] == Decimal("1000.00")

    def test_tax_benefits_multiple_incomes_summed(self, db: Session):
        """
        Multiple tax-applicable incomes must be SUMMED (kills mutant 128: = instead of +=).
        """
        from app.crud.period import create_period
        from app.crud.currency import create_currency
        from app.schemas.period import PeriodCreate
        from app.schemas.currency import CurrencyCreate
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.income_entry import IncomeEntry

        user = self._make_user_with_tax_settings(db, tax_rate="20.00")
        cur = create_currency(db, user.id, CurrencyCreate(
            ticker="PLN3", name="PLN3", is_default=True
        ))
        period = create_period(db, user.id, PeriodCreate(
            period_name="TaxMultiInc",
            start_date=date(2028, 11, 1), end_date=date(2028, 11, 30),
            snapshot_date=date(2028, 11, 30)
        ))
        for amt in [Decimal("3000.00"), Decimal("2000.00"), Decimal("1000.00")]:
            db.add(IncomeEntry(
                calculation_period_id=period.id,
                source_name=f"Inc{amt}", amount=amt,
                currency_id=cur.id, tax_applicable=True
            ))
        db.commit()

        result = calculate_tax_benefits(db=db, user_id=user.id, period_id=period.id)

        # taxable_income = 3000+2000+1000 = 6000 (not just 1000 from last item)
        assert result["taxable_income"] == Decimal("6000.00")
        assert result["estimated_tax"] == Decimal("1200.00")  # 6000 * 0.20

    def test_tax_benefits_multiple_deductibles_summed(self, db: Session):
        """
        Multiple deductible expenses must be SUMMED (kills mutant 135: = instead of +=).
        Also verifies deductible_items list is populated (kills mutant 134: = None).
        """
        from app.crud.period import create_period
        from app.crud.currency import create_currency
        from app.schemas.period import PeriodCreate
        from app.schemas.currency import CurrencyCreate
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.expense_item import ExpenseItem
        from app.models.expense_category import ExpenseCategory
        import uuid

        user = self._make_user_with_tax_settings(db, tax_rate="19.00")
        cur = create_currency(db, user.id, CurrencyCreate(
            ticker="PLN4", name="PLN4", is_default=True
        ))
        cat = ExpenseCategory(
            id=uuid.uuid4(), user_id=user.id,
            category_name="TaxCat2", icon="💼", sort_order=1
        )
        db.add(cat)
        period = create_period(db, user.id, PeriodCreate(
            period_name="TaxMultiDed",
            start_date=date(2028, 12, 1), end_date=date(2028, 12, 31),
            snapshot_date=date(2028, 12, 31)
        ))
        db.commit()
        for amt in [Decimal("500.00"), Decimal("700.00"), Decimal("300.00")]:
            db.add(ExpenseItem(
                calculation_period_id=period.id,
                item_name=f"Ded{amt}", amount=amt,
                currency_id=cur.id, category_id=cat.id,
                is_tax_deductible=True
            ))
        db.commit()

        result = calculate_tax_benefits(db=db, user_id=user.id, period_id=period.id)

        # deductible_expenses = 500+700+300 = 1500 (not just 300 from last item)
        assert result["deductible_expenses"] == Decimal("1500.00")
        # deductible_items list must have 3 entries (not crash if = None)
        assert len(result["deductible_items"]) == 3

    def test_tax_benefits_estimated_tax_uses_multiplication(self, db: Session):
        """
        estimated_tax = net_taxable * rate_fraction, NOT division.
        Kills mutant 142 (/ instead of *).
        """
        from app.crud.period import create_period
        from app.crud.currency import create_currency
        from app.schemas.period import PeriodCreate
        from app.schemas.currency import CurrencyCreate
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.income_entry import IncomeEntry

        user = self._make_user_with_tax_settings(db, tax_rate="10.00")
        cur = create_currency(db, user.id, CurrencyCreate(
            ticker="PLN5", name="PLN5", is_default=True
        ))
        period = create_period(db, user.id, PeriodCreate(
            period_name="TaxMultDiv",
            start_date=date(2029, 1, 1), end_date=date(2029, 1, 31),
            snapshot_date=date(2029, 1, 31)
        ))
        db.add(IncomeEntry(
            calculation_period_id=period.id,
            source_name="IncMulDiv", amount=Decimal("1000.00"),
            currency_id=cur.id, tax_applicable=True
        ))
        db.commit()

        result = calculate_tax_benefits(db=db, user_id=user.id, period_id=period.id)

        # rate = 10% → rate_fraction = 0.10
        # estimated_tax = 1000 * 0.10 = 100 (not 1000 / 0.10 = 10000)
        assert result["estimated_tax"] == Decimal("100.00")

    def test_tax_benefits_wrong_period_returns_none(self, db: Session):
        """
        Wrong period_id must return None (kills mutant 110: id != period_id).
        """
        from app.services.reconciliation_service import calculate_tax_benefits

        user = self._make_user_with_tax_settings(db)
        result = calculate_tax_benefits(db=db, user_id=user.id, period_id=uuid4())

        assert result is None

    def test_tax_benefits_wrong_user_settings_not_found(self, db: Session):
        """
        When user settings belong to another user (kills mutant 114: != on user_id filter).
        The query returns None settings → function returns None.
        """
        from app.crud.period import create_period
        from app.crud.currency import create_currency
        from app.schemas.period import PeriodCreate
        from app.schemas.currency import CurrencyCreate
        from app.services.reconciliation_service import calculate_tax_benefits

        # User with NO settings
        import uuid
        from app.core.security import get_password_hash
        from app.models.user import User

        user_no_settings = User(
            id=uuid.uuid4(),
            email=f"nosettings-{uuid.uuid4()}@example.com",
            password_hash=get_password_hash("testpw"),
            full_name="No Settings User",
            is_active=True
        )
        db.add(user_no_settings)
        db.commit()

        cur = create_currency(db, user_no_settings.id, CurrencyCreate(
            ticker="PLN6", name="PLN6", is_default=True
        ))
        period = create_period(db, user_no_settings.id, PeriodCreate(
            period_name="TaxNoSettings",
            start_date=date(2029, 2, 1), end_date=date(2029, 2, 28),
            snapshot_date=date(2029, 2, 28)
        ))

        # No UserSettings row → should return None
        result = calculate_tax_benefits(db=db, user_id=user_no_settings.id, period_id=period.id)
        assert result is None

    def test_tax_system_none_returns_none_not_b2b(self, db: Session):
        """
        When tax_system == "NONE", function must return None.
        Kills mutant 117 (inverts the condition so "NONE" goes through and "POLISH_B2B" returns None).
        """
        from app.crud.period import create_period
        from app.crud.currency import create_currency
        from app.schemas.period import PeriodCreate
        from app.schemas.currency import CurrencyCreate
        from app.services.reconciliation_service import calculate_tax_benefits

        user_none = self._make_user_with_tax_settings(db, tax_system="NONE", tax_rate="0.00")
        cur = create_currency(db, user_none.id, CurrencyCreate(
            ticker="PLN7", name="PLN7", is_default=True
        ))
        period_none = create_period(db, user_none.id, PeriodCreate(
            period_name="TaxNone",
            start_date=date(2029, 3, 1), end_date=date(2029, 3, 31),
            snapshot_date=date(2029, 3, 31)
        ))

        user_b2b = self._make_user_with_tax_settings(db, tax_system="POLISH_B2B", tax_rate="19.00")
        cur_b2b = create_currency(db, user_b2b.id, CurrencyCreate(
            ticker="PLN8", name="PLN8", is_default=True
        ))
        period_b2b = create_period(db, user_b2b.id, PeriodCreate(
            period_name="TaxB2B",
            start_date=date(2029, 3, 1), end_date=date(2029, 3, 31),
            snapshot_date=date(2029, 3, 31)
        ))

        # NONE user → must return None
        result_none = calculate_tax_benefits(db=db, user_id=user_none.id, period_id=period_none.id)
        assert result_none is None

        # POLISH_B2B user → must return a dict (not None)
        result_b2b = calculate_tax_benefits(db=db, user_id=user_b2b.id, period_id=period_b2b.id)
        assert result_b2b is not None
        assert result_b2b["tax_system"] == "POLISH_B2B"
