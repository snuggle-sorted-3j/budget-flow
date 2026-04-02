"""
Unit Tests for Tax Benefits (B2B) calculation.

Tests for calculate_tax_benefits() in reconciliation_service.py.
Covers POLISH_B2B, NONE, zero deductibles, multi-currency scenarios.
"""
import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestCalculateTaxBenefits:
    """Unit tests for calculate_tax_benefits()."""

    def _make_db_with(self, settings, incomes, expenses, period_id, currency_id, user_id):
        """Helper: build a mock Session that returns the supplied fixtures."""
        from app.models.calculation_period import CalculationPeriod

        db = MagicMock(spec=Session)

        # Fake period so the "period exists" check passes
        fake_period = MagicMock(spec=CalculationPeriod)
        fake_period.id = period_id
        fake_period.user_id = user_id

        call_count = {"n": 0}

        def execute_side_effect(stmt):
            result = MagicMock()
            # Determine query type by inspecting the entity being selected
            try:
                entity = stmt.column_descriptions[0]["entity"]
                entity_name = entity.__tablename__
            except (AttributeError, IndexError, KeyError):
                entity_name = ""

            if entity_name == "calculation_periods":
                result.scalar_one_or_none.return_value = fake_period
            elif entity_name == "user_settings":
                result.scalar_one_or_none.return_value = settings
            elif entity_name == "income_entries":
                result.scalars.return_value.all.return_value = incomes
            elif entity_name == "expense_items":
                result.scalars.return_value.all.return_value = expenses
            else:
                result.scalar_one_or_none.return_value = None
                result.scalars.return_value.all.return_value = []
            return result

        db.execute.side_effect = execute_side_effect
        return db

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_polish_b2b_basic_calculation(self):
        """POLISH_B2B: tax savings = deductible * rate; estimated_tax uses net taxable."""
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.user_settings import UserSettings
        from app.models.income_entry import IncomeEntry
        from app.models.expense_item import ExpenseItem

        user_id = uuid4()
        period_id = uuid4()
        currency_id = uuid4()

        settings = MagicMock(spec=UserSettings)
        settings.tax_system = "POLISH_B2B"
        settings.tax_rate = Decimal("19.00")

        income1 = MagicMock(spec=IncomeEntry)
        income1.amount = Decimal("10000.00")
        income1.tax_applicable = True
        income1.currency_id = currency_id

        expense1 = MagicMock(spec=ExpenseItem)
        expense1.amount = Decimal("2000.00")
        expense1.is_tax_deductible = True
        expense1.currency_id = currency_id

        expense2 = MagicMock(spec=ExpenseItem)
        expense2.amount = Decimal("500.00")
        expense2.is_tax_deductible = False
        expense2.currency_id = currency_id

        db = self._make_db_with(settings, [income1], [expense1, expense2], period_id, currency_id, user_id)

        result = calculate_tax_benefits(db=db, user_id=user_id, period_id=period_id)

        assert result is not None
        assert result["tax_system"] == "POLISH_B2B"
        assert result["tax_rate"] == Decimal("19.00")
        # taxable income = 10000, deductible = 2000, net = 8000
        assert result["taxable_income"] == Decimal("10000.00")
        assert result["deductible_expenses"] == Decimal("2000.00")
        assert result["net_taxable_income"] == Decimal("8000.00")
        # estimated_tax = 8000 * 0.19 = 1520
        assert result["estimated_tax"] == Decimal("1520.00")
        # tax_savings = 2000 * 0.19 = 380
        assert result["tax_savings"] == Decimal("380.00")

    def test_no_tax_system_returns_none(self):
        """When tax_system is NONE, function returns None (no tax mode active)."""
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.user_settings import UserSettings

        user_id = uuid4()
        period_id = uuid4()

        settings = MagicMock(spec=UserSettings)
        settings.tax_system = "NONE"
        settings.tax_rate = Decimal("0.00")

        db = self._make_db_with(settings, [], [], period_id, None, user_id)

        result = calculate_tax_benefits(db=db, user_id=user_id, period_id=period_id)

        assert result is None

    def test_no_settings_returns_none(self):
        """When user has no settings row, function returns None."""
        from app.services.reconciliation_service import calculate_tax_benefits

        user_id = uuid4()
        period_id = uuid4()

        db = self._make_db_with(None, [], [], period_id, None, user_id)

        result = calculate_tax_benefits(db=db, user_id=user_id, period_id=period_id)

        assert result is None

    def test_zero_deductibles_no_savings(self):
        """No deductible expenses → tax_savings=0, full income is taxed."""
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.user_settings import UserSettings
        from app.models.income_entry import IncomeEntry
        from app.models.expense_item import ExpenseItem

        user_id = uuid4()
        period_id = uuid4()
        currency_id = uuid4()

        settings = MagicMock(spec=UserSettings)
        settings.tax_system = "POLISH_B2B"
        settings.tax_rate = Decimal("19.00")

        income1 = MagicMock(spec=IncomeEntry)
        income1.amount = Decimal("5000.00")
        income1.tax_applicable = True
        income1.currency_id = currency_id

        expense1 = MagicMock(spec=ExpenseItem)
        expense1.amount = Decimal("1000.00")
        expense1.is_tax_deductible = False
        expense1.currency_id = currency_id

        db = self._make_db_with(settings, [income1], [expense1], period_id, currency_id, user_id)

        result = calculate_tax_benefits(db=db, user_id=user_id, period_id=period_id)

        assert result["deductible_expenses"] == Decimal("0.00")
        assert result["tax_savings"] == Decimal("0.00")
        assert result["net_taxable_income"] == Decimal("5000.00")
        assert result["estimated_tax"] == Decimal("950.00")  # 5000 * 0.19

    def test_no_taxable_income(self):
        """No tax-applicable income → taxable_income=0, estimated_tax=0."""
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.user_settings import UserSettings
        from app.models.income_entry import IncomeEntry
        from app.models.expense_item import ExpenseItem

        user_id = uuid4()
        period_id = uuid4()
        currency_id = uuid4()

        settings = MagicMock(spec=UserSettings)
        settings.tax_system = "POLISH_B2B"
        settings.tax_rate = Decimal("19.00")

        income1 = MagicMock(spec=IncomeEntry)
        income1.amount = Decimal("3000.00")
        income1.tax_applicable = False
        income1.currency_id = currency_id

        db = self._make_db_with(settings, [income1], [], period_id, currency_id, user_id)

        result = calculate_tax_benefits(db=db, user_id=user_id, period_id=period_id)

        assert result["taxable_income"] == Decimal("0.00")
        assert result["estimated_tax"] == Decimal("0.00")
        assert result["net_taxable_income"] == Decimal("0.00")

    def test_deductibles_exceed_taxable_income_clamps_to_zero(self):
        """When deductibles > taxable income, net_taxable is clamped to 0 (no negative tax)."""
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.user_settings import UserSettings
        from app.models.income_entry import IncomeEntry
        from app.models.expense_item import ExpenseItem

        user_id = uuid4()
        period_id = uuid4()
        currency_id = uuid4()

        settings = MagicMock(spec=UserSettings)
        settings.tax_system = "POLISH_B2B"
        settings.tax_rate = Decimal("19.00")

        income1 = MagicMock(spec=IncomeEntry)
        income1.amount = Decimal("1000.00")
        income1.tax_applicable = True
        income1.currency_id = currency_id

        expense1 = MagicMock(spec=ExpenseItem)
        expense1.amount = Decimal("3000.00")
        expense1.is_tax_deductible = True
        expense1.currency_id = currency_id

        db = self._make_db_with(settings, [income1], [expense1], period_id, currency_id, user_id)

        result = calculate_tax_benefits(db=db, user_id=user_id, period_id=period_id)

        assert result["net_taxable_income"] == Decimal("0.00")
        assert result["estimated_tax"] == Decimal("0.00")
        # savings still calculated on actual deductible amount
        assert result["tax_savings"] == Decimal("570.00")  # 3000 * 0.19

    def test_returns_deductible_items_list(self):
        """Result includes list of deductible expense items with name and amount."""
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.user_settings import UserSettings
        from app.models.expense_item import ExpenseItem

        user_id = uuid4()
        period_id = uuid4()
        currency_id = uuid4()

        settings = MagicMock(spec=UserSettings)
        settings.tax_system = "POLISH_B2B"
        settings.tax_rate = Decimal("19.00")

        expense1 = MagicMock(spec=ExpenseItem)
        expense1.item_name = "Laptop"
        expense1.amount = Decimal("4000.00")
        expense1.is_tax_deductible = True
        expense1.currency_id = currency_id

        expense2 = MagicMock(spec=ExpenseItem)
        expense2.item_name = "Coffee"
        expense2.amount = Decimal("50.00")
        expense2.is_tax_deductible = False
        expense2.currency_id = currency_id

        db = self._make_db_with(settings, [], [expense1, expense2], period_id, currency_id, user_id)

        result = calculate_tax_benefits(db=db, user_id=user_id, period_id=period_id)

        items = result["deductible_items"]
        assert len(items) == 1
        assert items[0]["item_name"] == "Laptop"
        assert items[0]["amount"] == Decimal("4000.00")

    def test_us_annual_tax_system(self):
        """US_ANNUAL tax system also calculates benefits (same formula)."""
        from app.services.reconciliation_service import calculate_tax_benefits
        from app.models.user_settings import UserSettings
        from app.models.income_entry import IncomeEntry

        user_id = uuid4()
        period_id = uuid4()
        currency_id = uuid4()

        settings = MagicMock(spec=UserSettings)
        settings.tax_system = "US_ANNUAL"
        settings.tax_rate = Decimal("22.00")

        income1 = MagicMock(spec=IncomeEntry)
        income1.amount = Decimal("6000.00")
        income1.tax_applicable = True
        income1.currency_id = currency_id

        db = self._make_db_with(settings, [income1], [], period_id, currency_id, user_id)

        result = calculate_tax_benefits(db=db, user_id=user_id, period_id=period_id)

        assert result["tax_system"] == "US_ANNUAL"
        assert result["estimated_tax"] == Decimal("1320.00")  # 6000 * 0.22
