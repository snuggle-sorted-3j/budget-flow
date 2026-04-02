"""
Unit test fixtures.

These fixtures provide lightweight test data that does NOT require a database
connection. They are available to all tests under tests/unit/.

For fixtures that need a live database (db, client, auth_headers, test_user,
test_currency, test_category), see the root conftest at tests/conftest.py.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest


@pytest.fixture
def sample_uuid():
    """A stable UUID for deterministic tests."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_uuid2():
    """A second stable UUID."""
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def valid_period_data():
    """Minimal valid data for PeriodCreate."""
    return {
        "period_name": "Test Period",
        "start_date": date(2027, 1, 1),
        "end_date": date(2027, 1, 31),
        "snapshot_date": date(2027, 1, 31),
    }


@pytest.fixture
def valid_income_data(sample_uuid):
    """Minimal valid data for IncomeCreate."""
    return {
        "source_name": "Salary",
        "amount": Decimal("5000.00"),
        "currency_id": sample_uuid,
    }


@pytest.fixture
def valid_expense_data(sample_uuid, sample_uuid2):
    """Minimal valid data for ExpenseCreate."""
    return {
        "item_name": "Rent",
        "amount": Decimal("1500.00"),
        "category_id": sample_uuid,
        "currency_id": sample_uuid2,
    }
