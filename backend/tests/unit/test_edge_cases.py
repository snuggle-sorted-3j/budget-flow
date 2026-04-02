"""
Unit Tests for Edge Cases & Boundary Values

Tests that valid-but-tricky input is handled correctly by schemas and
wouldn't silently corrupt data. These complement test_schemas.py which
tests rejection of invalid input — here we test acceptance of unusual
but legitimate input.

No database required.
"""

import pytest
import uuid

pytestmark = [pytest.mark.unit, pytest.mark.edge]
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from app.schemas.period import PeriodCreate
from app.schemas.income import IncomeCreate
from app.schemas.expense import ExpenseCreate
from app.schemas.installment import InstallmentItemCreate, InstallmentPaymentCreate
from app.schemas.currency_conversion import CurrencyConversionCreate


_UUID = uuid.uuid4()
_UUID2 = uuid.uuid4()


# ===========================================================================
# Unicode & International Characters
# ===========================================================================

class TestUnicodeHandling:
    """Financial apps serve international users — names must support
    non-ASCII characters without data corruption."""

    def test_period_name_with_japanese(self):
        p = PeriodCreate(
            period_name="2027年1月の予算",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 1, 31),
            snapshot_date=date(2027, 1, 31),
        )
        assert p.period_name == "2027年1月の予算"

    def test_income_source_with_arabic(self):
        i = IncomeCreate(
            source_name="راتب شهري",
            amount=Decimal("3000"),
            currency_id=_UUID,
        )
        assert i.source_name == "راتب شهري"

    def test_expense_name_with_emoji(self):
        e = ExpenseCreate(
            item_name="🏠 Rent Payment 🔑",
            amount=Decimal("1500"),
            category_id=_UUID,
            currency_id=_UUID2,
        )
        assert e.item_name == "🏠 Rent Payment 🔑"

    def test_expense_name_with_cyrillic(self):
        e = ExpenseCreate(
            item_name="Аренда квартиры",
            amount=Decimal("800"),
            category_id=_UUID,
            currency_id=_UUID2,
        )
        assert e.item_name == "Аренда квартиры"

    def test_installment_name_with_mixed_scripts(self):
        i = InstallmentItemCreate(
            item_name="MacBook Pro — 分割払い (12回)",
            total_price=Decimal("2499.99"),
            currency_id=_UUID,
            initial_period_id=_UUID2,
        )
        assert "分割払い" in i.item_name

    def test_notes_with_newlines_and_tabs(self):
        """Notes fields should accept multi-line text."""
        i = IncomeCreate(
            source_name="Salary",
            amount=Decimal("5000"),
            currency_id=_UUID,
            notes="Line 1\nLine 2\n\tIndented line",
        )
        assert "\n" in i.notes
        assert "\t" in i.notes


# ===========================================================================
# String Boundary Values
# ===========================================================================

class TestStringBoundaries:
    """Test string fields at their exact length limits."""

    def test_period_name_at_max_length(self):
        """Exactly 255 chars should be accepted."""
        name = "A" * 255
        p = PeriodCreate(
            period_name=name,
            start_date=date(2027, 1, 1),
            end_date=date(2027, 1, 31),
            snapshot_date=date(2027, 1, 31),
        )
        assert len(p.period_name) == 255

    def test_period_name_one_over_max_rejected(self):
        """256 chars should be rejected."""
        with pytest.raises(ValidationError):
            PeriodCreate(
                period_name="A" * 256,
                start_date=date(2027, 1, 1),
                end_date=date(2027, 1, 31),
                snapshot_date=date(2027, 1, 31),
            )

    def test_single_character_name(self):
        """Single-char names should be valid."""
        p = PeriodCreate(
            period_name="X",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 1, 31),
            snapshot_date=date(2027, 1, 31),
        )
        assert p.period_name == "X"

    def test_income_source_at_max_length(self):
        name = "B" * 255
        i = IncomeCreate(
            source_name=name,
            amount=Decimal("100"),
            currency_id=_UUID,
        )
        assert len(i.source_name) == 255

    def test_expense_tax_category_at_max_length(self):
        """tax_category has max_length=100."""
        e = ExpenseCreate(
            item_name="Test",
            amount=Decimal("100"),
            category_id=_UUID,
            currency_id=_UUID2,
            tax_category="T" * 100,
        )
        assert len(e.tax_category) == 100

    def test_expense_tax_category_one_over_rejected(self):
        with pytest.raises(ValidationError):
            ExpenseCreate(
                item_name="Test",
                amount=Decimal("100"),
                category_id=_UUID,
                currency_id=_UUID2,
                tax_category="T" * 101,
            )


# ===========================================================================
# Numeric Boundary Values
# ===========================================================================

