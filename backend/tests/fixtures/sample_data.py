"""
Sample data constants for BudgetFlow tests.

Provides pre-defined test data sets for common scenarios.
"""
from decimal import Decimal


# Common currencies used in tests
SAMPLE_CURRENCIES = [
    {"ticker": "USD", "name": "US Dollar", "is_default": True},
    {"ticker": "EUR", "name": "Euro", "is_default": False},
    {"ticker": "PLN", "name": "Polish Zloty", "is_default": False},
    {"ticker": "GBP", "name": "British Pound", "is_default": False},
]

# Default expense categories (matching system categories)
SAMPLE_CATEGORIES = [
    {"category_name": "Food & Dining", "icon": "🍕", "description": "Restaurants, groceries, coffee"},
    {"category_name": "Transportation", "icon": "🚗", "description": "Gas, public transit, uber"},
    {"category_name": "Housing", "icon": "🏠", "description": "Rent, mortgage, utilities"},
    {"category_name": "Entertainment", "icon": "🎬", "description": "Movies, games, subscriptions"},
    {"category_name": "Shopping", "icon": "🛒", "description": "Clothing, electronics, household"},
    {"category_name": "Healthcare", "icon": "💊", "description": "Doctor, pharmacy, insurance"},
    {"category_name": "Untracked Expenses", "icon": "❓", "description": "Reconciliation adjustments"},
]

# Account types available in the system
ACCOUNT_TYPES = ["BANK", "CASH", "CREDIT_CARD", "SAVINGS", "OTHER"]

# Investment account types
INVESTMENT_ACCOUNT_TYPES = ["BROKERAGE", "RETIREMENT", "CRYPTO", "OTHER"]

# Suspended expense transaction types
SUSPENDED_TRANSACTION_TYPES = ["LOAN_GIVEN", "LOAN_RECEIVED", "RETURN_PENDING", "DEPOSIT"]

# Period statuses
PERIOD_STATUSES = ["DRAFT", "FINALIZED"]

# Installment statuses
INSTALLMENT_STATUSES = ["ACTIVE", "PAID_OFF"]


# Reconciliation test scenarios
class ReconciliationScenarios:
    """Pre-defined reconciliation test scenarios."""
    
    # Scenario 1: Basic balanced period
    BALANCED_BASIC = {
        "starting_balance": Decimal("0.00"),
        "incomes": [Decimal("1000.00")],
        "expenses": [Decimal("200.00")],
        "snapshot_balance": Decimal("800.00"),
        "expected_balanced": True,
        "expected_difference": Decimal("0.00"),
    }
    
    # Scenario 2: Unbalanced (snapshot mismatch)
    UNBALANCED_SNAPSHOT = {
        "starting_balance": Decimal("0.00"),
        "incomes": [Decimal("1000.00")],
        "expenses": [Decimal("200.00")],
        "snapshot_balance": Decimal("500.00"),  # Should be 800
        "expected_balanced": False,
        "expected_difference": Decimal("300.00"),
    }
    
    # Scenario 3: With previous period carry-over
    WITH_PREVIOUS_PERIOD = {
        "previous_snapshot": Decimal("5000.00"),
        "incomes": [Decimal("2000.00")],
        "expenses": [Decimal("500.00")],
        "snapshot_balance": Decimal("6500.00"),
        "expected_balanced": True,
        "expected_starting": Decimal("5000.00"),
    }
    
    # Scenario 4: With investment transfer
    WITH_INVESTMENT = {
        "starting_balance": Decimal("1000.00"),
        "incomes": [Decimal("3000.00")],
        "expenses": [Decimal("500.00")],
        "investment_transfers": [Decimal("1000.00")],
        "snapshot_balance": Decimal("2500.00"),
        "expected_balanced": True,
    }
    
    # Scenario 5: With installment payment
    WITH_INSTALLMENT = {
        "starting_balance": Decimal("1000.00"),
        "incomes": [Decimal("2000.00")],
        "expenses": [Decimal("300.00")],
        "installment_payments": [Decimal("200.00")],
        "snapshot_balance": Decimal("2500.00"),
        "expected_balanced": True,
    }
    
    # Scenario 6: With suspended expense (loan given)
    WITH_SUSPENDED_OUT = {
        "starting_balance": Decimal("1000.00"),
        "incomes": [Decimal("1500.00")],
        "expenses": [Decimal("200.00")],
        "suspended_out": [Decimal("300.00")],  # Loan given
        "snapshot_balance": Decimal("2000.00"),
        "expected_balanced": True,
    }
    
    # Scenario 7: With suspended expense settled (loan repaid)
    WITH_SUSPENDED_IN = {
        "starting_balance": Decimal("1000.00"),
        "incomes": [Decimal("500.00")],
        "expenses": [Decimal("100.00")],
        "suspended_in": [Decimal("300.00")],  # Loan repaid to us
        "snapshot_balance": Decimal("1700.00"),
        "expected_balanced": True,
    }
    
    # Scenario 8: Currency conversion (USD to EUR)
    WITH_CURRENCY_CONVERSION = {
        "currencies": ["USD", "EUR"],
        "usd_starting": Decimal("1000.00"),
        "eur_starting": Decimal("500.00"),
        "conversion_from_usd": Decimal("200.00"),
        "conversion_to_eur": Decimal("185.00"),
        "usd_snapshot": Decimal("800.00"),
        "eur_snapshot": Decimal("685.00"),
        "expected_balanced": True,
    }
    
    # Scenario 9: Complex multi-component
    COMPLEX_FULL = {
        "starting_balance": Decimal("10000.00"),
        "incomes": [
            Decimal("5000.00"),  # Salary
            Decimal("500.00"),   # Side income
        ],
        "expenses": [
            Decimal("1500.00"),  # Rent
            Decimal("400.00"),   # Utilities
            Decimal("600.00"),   # Food
        ],
        "investment_transfers": [Decimal("1000.00")],
        "installment_payments": [Decimal("300.00")],
        "suspended_out": [Decimal("200.00")],
        "snapshot_balance": Decimal("11500.00"),
        # 10000 + 5500 - 2500 - 1000 - 300 - 200 = 11500
        "expected_balanced": True,
    }


# Test user credentials
class TestUsers:
    """Pre-defined test user data."""
    
    BASIC_USER = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "Password123!",
    }
    
    ADMIN_USER = {
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password": "AdminPass456!",
    }


# API response status codes
class ExpectedStatusCodes:
    """Expected HTTP status codes for API responses."""
    
    SUCCESS = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNPROCESSABLE = 422
    SERVER_ERROR = 500
