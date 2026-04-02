"""
Unit Tests for Pydantic Schema Validation

Tests verify that schemas correctly reject invalid input at the boundary.
Each test is designed so that removing the corresponding validator or
constraint from the schema would cause the test to fail.

No database required — these are pure Pydantic validation tests.
"""

import pytest
import uuid

pytestmark = [pytest.mark.unit, pytest.mark.schema]
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from app.schemas.period import PeriodCreate
from app.schemas.income import IncomeCreate
from app.schemas.expense import ExpenseCreate
from app.schemas.installment import InstallmentItemCreate, InstallmentPaymentCreate
from app.schemas.currency_conversion import CurrencyConversionCreate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_UUID = uuid.uuid4()
_UUID2 = uuid.uuid4()


# ===========================================================================
# PeriodCreate
# ===========================================================================

class TestPeriodCreateSchema:

    def test_valid_period(self):
        p = PeriodCreate(
            period_name="January 2027",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 1, 31),
            snapshot_date=date(2027, 1, 31),
        )
        assert p.period_name == "January 2027"

    def test_end_date_before_start_date_rejected(self):
        """end_date must be >= start_date."""
        with pytest.raises(ValidationError, match="end_date|date"):
            PeriodCreate(
                period_name="Bad Dates",
                start_date=date(2027, 2, 1),
                end_date=date(2027, 1, 1),
                snapshot_date=date(2027, 1, 1),
            )

    def test_snapshot_date_must_equal_end_date(self):
        """snapshot_date must equal end_date."""
        with pytest.raises(ValidationError, match="snapshot|end"):
            PeriodCreate(
                period_name="Bad Snapshot",
                start_date=date(2027, 1, 1),
                end_date=date(2027, 1, 31),
                snapshot_date=date(2027, 1, 15),
            )

    def test_missing_period_name_rejected(self):
        with pytest.raises(ValidationError, match="period_name"):
            PeriodCreate(
                start_date=date(2027, 1, 1),
                end_date=date(2027, 1, 31),
                snapshot_date=date(2027, 1, 31),
            )

    def test_period_name_max_length(self):
        """Names longer than 255 chars should be rejected."""
        with pytest.raises(ValidationError, match="period_name|max"):
            PeriodCreate(
                period_name="X" * 256,
                start_date=date(2027, 1, 1),
                end_date=date(2027, 1, 31),
                snapshot_date=date(2027, 1, 31),
            )

    def test_invalid_date_type_rejected(self):
        """Passing a non-date type should fail."""
        with pytest.raises(ValidationError):
            PeriodCreate(
                period_name="Type Error",
                start_date="not-a-date",
                end_date=date(2027, 1, 31),
                snapshot_date=date(2027, 1, 31),
            )


# ===========================================================================
# IncomeCreate
# ===========================================================================

class TestIncomeCreateSchema:

    def test_valid_income(self):
        i = IncomeCreate(
            source_name="Salary",
            amount=Decimal("5000.00"),
            currency_id=_UUID,
        )
        assert i.amount == Decimal("5000.00")

    def test_negative_amount_rejected(self):
        """amount must be >= 0."""
        with pytest.raises(ValidationError, match="amount"):
            IncomeCreate(
                source_name="Bad Income",
                amount=Decimal("-100.00"),
                currency_id=_UUID,
            )

    def test_zero_amount_accepted(self):
        """ge=0 means zero is valid."""
        i = IncomeCreate(
            source_name="Zero Income",
            amount=Decimal("0"),
            currency_id=_UUID,
        )
        assert i.amount == Decimal("0")

    def test_missing_source_name_rejected(self):
        with pytest.raises(ValidationError, match="source_name"):
            IncomeCreate(amount=Decimal("100"), currency_id=_UUID)

    def test_missing_currency_id_rejected(self):
        with pytest.raises(ValidationError, match="currency_id"):
            IncomeCreate(source_name="Test", amount=Decimal("100"))

    def test_source_name_max_length(self):
        with pytest.raises(ValidationError, match="source_name|max"):
            IncomeCreate(
                source_name="X" * 256,
                amount=Decimal("100"),
                currency_id=_UUID,
            )

    def test_invalid_currency_id_type_rejected(self):
        with pytest.raises(ValidationError):
            IncomeCreate(
                source_name="Test",
                amount=Decimal("100"),
                currency_id="not-a-uuid",
            )


# ===========================================================================
# ExpenseCreate
# ===========================================================================

class TestExpenseCreateSchema:

    def test_valid_expense(self):
        e = ExpenseCreate(
            item_name="Rent",
            amount=Decimal("1500.00"),
            category_id=_UUID,
            currency_id=_UUID2,
        )
        assert e.item_name == "Rent"

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError, match="amount"):
            ExpenseCreate(
                item_name="Bad",
                amount=Decimal("-50"),
                category_id=_UUID,
                currency_id=_UUID2,
            )

    def test_missing_category_id_rejected(self):
        with pytest.raises(ValidationError, match="category_id"):
            ExpenseCreate(
                item_name="No Category",
                amount=Decimal("100"),
                currency_id=_UUID2,
            )

    def test_missing_item_name_rejected(self):
        with pytest.raises(ValidationError, match="item_name"):
            ExpenseCreate(
                amount=Decimal("100"),
                category_id=_UUID,
                currency_id=_UUID2,
            )

    def test_item_name_max_length(self):
        with pytest.raises(ValidationError, match="item_name|max"):
            ExpenseCreate(
                item_name="X" * 256,
                amount=Decimal("100"),
                category_id=_UUID,
                currency_id=_UUID2,
            )

    def test_tax_category_max_length(self):
        """tax_category has max_length=100."""
        with pytest.raises(ValidationError, match="tax_category|max"):
            ExpenseCreate(
                item_name="Tax Test",
                amount=Decimal("100"),
                category_id=_UUID,
                currency_id=_UUID2,
                tax_category="X" * 101,
            )