class TestNumericBoundaries:
    """Test amount fields at interesting numeric boundaries."""

    def test_very_small_positive_amount(self):
        """Smallest practical amount (1 cent)."""
        i = IncomeCreate(
            source_name="Tiny",
            amount=Decimal("0.01"),
            currency_id=_UUID,
        )
        assert i.amount == Decimal("0.01")

    def test_very_large_amount(self):
        """Large amounts should not overflow or truncate."""
        i = IncomeCreate(
            source_name="Jackpot",
            amount=Decimal("99999999.99"),
            currency_id=_UUID,
        )
        assert i.amount == Decimal("99999999.99")

    def test_many_decimal_places_preserved(self):
        """Decimal precision should be maintained."""
        c = CurrencyConversionCreate(
            from_currency_id=_UUID,
            to_currency_id=_UUID2,
            from_amount=Decimal("100"),
            to_amount=Decimal("85.123456"),
            rate=Decimal("0.85123456"),
            conversion_date=date(2027, 3, 15),
        )
        assert c.rate == Decimal("0.85123456")

    def test_installment_total_price_one_cent(self):
        """Smallest valid installment (gt=0 so 0.01 is valid)."""
        i = InstallmentItemCreate(
            item_name="Penny Item",
            total_price=Decimal("0.01"),
            currency_id=_UUID,
            initial_period_id=_UUID2,
        )
        assert i.total_price == Decimal("0.01")

    def test_installment_months_to_pay_one(self):
        """Single month installment."""
        i = InstallmentItemCreate(
            item_name="One Month",
            total_price=Decimal("100"),
            currency_id=_UUID,
            initial_period_id=_UUID2,
            months_to_pay=1,
        )
        assert i.months_to_pay == 1

    def test_installment_months_to_pay_large(self):
        """Long-term installment (30 years = 360 months)."""
        i = InstallmentItemCreate(
            item_name="Mortgage",
            total_price=Decimal("500000"),
            currency_id=_UUID,
            initial_period_id=_UUID2,
            months_to_pay=360,
        )
        assert i.months_to_pay == 360

    def test_conversion_rate_less_than_one(self):
        """Rates below 1 are common (e.g. EUR/GBP)."""
        c = CurrencyConversionCreate(
            from_currency_id=_UUID,
            to_currency_id=_UUID2,
            from_amount=Decimal("100"),
            to_amount=Decimal("85"),
            rate=Decimal("0.85"),
            conversion_date=date(2027, 1, 1),
        )
        assert c.rate == Decimal("0.85")

    def test_conversion_rate_much_greater_than_one(self):
        """Rates >> 1 are common (e.g. USD/JPY ~150)."""
        c = CurrencyConversionCreate(
            from_currency_id=_UUID,
            to_currency_id=_UUID2,
            from_amount=Decimal("100"),
            to_amount=Decimal("15000"),
            rate=Decimal("150.00"),
            conversion_date=date(2027, 1, 1),
        )
        assert c.rate == Decimal("150.00")


# ===========================================================================
# Date Boundary Values
# ===========================================================================

class TestDateBoundaries:
    """Test date fields at edge values."""

    def test_single_day_period(self):
        """Period where start == end should be valid."""
        p = PeriodCreate(
            period_name="One Day",
            start_date=date(2027, 6, 15),
            end_date=date(2027, 6, 15),
            snapshot_date=date(2027, 6, 15),
        )
        assert p.start_date == p.end_date

    def test_leap_year_period(self):
        """Feb 29 on a leap year."""
        p = PeriodCreate(
            period_name="Leap February",
            start_date=date(2028, 2, 1),
            end_date=date(2028, 2, 29),
            snapshot_date=date(2028, 2, 29),
        )
        assert p.end_date.day == 29

    def test_year_long_period(self):
        """Full calendar year period."""
        p = PeriodCreate(
            period_name="Full Year",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 12, 31),
            snapshot_date=date(2027, 12, 31),
        )
        assert (p.end_date - p.start_date).days == 364

    def test_payment_date_far_past(self):
        """Historical dates should be accepted."""
        p = InstallmentPaymentCreate(
            payment_amount=Decimal("100"),
            payment_date=date(2020, 1, 1),
        )
        assert p.payment_date.year == 2020

    def test_payment_date_far_future(self):
        """Future dates should be accepted."""
        p = InstallmentPaymentCreate(
            payment_amount=Decimal("100"),
            payment_date=date(2050, 12, 31),
        )
        assert p.payment_date.year == 2050


# ===========================================================================
# Special Characters in Text Fields
# ===========================================================================

class TestSpecialCharacters:
    """Characters that could cause issues in rendering, CSV export, or queries."""

    SPECIAL_STRINGS = [
        'Item with "double quotes"',
        "Item with 'single quotes'",
        "Item with <angle brackets>",
        "Item with & ampersand",
        "Item, with, commas",
        "Item with\ttab",
        "Item with   multiple   spaces",
        "Item/with/slashes",
        "Item\\with\\backslashes",
        "Item with (parentheses) [brackets] {braces}",
        "Item with @#$%^*+=~`|",
        "100% off — best deal™ © 2027",
    ]

    @pytest.mark.parametrize("name", SPECIAL_STRINGS)
    def test_special_chars_in_income_source(self, name):
        i = IncomeCreate(
            source_name=name,
            amount=Decimal("100"),
            currency_id=_UUID,
        )
        assert i.source_name == name

    @pytest.mark.parametrize("name", SPECIAL_STRINGS)
    def test_special_chars_in_expense_name(self, name):
        e = ExpenseCreate(
            item_name=name,
            amount=Decimal("100"),
            category_id=_UUID,
            currency_id=_UUID2,
        )
        assert e.item_name == name
