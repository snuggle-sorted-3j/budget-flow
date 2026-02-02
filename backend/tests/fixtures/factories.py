"""
Test Data Factories for BudgetFlow

Provides factory functions to create test data dictionaries and model instances.
Use these factories to reduce duplication and maintain consistent test data.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID


class UserFactory:
    """Factory for creating user test data."""
    
    @staticmethod
    def create(
        email: Optional[str] = None,
        full_name: str = "Test User",
        password: str = "testpassword123",
        is_active: bool = True,
        **overrides: Any
    ) -> dict:
        """Create user registration payload."""
        return {
            "email": email or f"test-{uuid.uuid4().hex[:8]}@example.com",
            "full_name": full_name,
            "password": password,
            "is_active": is_active,
            **overrides
        }


class PeriodFactory:
    """Factory for creating period test data."""
    
    @staticmethod
    def create(
        name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        snapshot_date: Optional[date] = None,
        **overrides: Any
    ) -> dict:
        """Create period payload for API requests."""
        start = start_date or date(2026, 1, 1)
        end = end_date or date(2026, 1, 31)
        snapshot = snapshot_date or end
        
        return {
            "period_name": name or f"Test Period {uuid.uuid4().hex[:6]}",
            "start_date": str(start),
            "end_date": str(end),
            "snapshot_date": str(snapshot),
            **overrides
        }
    
    @staticmethod
    def create_sequence(count: int = 3, start_year: int = 2026) -> list[dict]:
        """Create a sequence of consecutive monthly periods."""
        periods = []
        for i in range(count):
            month = (i % 12) + 1
            year = start_year + (i // 12)
            
            # Calculate last day of month
            if month == 12:
                next_month_start = date(year + 1, 1, 1)
            else:
                next_month_start = date(year, month + 1, 1)
            last_day = next_month_start - timedelta(days=1)
            
            periods.append(PeriodFactory.create(
                name=f"{date(year, month, 1).strftime('%b %Y')}",
                start_date=date(year, month, 1),
                end_date=last_day,
                snapshot_date=last_day
            ))
        return periods


class CurrencyFactory:
    """Factory for creating currency test data."""
    
    @staticmethod
    def create(
        ticker: str = "USD",
        name: str = "US Dollar",
        is_default: bool = False,
        **overrides: Any
    ) -> dict:
        """Create currency payload."""
        return {
            "ticker": ticker,
            "name": name,
            "is_default": is_default,
            **overrides
        }
    
    @staticmethod
    def usd(is_default: bool = True) -> dict:
        """Convenience method for USD currency."""
        return CurrencyFactory.create("USD", "US Dollar", is_default)
    
    @staticmethod
    def eur(is_default: bool = False) -> dict:
        """Convenience method for EUR currency."""
        return CurrencyFactory.create("EUR", "Euro", is_default)
    
    @staticmethod
    def pln(is_default: bool = False) -> dict:
        """Convenience method for PLN currency."""
        return CurrencyFactory.create("PLN", "Polish Zloty", is_default)


class AccountFactory:
    """Factory for creating account test data."""
    
    @staticmethod
    def create(
        name: Optional[str] = None,
        account_type: str = "BANK",
        currency_id: Optional[UUID] = None,
        opening_balance: Decimal = Decimal("0.00"),
        **overrides: Any
    ) -> dict:
        """Create account payload."""
        return {
            "account_name": name or f"Test Account {uuid.uuid4().hex[:6]}",
            "account_type": account_type,
            "currency_id": str(currency_id) if currency_id else None,
            "opening_balance": float(opening_balance),
            **overrides
        }
    
    @staticmethod
    def bank(currency_id: UUID, name: str = "Bank Account", **kwargs: Any) -> dict:
        """Convenience method for bank account."""
        return AccountFactory.create(name=name, account_type="BANK", currency_id=currency_id, **kwargs)
    
    @staticmethod
    def cash(currency_id: UUID, name: str = "Cash", **kwargs: Any) -> dict:
        """Convenience method for cash account."""
        return AccountFactory.create(name=name, account_type="CASH", currency_id=currency_id, **kwargs)


class IncomeFactory:
    """Factory for creating income test data."""
    
    @staticmethod
    def create(
        source_name: str = "Test Income",
        amount: Decimal = Decimal("1000.00"),
        currency_id: Optional[UUID] = None,
        income_date: Optional[date] = None,
        tax_applicable: bool = False,
        notes: Optional[str] = None,
        **overrides: Any
    ) -> dict:
        """Create income entry payload."""
        return {
            "source_name": source_name,
            "amount": float(amount),
            "currency_id": str(currency_id) if currency_id else None,
            "income_date": str(income_date) if income_date else None,
            "tax_applicable": tax_applicable,
            "notes": notes,
            **overrides
        }
    
    @staticmethod
    def salary(currency_id: UUID, amount: Decimal = Decimal("5000.00"), **kwargs: Any) -> dict:
        """Convenience method for salary income."""
        return IncomeFactory.create(
            source_name="Salary",
            amount=amount,
            currency_id=currency_id,
            tax_applicable=True,
            **kwargs
        )


class ExpenseFactory:
    """Factory for creating expense test data."""
    
    @staticmethod
    def create(
        item_name: str = "Test Expense",
        amount: Decimal = Decimal("100.00"),
        currency_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        expense_date: Optional[date] = None,
        is_tax_deductible: bool = False,
        notes: Optional[str] = None,
        **overrides: Any
    ) -> dict:
        """Create expense entry payload."""
        return {
            "item_name": item_name,
            "amount": float(amount),
            "currency_id": str(currency_id) if currency_id else None,
            "category_id": str(category_id) if category_id else None,
            "expense_date": str(expense_date) if expense_date else None,
            "is_tax_deductible": is_tax_deductible,
            "notes": notes,
            **overrides
        }
    
    @staticmethod
    def rent(currency_id: UUID, category_id: UUID, amount: Decimal = Decimal("1500.00"), **kwargs: Any) -> dict:
        """Convenience method for rent expense."""
        return ExpenseFactory.create(
            item_name="Rent",
            amount=amount,
            currency_id=currency_id,
            category_id=category_id,
            **kwargs
        )


class SnapshotFactory:
    """Factory for creating balance snapshot test data."""
    
    @staticmethod
    def create(
        account_id: UUID,
        balance: Decimal = Decimal("0.00"),
        **overrides: Any
    ) -> dict:
        """Create snapshot payload."""
        return {
            "account_id": str(account_id),
            "balance": float(balance),
            **overrides
        }
    
    @staticmethod
    def bulk(accounts_balances: list[tuple[UUID, Decimal]]) -> list[dict]:
        """Create multiple snapshot payloads."""
        return [
            SnapshotFactory.create(account_id, balance)
            for account_id, balance in accounts_balances
        ]


class InstallmentFactory:
    """Factory for creating installment test data."""
    
    @staticmethod
    def create_item(
        item_name: str = "Test Installment",
        total_price: Decimal = Decimal("1200.00"),
        currency_id: Optional[UUID] = None,
        initial_period_id: Optional[UUID] = None,
        monthly_payment_amount: Optional[Decimal] = None,
        months_to_pay: int = 12,
        notes: Optional[str] = None,
        **overrides: Any
    ) -> dict:
        """Create installment item payload."""
        monthly = monthly_payment_amount or (total_price / months_to_pay)
        return {
            "item_name": item_name,
            "total_price": float(total_price),
            "currency_id": str(currency_id) if currency_id else None,
            "initial_period_id": str(initial_period_id) if initial_period_id else None,
            "monthly_payment_amount": float(monthly),
            "months_to_pay": months_to_pay,
            "notes": notes,
            **overrides
        }
    
    @staticmethod
    def create_payment(
        payment_amount: Decimal = Decimal("100.00"),
        payment_date: Optional[date] = None,
        notes: Optional[str] = None,
        **overrides: Any
    ) -> dict:
        """Create installment payment payload."""
        return {
            "payment_amount": float(payment_amount),
            "payment_date": str(payment_date) if payment_date else None,
            "notes": notes,
            **overrides
        }


class InvestmentFactory:
    """Factory for creating investment test data."""
    
    @staticmethod
    def create_account(
        account_name: str = "Test Investment Account",
        account_type: str = "BROKERAGE",
        notes: Optional[str] = None,
        **overrides: Any
    ) -> dict:
        """Create investment account payload."""
        return {
            "account_name": account_name,
            "account_type": account_type,
            "notes": notes,
            "is_active": True,
            **overrides
        }
    
    @staticmethod
    def create_investment(
        category_name: str = "Test Investment",
        investment_account_id: Optional[UUID] = None,
        opening_balance: Decimal = Decimal("0.00"),
        opening_balance_date: Optional[date] = None,
        opening_balance_currency_id: Optional[UUID] = None,
        **overrides: Any
    ) -> dict:
        """Create investment category payload."""
        return {
            "category_name": category_name,
            "investment_account_id": str(investment_account_id) if investment_account_id else None,
            "opening_balance": float(opening_balance),
            "opening_balance_date": str(opening_balance_date) if opening_balance_date else None,
            "opening_balance_currency_id": str(opening_balance_currency_id) if opening_balance_currency_id else None,
            **overrides
        }
    
    @staticmethod
    def create_transfer(
        investment_id: UUID,
        amount_transferred: Decimal = Decimal("500.00"),
        currency_id: Optional[UUID] = None,
        source_account_id: Optional[UUID] = None,
        transfer_date: Optional[date] = None,
        units_added: Optional[Decimal] = None,
        notes: Optional[str] = None,
        **overrides: Any
    ) -> dict:
        """Create investment transfer payload."""
        return {
            "investment_id": str(investment_id),
            "amount_transferred": float(amount_transferred),
            "currency_id": str(currency_id) if currency_id else None,
            "source_account_id": str(source_account_id) if source_account_id else None,
            "transfer_date": str(transfer_date) if transfer_date else None,
            "units_added": float(units_added) if units_added else None,
            "notes": notes,
            **overrides
        }


class SuspendedExpenseFactory:
    """Factory for creating suspended expense test data."""
    
    @staticmethod
    def create(
        item_name: str = "Test Suspended",
        amount: Decimal = Decimal("200.00"),
        currency_id: Optional[UUID] = None,
        transaction_type: str = "LOAN_GIVEN",
        notes: Optional[str] = None,
        **overrides: Any
    ) -> dict:
        """Create suspended expense payload."""
        return {
            "item_name": item_name,
            "amount": float(amount),
            "currency_id": str(currency_id) if currency_id else None,
            "transaction_type": transaction_type,
            "notes": notes,
            **overrides
        }
    
    @staticmethod
    def loan_given(currency_id: UUID, amount: Decimal, item_name: str = "Loan to Friend", **kwargs: Any) -> dict:
        """Convenience method for loan given."""
        return SuspendedExpenseFactory.create(
            item_name=item_name,
            amount=amount,
            currency_id=currency_id,
            transaction_type="LOAN_GIVEN",
            **kwargs
        )
    
    @staticmethod
    def loan_received(currency_id: UUID, amount: Decimal, item_name: str = "Loan from Friend", **kwargs: Any) -> dict:
        """Convenience method for loan received."""
        return SuspendedExpenseFactory.create(
            item_name=item_name,
            amount=amount,
            currency_id=currency_id,
            transaction_type="LOAN_RECEIVED",
            **kwargs
        )


class CurrencyConversionFactory:
    """Factory for creating currency conversion test data."""
    
    @staticmethod
    def create(
        from_currency_id: UUID,
        to_currency_id: UUID,
        from_amount: Decimal = Decimal("100.00"),
        to_amount: Decimal = Decimal("90.00"),
        conversion_date: Optional[date] = None,
        exchange_rate: Optional[Decimal] = None,
        notes: Optional[str] = None,
        **overrides: Any
    ) -> dict:
        """Create currency conversion payload."""
        rate = exchange_rate or (to_amount / from_amount)
        return {
            "from_currency_id": str(from_currency_id),
            "to_currency_id": str(to_currency_id),
            "from_amount": float(from_amount),
            "to_amount": float(to_amount),
            "conversion_date": str(conversion_date) if conversion_date else None,
            "exchange_rate": float(rate),
            "notes": notes,
            **overrides
        }


class CategoryFactory:
    """Factory for creating expense category test data."""
    
    @staticmethod
    def create(
        category_name: str = "Test Category",
        icon: str = "🧪",
        parent_category_id: Optional[UUID] = None,
        description: Optional[str] = None,
        **overrides: Any
    ) -> dict:
        """Create category payload."""
        return {
            "category_name": category_name,
            "icon": icon,
            "parent_category_id": str(parent_category_id) if parent_category_id else None,
            "description": description,
            **overrides
        }