# ===========================================================================
# InstallmentItemCreate
# ===========================================================================

class TestInstallmentItemCreateSchema:

    def test_valid_installment(self):
        i = InstallmentItemCreate(
            item_name="Laptop",
            total_price=Decimal("1200.00"),
            currency_id=_UUID,
            initial_period_id=_UUID2,
        )
        assert i.total_price == Decimal("1200.00")

    def test_zero_total_price_rejected(self):
        """total_price uses gt=0, so zero is invalid."""
        with pytest.raises(ValidationError, match="total_price"):
            InstallmentItemCreate(
                item_name="Free Item",
                total_price=Decimal("0"),
                currency_id=_UUID,
                initial_period_id=_UUID2,
            )

    def test_negative_total_price_rejected(self):
        with pytest.raises(ValidationError, match="total_price"):
            InstallmentItemCreate(
                item_name="Negative",
                total_price=Decimal("-500"),
                currency_id=_UUID,
                initial_period_id=_UUID2,
            )

    def test_zero_monthly_payment_rejected(self):
        """monthly_payment_amount uses gt=0."""
        with pytest.raises(ValidationError, match="monthly_payment"):
            InstallmentItemCreate(
                item_name="Zero Monthly",
                total_price=Decimal("1000"),
                currency_id=_UUID,
                initial_period_id=_UUID2,
                monthly_payment_amount=Decimal("0"),
            )

    def test_zero_months_to_pay_rejected(self):
        """months_to_pay uses gt=0."""
        with pytest.raises(ValidationError, match="months_to_pay"):
            InstallmentItemCreate(
                item_name="Zero Months",
                total_price=Decimal("1000"),
                currency_id=_UUID,
                initial_period_id=_UUID2,
                months_to_pay=0,
            )

    def test_negative_months_to_pay_rejected(self):
        with pytest.raises(ValidationError, match="months_to_pay"):
            InstallmentItemCreate(
                item_name="Negative Months",
                total_price=Decimal("1000"),
                currency_id=_UUID,
                initial_period_id=_UUID2,
                months_to_pay=-3,
            )


# ===========================================================================
# InstallmentPaymentCreate
# ===========================================================================

class TestInstallmentPaymentCreateSchema:

    def test_valid_payment(self):
        p = InstallmentPaymentCreate(
            payment_amount=Decimal("200.00"),
            payment_date=date(2027, 3, 15),
        )
        assert p.payment_amount == Decimal("200.00")

    def test_zero_payment_rejected(self):
        """payment_amount uses gt=0."""
        with pytest.raises(ValidationError, match="payment_amount"):
            InstallmentPaymentCreate(
                payment_amount=Decimal("0"),
                payment_date=date(2027, 3, 15),
            )

    def test_negative_payment_rejected(self):
        with pytest.raises(ValidationError, match="payment_amount"):
            InstallmentPaymentCreate(
                payment_amount=Decimal("-100"),
                payment_date=date(2027, 3, 15),
            )

    def test_missing_payment_date_rejected(self):
        with pytest.raises(ValidationError, match="payment_date"):
            InstallmentPaymentCreate(payment_amount=Decimal("100"))


# ===========================================================================
# CurrencyConversionCreate
# ===========================================================================

class TestCurrencyConversionCreateSchema:

    def test_valid_conversion(self):
        c = CurrencyConversionCreate(
            from_currency_id=_UUID,
            to_currency_id=_UUID2,
            from_amount=Decimal("100.00"),
            to_amount=Decimal("85.00"),
            rate=Decimal("0.85"),
            conversion_date=date(2027, 3, 15),
        )
        assert c.rate == Decimal("0.85")

    def test_zero_from_amount_rejected(self):
        """from_amount uses gt=0."""
        with pytest.raises(ValidationError, match="from_amount"):
            CurrencyConversionCreate(
                from_currency_id=_UUID,
                to_currency_id=_UUID2,
                from_amount=Decimal("0"),
                to_amount=Decimal("85"),
                rate=Decimal("0.85"),
                conversion_date=date(2027, 3, 15),
            )

    def test_negative_to_amount_rejected(self):
        with pytest.raises(ValidationError, match="to_amount"):
            CurrencyConversionCreate(
                from_currency_id=_UUID,
                to_currency_id=_UUID2,
                from_amount=Decimal("100"),
                to_amount=Decimal("-85"),
                rate=Decimal("0.85"),
                conversion_date=date(2027, 3, 15),
            )

    def test_zero_rate_rejected(self):
        with pytest.raises(ValidationError, match="rate"):
            CurrencyConversionCreate(
                from_currency_id=_UUID,
                to_currency_id=_UUID2,
                from_amount=Decimal("100"),
                to_amount=Decimal("85"),
                rate=Decimal("0"),
                conversion_date=date(2027, 3, 15),
            )

    def test_missing_conversion_date_rejected(self):
        with pytest.raises(ValidationError, match="conversion_date"):
            CurrencyConversionCreate(
                from_currency_id=_UUID,
                to_currency_id=_UUID2,
                from_amount=Decimal("100"),
                to_amount=Decimal("85"),
                rate=Decimal("0.85"),
            )

    def test_missing_from_currency_rejected(self):
        with pytest.raises(ValidationError, match="from_currency_id"):
            CurrencyConversionCreate(
                to_currency_id=_UUID2,
                from_amount=Decimal("100"),
                to_amount=Decimal("85"),
                rate=Decimal("0.85"),
                conversion_date=date(2027, 3, 15),
            )
