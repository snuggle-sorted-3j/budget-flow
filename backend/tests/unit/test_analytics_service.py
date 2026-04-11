"""
Unit/Integration Tests for analytics_service.py

Covers all 8 functions:
- get_spending_by_category
- get_income_vs_expenses_trend
- get_top_expenses
- get_net_worth_trend
- get_category_trends
- get_period_comparison
- detect_recurring_patterns
- detect_anomalies
"""
import uuid
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services import analytics_service
from app.models.calculation_period import CalculationPeriod
from app.models.currency import Currency
from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.expense_category import ExpenseCategory
from app.models.expense_item import ExpenseItem
from app.models.income_entry import IncomeEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_currency(db, user_id, ticker="USD", is_default=True):
    cur = Currency(
        id=uuid.uuid4(), user_id=user_id,
        ticker=ticker, name=ticker, is_default=is_default
    )
    db.add(cur)
    db.flush()
    return cur


def _make_category(db, user_id, name="General"):
    cat = ExpenseCategory(
        id=uuid.uuid4(), user_id=user_id,
        category_name=name, icon="📦", sort_order=1, is_active=True
    )
    db.add(cat)
    db.flush()
    return cat


def _make_period(db, user_id, name, start, end, snap, status="FINALIZED"):
    p = CalculationPeriod(
        id=uuid.uuid4(), user_id=user_id, period_name=name,
        start_date=start, end_date=end, snapshot_date=snap, status=status
    )
    db.add(p)
    db.flush()
    return p


def _add_income(db, period_id, cur_id, amount, source="Salary"):
    inc = IncomeEntry(
        id=uuid.uuid4(), calculation_period_id=period_id,
        source_name=source, amount=amount, currency_id=cur_id
    )
    db.add(inc)
    db.flush()
    return inc


def _add_expense(db, period_id, cat_id, cur_id, amount, name="Expense", exp_date=None):
    exp = ExpenseItem(
        id=uuid.uuid4(), calculation_period_id=period_id,
        category_id=cat_id, item_name=name, amount=amount,
        currency_id=cur_id,
        expense_date=exp_date
    )
    db.add(exp)
    db.flush()
    return exp


def _add_snapshot(db, period_id, account_id, balance, snap_date=None):
    snap = BalanceSnapshot(
        id=uuid.uuid4(), calculation_period_id=period_id,
        account_id=account_id, balance=balance,
        snapshot_date=snap_date or date(2026, 1, 31)
    )
    db.add(snap)
    db.flush()
    return snap


# ---------------------------------------------------------------------------
# get_spending_by_category
# ---------------------------------------------------------------------------

class TestGetSpendingByCategory:

    def test_basic_single_category(self, db: Session, test_user, test_currency, test_category):
        """Single expense in one category returns correct total and percentage."""
        period = _make_period(db, test_user.id, "SpendCat1",
                              date(2026, 1, 1), date(2026, 1, 31), date(2026, 1, 31))
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("200.00"), "Rent")
        db.commit()

        result = analytics_service.get_spending_by_category(db, test_user.id, period_id=period.id)

        assert result["total_expenses"] == 200.0
        assert len(result["by_category"]) == 1
        assert result["by_category"][0]["category_name"] == test_category.category_name
        assert result["by_category"][0]["percentage"] == 100.0

    def test_multiple_categories(self, db: Session, test_user, test_currency):
        """Expenses in multiple categories sum correctly and percentages add to 100."""
        cat1 = _make_category(db, test_user.id, "Food")
        cat2 = _make_category(db, test_user.id, "Transport")
        period = _make_period(db, test_user.id, "SpendMultiCat",
                              date(2026, 2, 1), date(2026, 2, 28), date(2026, 2, 28))
        _add_expense(db, period.id, cat1.id, test_currency.id, Decimal("300.00"), "Groceries")
        _add_expense(db, period.id, cat2.id, test_currency.id, Decimal("100.00"), "Bus")
        db.commit()

        result = analytics_service.get_spending_by_category(db, test_user.id, period_id=period.id)

        assert result["total_expenses"] == 400.0
        names = {c["category_name"] for c in result["by_category"]}
        assert "Food" in names
        assert "Transport" in names
        percentages = sum(c["percentage"] for c in result["by_category"])
        assert abs(percentages - 100.0) < 0.2

    def test_empty_period_returns_zero_total(self, db: Session, test_user):
        """Period with no expenses returns empty breakdown and zero total."""
        period = _make_period(db, test_user.id, "SpendEmpty",
                              date(2026, 3, 1), date(2026, 3, 31), date(2026, 3, 31))
        db.commit()

        result = analytics_service.get_spending_by_category(db, test_user.id, period_id=period.id)

        assert result["total_expenses"] == 0.0
        assert result["by_category"] == []

    def test_date_range_filter(self, db: Session, test_user, test_currency, test_category):
        """start_date / end_date filters expenses by expense_date."""
        period = _make_period(db, test_user.id, "SpendDate",
                              date(2026, 4, 1), date(2026, 4, 30), date(2026, 4, 30))
        _add_expense(db, period.id, test_category.id, test_currency.id,
                     Decimal("500.00"), "InRange", exp_date=date(2026, 4, 15))
        _add_expense(db, period.id, test_category.id, test_currency.id,
                     Decimal("999.00"), "OutOfRange", exp_date=date(2026, 5, 1))
        db.commit()

        result = analytics_service.get_spending_by_category(
            db, test_user.id,
            start_date=date(2026, 4, 1), end_date=date(2026, 4, 30)
        )

        assert result["total_expenses"] == 500.0

    def test_no_period_filter_returns_all_user_expenses(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Without period_id, all expenses for the user are returned."""
        p1 = _make_period(db, test_user.id, "AllP1",
                          date(2026, 5, 1), date(2026, 5, 31), date(2026, 5, 31))
        p2 = _make_period(db, test_user.id, "AllP2",
                          date(2026, 6, 1), date(2026, 6, 30), date(2026, 6, 30))
        _add_expense(db, p1.id, test_category.id, test_currency.id, Decimal("100.00"))
        _add_expense(db, p2.id, test_category.id, test_currency.id, Decimal("200.00"))
        db.commit()

        result = analytics_service.get_spending_by_category(db, test_user.id)
        # At least 300 total (may include other tests' data, but our categories' sum is right)
        assert result["total_expenses"] >= 300.0


# ---------------------------------------------------------------------------
# get_income_vs_expenses_trend
# ---------------------------------------------------------------------------

class TestGetIncomeVsExpensesTrend:

    def test_single_finalized_period(self, db: Session, test_user, test_currency, test_category):
        """Returns data for one finalized period."""
        period = _make_period(db, test_user.id, "TrendP1",
                              date(2026, 7, 1), date(2026, 7, 31), date(2026, 7, 31),
                              status="FINALIZED")
        _add_income(db, period.id, test_currency.id, Decimal("3000.00"))
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("1000.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id, num_periods=6)

        period_entry = next((p for p in result["periods"] if p["period_name"] == "TrendP1"), None)
        assert period_entry is not None
        assert period_entry["income"] == 3000.0
        assert period_entry["expenses"] == 1000.0
        assert period_entry["net"] == 2000.0

    def test_draft_periods_excluded(self, db: Session, test_user, test_currency, test_category):
        """DRAFT periods must not appear in the trend."""
        draft = _make_period(db, test_user.id, "DraftPeriod",
                             date(2026, 8, 1), date(2026, 8, 31), date(2026, 8, 31),
                             status="DRAFT")
        _add_income(db, draft.id, test_currency.id, Decimal("5000.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id)
        names = [p["period_name"] for p in result["periods"]]
        assert "DraftPeriod" not in names

    def test_empty_returns_zero_totals(self, db: Session, test_user):
        """User with no finalized periods gets zeroed totals and empty periods list."""
        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id)

        assert result["totals"]["total_income"] == 0.0
        assert result["totals"]["total_expenses"] == 0.0
        assert result["totals"]["average_monthly_net"] == 0.0

    def test_multiple_periods_sorted_chronologically(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Multiple periods are returned in chronological order."""
        p1 = _make_period(db, test_user.id, "TrendChron1",
                          date(2026, 9, 1), date(2026, 9, 30), date(2026, 9, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "TrendChron2",
                          date(2026, 10, 1), date(2026, 10, 31), date(2026, 10, 31),
                          status="FINALIZED")
        _add_income(db, p1.id, test_currency.id, Decimal("1000.00"))
        _add_income(db, p2.id, test_currency.id, Decimal("2000.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id)
        names = [p["period_name"] for p in result["periods"]]
        idx1 = names.index("TrendChron1")
        idx2 = names.index("TrendChron2")
        assert idx1 < idx2  # p1 must come before p2


# ---------------------------------------------------------------------------
# get_top_expenses
# ---------------------------------------------------------------------------

class TestGetTopExpenses:

    def test_returns_ordered_by_amount_desc(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Top expenses are ordered largest first."""
        period = _make_period(db, test_user.id, "TopExpP",
                              date(2026, 11, 1), date(2026, 11, 30), date(2026, 11, 30))
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("50.00"), "Small")
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("500.00"), "Large")
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("200.00"), "Medium")
        db.commit()

        results = analytics_service.get_top_expenses(db, test_user.id, period_id=period.id)

        amounts = [r["amount"] for r in results]
        assert amounts == sorted(amounts, reverse=True)
        assert results[0]["item_name"] == "Large"

    def test_limit_respected(self, db: Session, test_user, test_currency, test_category):
        """limit parameter caps the number of results."""
        period = _make_period(db, test_user.id, "TopExpLimit",
                              date(2026, 12, 1), date(2026, 12, 31), date(2026, 12, 31))
        for i in range(5):
            _add_expense(db, period.id, test_category.id, test_currency.id,
                         Decimal(str(i * 100 + 100)), f"Exp{i}")
        db.commit()

        results = analytics_service.get_top_expenses(
            db, test_user.id, period_id=period.id, limit=3
        )
        assert len(results) <= 3

    def test_no_period_filter_returns_all_user(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Without period_id, all user expenses across all periods are considered."""
        p1 = _make_period(db, test_user.id, "TopAllP1",
                          date(2027, 1, 1), date(2027, 1, 31), date(2027, 1, 31))
        p2 = _make_period(db, test_user.id, "TopAllP2",
                          date(2027, 2, 1), date(2027, 2, 28), date(2027, 2, 28))
        _add_expense(db, p1.id, test_category.id, test_currency.id, Decimal("1000.00"), "TopAll1")
        _add_expense(db, p2.id, test_category.id, test_currency.id, Decimal("900.00"), "TopAll2")
        db.commit()

        results = analytics_service.get_top_expenses(db, test_user.id, limit=100)
        names = [r["item_name"] for r in results]
        assert "TopAll1" in names
        assert "TopAll2" in names

    def test_empty_returns_empty_list(self, db: Session, test_user):
        """User with no expenses returns empty list."""
        results = analytics_service.get_top_expenses(db, test_user.id)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# get_net_worth_trend
# ---------------------------------------------------------------------------

class TestGetNetWorthTrend:

    def test_single_period_net_change_zero(self, db: Session, test_user, test_currency):
        """Single period has net_change=0 and percentage_change=0."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="NWAcc", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        period = _make_period(db, test_user.id, "NW1",
                              date(2027, 3, 1), date(2027, 3, 31), date(2027, 3, 31),
                              status="FINALIZED")
        _add_snapshot(db, period.id, account.id, Decimal("5000.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id)

        assert result["net_change"] == 0.0
        assert result["percentage_change"] == 0.0

    def test_two_periods_positive_growth(self, db: Session, test_user, test_currency):
        """Two periods with growing balance shows positive net_change."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="NWGrowAcc", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        p1 = _make_period(db, test_user.id, "NWGrow1",
                          date(2027, 4, 1), date(2027, 4, 30), date(2027, 4, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "NWGrow2",
                          date(2027, 5, 1), date(2027, 5, 31), date(2027, 5, 31),
                          status="FINALIZED")
        _add_snapshot(db, p1.id, account.id, Decimal("4000.00"))
        _add_snapshot(db, p2.id, account.id, Decimal("5000.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id)

        # net_change = 5000 - 4000 = 1000
        # percentage_change = 1000/4000 * 100 = 25%
        assert result["net_change"] == 1000.0
        assert abs(result["percentage_change"] - 25.0) < 0.1

    def test_draft_periods_excluded(self, db: Session, test_user, test_currency):
        """DRAFT periods must not appear in net worth trend."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="NWDraftAcc", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        draft = _make_period(db, test_user.id, "NWDraft",
                             date(2027, 6, 1), date(2027, 6, 30), date(2027, 6, 30),
                             status="DRAFT")
        _add_snapshot(db, draft.id, account.id, Decimal("99999.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id)
        names = [p["period_name"] for p in result["periods"]]
        assert "NWDraft" not in names

    def test_empty_user_returns_zero(self, db: Session, test_user):
        """User with no periods returns empty list and zero changes."""
        result = analytics_service.get_net_worth_trend(db, test_user.id)
        assert result["net_change"] == 0.0
        assert result["percentage_change"] == 0.0
        assert result["periods"] == []


# ---------------------------------------------------------------------------
# get_category_trends
# ---------------------------------------------------------------------------

class TestGetCategoryTrends:

    def test_stable_trend_same_amounts(self, db: Session, test_user, test_currency):
        """When all periods have same amount, trend is 'stable'."""
        cat = _make_category(db, test_user.id, "CatStable")
        p1 = _make_period(db, test_user.id, "CT_S1",
                          date(2027, 7, 1), date(2027, 7, 31), date(2027, 7, 31),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "CT_S2",
                          date(2027, 8, 1), date(2027, 8, 31), date(2027, 8, 31),
                          status="FINALIZED")
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("100.00"))
        _add_expense(db, p2.id, cat.id, test_currency.id, Decimal("100.00"))
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id)

        assert result["trend"] == "stable"
        assert result["average"] == 100.0

    def test_increasing_trend(self, db: Session, test_user, test_currency):
        """Last period > prev period by >5%  → trend is 'increasing'."""
        cat = _make_category(db, test_user.id, "CatIncrease")
        p1 = _make_period(db, test_user.id, "CT_I1",
                          date(2027, 9, 1), date(2027, 9, 30), date(2027, 9, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "CT_I2",
                          date(2027, 10, 1), date(2027, 10, 31), date(2027, 10, 31),
                          status="FINALIZED")
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("100.00"))
        _add_expense(db, p2.id, cat.id, test_currency.id, Decimal("200.00"))  # +100%
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id)

        assert result["trend"] == "increasing"

    def test_decreasing_trend(self, db: Session, test_user, test_currency):
        """Last period < prev period by >5%  → trend is 'decreasing'."""
        cat = _make_category(db, test_user.id, "CatDecrease")
        p1 = _make_period(db, test_user.id, "CT_D1",
                          date(2027, 11, 1), date(2027, 11, 30), date(2027, 11, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "CT_D2",
                          date(2027, 12, 1), date(2027, 12, 31), date(2027, 12, 31),
                          status="FINALIZED")
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("200.00"))
        _add_expense(db, p2.id, cat.id, test_currency.id, Decimal("50.00"))  # -75%
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id)

        assert result["trend"] == "decreasing"

    def test_wrong_category_user_returns_empty(self, db: Session, test_user):
        """Category belonging to a different user returns {}."""
        other_user_cat_id = uuid.uuid4()  # doesn't exist for this user
        result = analytics_service.get_category_trends(db, test_user.id, other_user_cat_id)
        assert result == {}

    def test_no_finalized_periods_returns_empty_list(self, db: Session, test_user, test_currency):
        """Category with no FINALIZED periods has empty periods list and zero average."""
        cat = _make_category(db, test_user.id, "CatNoFinalized")
        draft = _make_period(db, test_user.id, "CT_Draft",
                             date(2028, 1, 1), date(2028, 1, 31), date(2028, 1, 31),
                             status="DRAFT")
        _add_expense(db, draft.id, cat.id, test_currency.id, Decimal("100.00"))
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id)

        assert result["periods"] == []
        assert result["average"] == 0.0


# ---------------------------------------------------------------------------
# get_period_comparison
# ---------------------------------------------------------------------------

class TestGetPeriodComparison:

    def test_basic_comparison(self, db: Session, test_user, test_currency, test_category):
        """Two periods are compared correctly with diffs."""
        p1 = _make_period(db, test_user.id, "CompP1",
                          date(2028, 2, 1), date(2028, 2, 28), date(2028, 2, 28))
        p2 = _make_period(db, test_user.id, "CompP2",
                          date(2028, 3, 1), date(2028, 3, 31), date(2028, 3, 31))
        _add_income(db, p1.id, test_currency.id, Decimal("2000.00"))
        _add_income(db, p2.id, test_currency.id, Decimal("3000.00"))
        _add_expense(db, p1.id, test_category.id, test_currency.id, Decimal("500.00"))
        _add_expense(db, p2.id, test_category.id, test_currency.id, Decimal("800.00"))
        db.commit()

        result = analytics_service.get_period_comparison(
            db, test_user.id, p1.id, p2.id
        )

        assert result["period_1"]["income"] == 2000.0
        assert result["period_2"]["income"] == 3000.0
        assert result["differences"]["income_diff"] == 1000.0
        assert result["differences"]["expenses_diff"] == 300.0
        assert result["differences"]["net_diff"] == 700.0

    def test_wrong_user_returns_empty(self, db: Session, test_user):
        """Periods not belonging to user return empty dict."""
        result = analytics_service.get_period_comparison(
            db, test_user.id, uuid.uuid4(), uuid.uuid4()
        )
        assert result == {}

    def test_category_breakdown_included(
        self, db: Session, test_user, test_currency
    ):
        """Category breakdown is included for both periods."""
        cat1 = _make_category(db, test_user.id, "CompCat1")
        cat2 = _make_category(db, test_user.id, "CompCat2")
        p1 = _make_period(db, test_user.id, "CompCatP1",
                          date(2028, 4, 1), date(2028, 4, 30), date(2028, 4, 30))
        p2 = _make_period(db, test_user.id, "CompCatP2",
                          date(2028, 5, 1), date(2028, 5, 31), date(2028, 5, 31))
        _add_expense(db, p1.id, cat1.id, test_currency.id, Decimal("300.00"), "P1Cat1")
        _add_expense(db, p2.id, cat1.id, test_currency.id, Decimal("400.00"), "P2Cat1")
        _add_expense(db, p2.id, cat2.id, test_currency.id, Decimal("200.00"), "P2Cat2")
        db.commit()

        result = analytics_service.get_period_comparison(
            db, test_user.id, p1.id, p2.id
        )

        # CompCat1 appears in both periods; diff should be 100
        change = next(c for c in result["category_changes"] if c["category"] == "CompCat1")
        assert change["diff"] == 100.0
        # CompCat2 only in p2; p1 value = 0
        change2 = next(c for c in result["category_changes"] if c["category"] == "CompCat2")
        assert change2["period_1"] == 0.0
        assert change2["period_2"] == 200.0


# ---------------------------------------------------------------------------
# detect_recurring_patterns
# ---------------------------------------------------------------------------

class TestDetectRecurringPatterns:

    def test_item_appearing_3_times_detected(self, db: Session, test_user, test_currency):
        """Expense item appearing in 3+ periods is flagged as recurring."""
        cat = _make_category(db, test_user.id, "RecSubs")
        for i in range(3):
            p = _make_period(db, test_user.id, f"RecP{i}",
                             date(2028, 6 + i, 1), date(2028, 6 + i, 28),
                             date(2028, 6 + i, 28))
            _add_expense(db, p.id, cat.id, test_currency.id, Decimal("50.00"), "Spotify")
        db.commit()

        patterns = analytics_service.detect_recurring_patterns(db, test_user.id)

        spotify = next((p for p in patterns if p["item_name"] == "Spotify"), None)
        assert spotify is not None
        assert spotify["average_amount"] == 50.0
        assert spotify["frequency"] == "3 periods"
        assert spotify["confidence"] == "medium"

    def test_item_appearing_2_times_not_detected(self, db: Session, test_user, test_currency):
        """Item appearing only twice is NOT flagged (requires >= 3)."""
        cat = _make_category(db, test_user.id, "RecRare")
        for i in range(2):
            p = _make_period(db, test_user.id, f"RarePeriod{i}",
                             date(2029, 1 + i, 1), date(2029, 1 + i, 28),
                             date(2029, 1 + i, 28))
            _add_expense(db, p.id, cat.id, test_currency.id, Decimal("100.00"), "RareItem")
        db.commit()

        patterns = analytics_service.detect_recurring_patterns(db, test_user.id)
        names = [p["item_name"] for p in patterns]
        assert "RareItem" not in names

    def test_high_confidence_after_6_occurrences(self, db: Session, test_user, test_currency):
        """Item appearing in 6+ periods gets 'high' confidence."""
        cat = _make_category(db, test_user.id, "RecHigh")
        for i in range(6):
            p = _make_period(db, test_user.id, f"HighConfP{i}",
                             date(2029, 3, 1 + i), date(2029, 3, 1 + i),
                             date(2029, 3, 1 + i))
            _add_expense(db, p.id, cat.id, test_currency.id, Decimal("10.00"), "HighFreq")
        db.commit()

        patterns = analytics_service.detect_recurring_patterns(db, test_user.id)
        hf = next((p for p in patterns if p["item_name"] == "HighFreq"), None)
        assert hf is not None
        assert hf["confidence"] == "high"


# ---------------------------------------------------------------------------
# detect_anomalies
# ---------------------------------------------------------------------------

class TestDetectAnomalies:

    def test_large_expense_flagged(self, db: Session, test_user, test_currency):
        """Expense > 2.5x historical category average is flagged as LARGE_EXPENSE."""
        cat = _make_category(db, test_user.id, "AnomalyFood")
        p_hist = _make_period(db, test_user.id, "AnoHist",
                              date(2029, 4, 1), date(2029, 4, 30), date(2029, 4, 30),
                              status="FINALIZED")
        p_curr = _make_period(db, test_user.id, "AnoCurr",
                              date(2029, 5, 1), date(2029, 5, 31), date(2029, 5, 31),
                              status="DRAFT")
        _add_expense(db, p_hist.id, cat.id, test_currency.id, Decimal("100.00"), "Normal")
        _add_expense(db, p_curr.id, cat.id, test_currency.id, Decimal("500.00"), "Huge")
        db.commit()

        anomalies = analytics_service.detect_anomalies(db, test_user.id, p_curr.id)

        assert len(anomalies) == 1
        assert anomalies[0]["type"] == "LARGE_EXPENSE"
        assert anomalies[0]["item_name"] == "Huge"
        assert anomalies[0]["amount"] == 500.0
        assert anomalies[0]["historical_average"] == 100.0

    def test_normal_expense_not_flagged(self, db: Session, test_user, test_currency):
        """Expense within 2.5x average is NOT flagged."""
        cat = _make_category(db, test_user.id, "AnoNormal")
        p_hist = _make_period(db, test_user.id, "AnoNHist",
                              date(2029, 6, 1), date(2029, 6, 30), date(2029, 6, 30))
        p_curr = _make_period(db, test_user.id, "AnoNCurr",
                              date(2029, 7, 1), date(2029, 7, 31), date(2029, 7, 31))
        _add_expense(db, p_hist.id, cat.id, test_currency.id, Decimal("100.00"), "Hist")
        _add_expense(db, p_curr.id, cat.id, test_currency.id, Decimal("200.00"), "Near")
        # 200 < 2.5 * 100 = 250, so NOT flagged
        db.commit()

        anomalies = analytics_service.detect_anomalies(db, test_user.id, p_curr.id)

        names = [a["item_name"] for a in anomalies]
        assert "Near" not in names

    def test_no_history_not_flagged(self, db: Session, test_user, test_currency):
        """Expense with no historical data (hist_avg=None) is not flagged."""
        cat = _make_category(db, test_user.id, "AnoNoHist")
        p_curr = _make_period(db, test_user.id, "AnoNoHistCurr",
                              date(2029, 8, 1), date(2029, 8, 31), date(2029, 8, 31))
        _add_expense(db, p_curr.id, cat.id, test_currency.id, Decimal("9999.00"), "NewItem")
        db.commit()

        anomalies = analytics_service.detect_anomalies(db, test_user.id, p_curr.id)

        names = [a["item_name"] for a in anomalies]
        assert "NewItem" not in names

    def test_empty_period_returns_empty(self, db: Session, test_user):
        """Period with no expenses returns empty anomalies list."""
        period = _make_period(db, test_user.id, "AnoEmpty",
                              date(2029, 9, 1), date(2029, 9, 30), date(2029, 9, 30))
        db.commit()

        anomalies = analytics_service.detect_anomalies(db, test_user.id, period.id)
        assert anomalies == []


# ---------------------------------------------------------------------------
# Kill-tests round 2 — survivors from 78% run
# ---------------------------------------------------------------------------

class TestKillMutantsSpendingByCategory2:

    def test_currency_key_in_by_category_item(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Each by_category item must have 'currency' key (kills XXcurrencyXX mutation)."""
        period = _make_period(db, test_user.id, "KillCurKey",
                              date(2033, 1, 1), date(2033, 1, 31), date(2033, 1, 31))
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("100.00"))
        db.commit()

        result = analytics_service.get_spending_by_category(db, test_user.id, period_id=period.id)

        assert len(result["by_category"]) == 1
        assert "currency" in result["by_category"][0]
        assert result["by_category"][0]["currency"] == test_currency.ticker

    def test_percentage_key_in_by_category_item(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Each by_category item must have 'percentage' key == correct value (kills XXpercentageXX, =1, =None)."""
        period = _make_period(db, test_user.id, "KillPctKey",
                              date(2033, 2, 1), date(2033, 2, 28), date(2033, 2, 28))
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("200.00"))
        db.commit()

        result = analytics_service.get_spending_by_category(db, test_user.id, period_id=period.id)

        cat = result["by_category"][0]
        assert "percentage" in cat
        assert cat["percentage"] == 100.0  # kills =1.0 and =None mutations

    def test_total_expenses_key_in_result(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Result must have 'total_expenses' key (kills XXtotal_expensesXX mutation)."""
        period = _make_period(db, test_user.id, "KillTotalExpKey",
                              date(2033, 3, 1), date(2033, 3, 31), date(2033, 3, 31))
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("150.00"))
        db.commit()

        result = analytics_service.get_spending_by_category(db, test_user.id, period_id=period.id)

        assert "total_expenses" in result
        assert result["total_expenses"] == 150.0

    def test_start_date_boundary_inclusive(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Expense ON start_date must be included (kills >= → > in start_date filter)."""
        period = _make_period(db, test_user.id, "KillStartDate",
                              date(2033, 4, 1), date(2033, 4, 30), date(2033, 4, 30))
        _add_expense(db, period.id, test_category.id, test_currency.id,
                     Decimal("333.00"), "OnStart", exp_date=date(2033, 4, 1))
        _add_expense(db, period.id, test_category.id, test_currency.id,
                     Decimal("111.00"), "BeforeStart", exp_date=date(2033, 3, 31))
        db.commit()

        result = analytics_service.get_spending_by_category(
            db, test_user.id,
            start_date=date(2033, 4, 1), end_date=date(2033, 4, 30)
        )

        assert result["total_expenses"] == 333.0  # BeforeStart excluded

    def test_label_total_accessible(
        self, db: Session, test_user, test_currency, test_category
    ):
        """SQL label 'total' must be accessible (kills label('XXtotalXX') mutation)."""
        period = _make_period(db, test_user.id, "KillLabelTotal",
                              date(2033, 5, 1), date(2033, 5, 31), date(2033, 5, 31))
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("450.00"))
        db.commit()

        # If label is wrong, the function will raise AttributeError → test errors
        result = analytics_service.get_spending_by_category(db, test_user.id, period_id=period.id)

        assert result["total_expenses"] == 450.0
        assert result["by_category"][0]["total"] == 450.0


class TestKillMutantsIncomeTrend2:

    def test_period_dates_key_in_result(
        self, db: Session, test_user, test_currency
    ):
        """Each period entry must have 'period_dates' key (kills XXperiod_datesXX)."""
        _make_category(db, test_user.id, "KillPDates")
        p = _make_period(db, test_user.id, "KillPDatesP",
                         date(2033, 6, 1), date(2033, 6, 30), date(2033, 6, 30),
                         status="FINALIZED")
        _add_income(db, p.id, test_currency.id, Decimal("1000.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id, num_periods=6)

        entry = next((e for e in result["periods"] if e["period_name"] == "KillPDatesP"), None)
        assert entry is not None
        assert "period_dates" in entry
        assert "2033-06-01" in entry["period_dates"]

    def test_currency_key_in_trend_entry(
        self, db: Session, test_user, test_currency
    ):
        """Each period entry must have 'currency' key (kills XXcurrencyXX in trend)."""
        p = _make_period(db, test_user.id, "KillTrendCurP",
                         date(2033, 7, 1), date(2033, 7, 31), date(2033, 7, 31),
                         status="FINALIZED")
        _add_income(db, p.id, test_currency.id, Decimal("500.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id, num_periods=6)

        entry = next((e for e in result["periods"] if e["period_name"] == "KillTrendCurP"), None)
        assert entry is not None
        assert "currency" in entry

    def test_income_and_expense_accumulate_across_periods(
        self, db: Session, test_user, test_currency
    ):
        """totals are cumulative across 3 periods (kills += → = or -= mutations)."""
        cat = _make_category(db, test_user.id, "KillAccum")
        p1 = _make_period(db, test_user.id, "KillAccumP1",
                          date(2033, 8, 1), date(2033, 8, 31), date(2033, 8, 31),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillAccumP2",
                          date(2033, 9, 1), date(2033, 9, 30), date(2033, 9, 30),
                          status="FINALIZED")
        p3 = _make_period(db, test_user.id, "KillAccumP3",
                          date(2033, 10, 1), date(2033, 10, 31), date(2033, 10, 31),
                          status="FINALIZED")
        _add_income(db, p1.id, test_currency.id, Decimal("1000.00"))
        _add_income(db, p2.id, test_currency.id, Decimal("2000.00"))
        _add_income(db, p3.id, test_currency.id, Decimal("3000.00"))
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("200.00"))
        _add_expense(db, p2.id, cat.id, test_currency.id, Decimal("300.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id, num_periods=6)

        assert result["totals"]["total_income"] == 6000.0
        assert result["totals"]["total_expenses"] == 500.0
        assert result["totals"]["total_net"] == 5500.0

    def test_avg_net_is_division_not_multiplication(
        self, db: Session, test_user, test_currency
    ):
        """avg_net = total_net / num_periods (kills / → * mutation)."""
        cat = _make_category(db, test_user.id, "KillAvgDiv")
        p1 = _make_period(db, test_user.id, "KillAvgDiv1",
                          date(2033, 11, 1), date(2033, 11, 30), date(2033, 11, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillAvgDiv2",
                          date(2033, 12, 1), date(2033, 12, 31), date(2033, 12, 31),
                          status="FINALIZED")
        _add_income(db, p1.id, test_currency.id, Decimal("1000.00"))
        _add_income(db, p2.id, test_currency.id, Decimal("1000.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id, num_periods=6)

        # total_net=2000, 2 periods → avg=1000 (not 2000*2=4000)
        assert result["totals"]["average_monthly_net"] == 1000.0


class TestKillMutantsTopExpenses2:

    def test_category_key_in_result(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Top expense entries must have 'category' key (kills XXcategoryXX mutation)."""
        period = _make_period(db, test_user.id, "KillTopCatKey",
                              date(2034, 1, 1), date(2034, 1, 31), date(2034, 1, 31))
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("500.00"), "Big")
        db.commit()

        results = analytics_service.get_top_expenses(db, test_user.id, period_id=period.id)

        assert len(results) > 0
        assert "category" in results[0]
        assert results[0]["category"] == test_category.category_name

    def test_date_key_in_result(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Top expense entries must have 'date' key (kills XXdateXX mutation)."""
        period = _make_period(db, test_user.id, "KillTopDateKey",
                              date(2034, 2, 1), date(2034, 2, 28), date(2034, 2, 28))
        _add_expense(db, period.id, test_category.id, test_currency.id,
                     Decimal("300.00"), "BigDate", exp_date=date(2034, 2, 15))
        db.commit()

        results = analytics_service.get_top_expenses(db, test_user.id, period_id=period.id)

        assert len(results) > 0
        assert "date" in results[0]
        assert results[0]["date"] == "2034-02-15"

    def test_limit_is_exactly_10_by_default(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Default limit is 10, not 11 (kills limit=11 mutation)."""
        period = _make_period(db, test_user.id, "KillLimit10",
                              date(2034, 3, 1), date(2034, 3, 31), date(2034, 3, 31))
        for i in range(12):
            _add_expense(db, period.id, test_category.id, test_currency.id,
                         Decimal(str(100 + i)), f"Item{i:02d}")
        db.commit()

        results = analytics_service.get_top_expenses(db, test_user.id, period_id=period.id)

        assert len(results) == 10  # default limit, not 11


class TestKillMutantsNetWorthTrend2:

    def test_first_balance_uses_index_0_not_1(
        self, db: Session, test_user, test_currency
    ):
        """First balance is period_data[0], not period_data[1] (kills [0] → [1])."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="KillIdx0Acc", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        p1 = _make_period(db, test_user.id, "KillIdx0_P1",
                          date(2034, 4, 1), date(2034, 4, 30), date(2034, 4, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillIdx0_P2",
                          date(2034, 5, 1), date(2034, 5, 31), date(2034, 5, 31),
                          status="FINALIZED")
        p3 = _make_period(db, test_user.id, "KillIdx0_P3",
                          date(2034, 6, 1), date(2034, 6, 30), date(2034, 6, 30),
                          status="FINALIZED")
        _add_snapshot(db, p1.id, account.id, Decimal("1000.00"))
        _add_snapshot(db, p2.id, account.id, Decimal("2000.00"))
        _add_snapshot(db, p3.id, account.id, Decimal("4000.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id, num_periods=12)

        # net_change = 4000 - 1000 = 3000; if [0]→[1] then 4000-2000=2000
        assert result["net_change"] == 3000.0

    def test_first_zero_percentage_no_division(
        self, db: Session, test_user, test_currency
    ):
        """When first=0, percentage_change=0 (kills 'first != 0' → 'first != 1')."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="KillZeroFirst", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        p1 = _make_period(db, test_user.id, "KillZeroFirst1",
                          date(2034, 7, 1), date(2034, 7, 31), date(2034, 7, 31),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillZeroFirst2",
                          date(2034, 8, 1), date(2034, 8, 31), date(2034, 8, 31),
                          status="FINALIZED")
        # p1 has balance 0 (no snapshots) → first=0 → no division
        _add_snapshot(db, p2.id, account.id, Decimal("5000.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id, num_periods=12)

        assert result["percentage_change"] == 0.0

    def test_snapshot_date_key_present(
        self, db: Session, test_user, test_currency
    ):
        """Period entries must have 'snapshot_date' key (kills XXsnapshot_dateXX)."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="KillSnapDateAcc", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        p = _make_period(db, test_user.id, "KillSnapDate",
                         date(2034, 9, 1), date(2034, 9, 30), date(2034, 9, 30),
                         status="FINALIZED")
        _add_snapshot(db, p.id, account.id, Decimal("1500.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id, num_periods=12)

        entry = next((e for e in result["periods"] if e["period_name"] == "KillSnapDate"), None)
        assert entry is not None
        assert "snapshot_date" in entry
        assert entry["snapshot_date"] == "2034-09-30"


class TestKillMutantsCategoryTrends2:

    def test_category_name_key_present(
        self, db: Session, test_user, test_currency
    ):
        """Result must have 'category_name' key (kills XXcategory_nameXX mutation)."""
        cat = _make_category(db, test_user.id, "KillCTNameKey")
        p = _make_period(db, test_user.id, "KillCTNameKP",
                         date(2034, 10, 1), date(2034, 10, 31), date(2034, 10, 31),
                         status="FINALIZED")
        _add_expense(db, p.id, cat.id, test_currency.id, Decimal("100.00"))
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id)

        assert "category_name" in result
        assert result["category_name"] == "KillCTNameKey"

    def test_periods_key_present(
        self, db: Session, test_user, test_currency
    ):
        """Result must have 'periods' key (kills XXperiodsXX mutation)."""
        cat = _make_category(db, test_user.id, "KillCTPeriodsKey")
        p = _make_period(db, test_user.id, "KillCTPeriodsKP",
                         date(2034, 11, 1), date(2034, 11, 30), date(2034, 11, 30),
                         status="FINALIZED")
        _add_expense(db, p.id, cat.id, test_currency.id, Decimal("100.00"))
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id)

        assert "periods" in result
        assert isinstance(result["periods"], list)

    def test_default_trend_is_stable_string(
        self, db: Session, test_user, test_currency
    ):
        """Default trend='stable' not 'XXstableXX' (kills string mutation)."""
        cat = _make_category(db, test_user.id, "KillStableStr")
        p1 = _make_period(db, test_user.id, "KillStableStr1",
                          date(2034, 12, 1), date(2034, 12, 31), date(2034, 12, 31),
                          status="FINALIZED")
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("100.00"))
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id, num_periods=1)

        assert result["trend"] == "stable"

    def test_wrong_user_category_returns_empty(
        self, db: Session, test_user, test_currency
    ):
        """Wrong user_id for category returns {} (kills != → == in user guard)."""
        cat = _make_category(db, test_user.id, "KillCTGuard")
        different_user_id = uuid.uuid4()
        result = analytics_service.get_category_trends(db, different_user_id, cat.id)
        assert result == {}

    def test_amount_key_in_period_entry(
        self, db: Session, test_user, test_currency
    ):
        """Period entries must have 'amount' key with correct value (kills XXamountXX)."""
        cat = _make_category(db, test_user.id, "KillAmtKey")
        p = _make_period(db, test_user.id, "KillAmtKeyP",
                         date(2035, 1, 1), date(2035, 1, 31), date(2035, 1, 31),
                         status="FINALIZED")
        _add_expense(db, p.id, cat.id, test_currency.id, Decimal("750.00"))
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id)

        assert len(result["periods"]) >= 1
        entry = next((e for e in result["periods"] if e["period_name"] == "KillAmtKeyP"), None)
        assert entry is not None
        assert "amount" in entry
        assert entry["amount"] == 750.0


class TestKillMutantsPeriodComparison2:

    def test_wrong_p2_user_returns_empty(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Periods from different user return {} (kills != → == in user_id check)."""
        p1 = _make_period(db, test_user.id, "KillGuardP1",
                          date(2035, 2, 1), date(2035, 2, 28), date(2035, 2, 28))
        p2 = _make_period(db, test_user.id, "KillGuardP2",
                          date(2035, 3, 1), date(2035, 3, 31), date(2035, 3, 31))
        db.commit()

        different_user = uuid.uuid4()
        result = analytics_service.get_period_comparison(db, different_user, p1.id, p2.id)
        assert result == {}

    def test_expenses_from_correct_period_only(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Category expenses use == period_id, not != (kills != mutation)."""
        p1 = _make_period(db, test_user.id, "KillCompExpP1",
                          date(2035, 4, 1), date(2035, 4, 30), date(2035, 4, 30))
        p2 = _make_period(db, test_user.id, "KillCompExpP2",
                          date(2035, 5, 1), date(2035, 5, 31), date(2035, 5, 31))
        _add_expense(db, p1.id, test_category.id, test_currency.id, Decimal("100.00"))
        _add_expense(db, p2.id, test_category.id, test_currency.id, Decimal("200.00"))
        db.commit()

        result = analytics_service.get_period_comparison(db, test_user.id, p1.id, p2.id)

        assert result["period_1"]["expenses"] == 100.0
        assert result["period_2"]["expenses"] == 200.0
        assert result["differences"]["expenses_diff"] == 100.0

    def test_income_diff_subtracts_not_adds(
        self, db: Session, test_user, test_currency, test_category
    ):
        """income_diff = p2.income - p1.income (kills + → - mutation)."""
        p1 = _make_period(db, test_user.id, "KillIncDiffP1",
                          date(2035, 6, 1), date(2035, 6, 30), date(2035, 6, 30))
        p2 = _make_period(db, test_user.id, "KillIncDiffP2",
                          date(2035, 7, 1), date(2035, 7, 31), date(2035, 7, 31))
        _add_income(db, p1.id, test_currency.id, Decimal("1000.00"))
        _add_income(db, p2.id, test_currency.id, Decimal("3000.00"))
        db.commit()

        result = analytics_service.get_period_comparison(db, test_user.id, p1.id, p2.id)

        # 3000 - 1000 = 2000 (not 3000 + 1000 = 4000)
        assert result["differences"]["income_diff"] == 2000.0

    def test_v2_default_is_zero_not_one(
        self, db: Session, test_user, test_currency
    ):
        """Missing category in p1 gets 0.0 default, not 1.0 (kills default 0.0 → 1.0)."""
        cat = _make_category(db, test_user.id, "KillV2Default")
        p1 = _make_period(db, test_user.id, "KillV2DefaultP1",
                          date(2035, 8, 1), date(2035, 8, 31), date(2035, 8, 31))
        p2 = _make_period(db, test_user.id, "KillV2DefaultP2",
                          date(2035, 9, 1), date(2035, 9, 30), date(2035, 9, 30))
        _add_expense(db, p2.id, cat.id, test_currency.id, Decimal("500.00"), "OnlyP2")
        db.commit()

        result = analytics_service.get_period_comparison(db, test_user.id, p1.id, p2.id)

        change = next((c for c in result["category_changes"] if c["category"] == "KillV2Default"), None)
        assert change is not None
        assert change["period_1"] == 0.0
        assert change["diff"] == 500.0  # not 500-1=499


class TestKillMutantsAnomalies2:

    def test_anomaly_query_uses_current_period(
        self, db: Session, test_user, test_currency
    ):
        """Anomaly detection queries expenses from current period (kills != mutation)."""
        cat = _make_category(db, test_user.id, "KillAnoPeriod")
        p_hist = _make_period(db, test_user.id, "KillAnoPHist",
                              date(2035, 10, 1), date(2035, 10, 31), date(2035, 10, 31),
                              status="FINALIZED")
        p_curr = _make_period(db, test_user.id, "KillAnoPCurr",
                              date(2035, 11, 1), date(2035, 11, 30), date(2035, 11, 30),
                              status="DRAFT")
        _add_expense(db, p_hist.id, cat.id, test_currency.id, Decimal("100.00"), "HistNormal")
        _add_expense(db, p_curr.id, cat.id, test_currency.id, Decimal("400.00"), "CurrLarge")
        db.commit()

        anomalies = analytics_service.detect_anomalies(db, test_user.id, p_curr.id)

        names = [a["item_name"] for a in anomalies]
        assert "CurrLarge" in names
        assert "HistNormal" not in names

    def test_type_value_is_large_expense_string(
        self, db: Session, test_user, test_currency
    ):
        """Anomaly type must be 'LARGE_EXPENSE' string exactly (kills XXLARGE_EXPENSEXX)."""
        cat = _make_category(db, test_user.id, "KillAnoTypeStr")
        p_hist = _make_period(db, test_user.id, "KillAnoTypeHist",
                              date(2035, 12, 1), date(2035, 12, 31), date(2035, 12, 31),
                              status="FINALIZED")
        p_curr = _make_period(db, test_user.id, "KillAnoTypeCurr",
                              date(2036, 1, 1), date(2036, 1, 31), date(2036, 1, 31),
                              status="DRAFT")
        _add_expense(db, p_hist.id, cat.id, test_currency.id, Decimal("100.00"), "H")
        _add_expense(db, p_curr.id, cat.id, test_currency.id, Decimal("500.00"), "BigType")
        db.commit()

        anomalies = analytics_service.detect_anomalies(db, test_user.id, p_curr.id)
        flagged = next((a for a in anomalies if a["item_name"] == "BigType"), None)

        assert flagged is not None
        assert flagged["type"] == "LARGE_EXPENSE"

    def test_confidence_high_value_not_xxhighxx(
        self, db: Session, test_user, test_currency
    ):
        """High confidence string must be 'high' not 'XXhighXX' (kills string mutation)."""
        cat = _make_category(db, test_user.id, "KillHighStr")
        for i in range(7):
            p = _make_period(db, test_user.id, f"KillHighStrP{i}",
                             date(2036, 2, 1 + i), date(2036, 2, 1 + i),
                             date(2036, 2, 1 + i))
            _add_expense(db, p.id, cat.id, test_currency.id, Decimal("10.00"), "HighStrItem")
        db.commit()

        patterns = analytics_service.detect_recurring_patterns(db, test_user.id)
        item = next((p for p in patterns if p["item_name"] == "HighStrItem"), None)

        assert item is not None
        assert item["confidence"] == "high"

    def test_recurring_category_key_present(
        self, db: Session, test_user, test_currency
    ):
        """Recurring pattern must have 'category' key (kills XXcategoryXX in recurring)."""
        cat = _make_category(db, test_user.id, "KillRecCatKey")
        for i in range(3):
            p = _make_period(db, test_user.id, f"KillRecCatKP{i}",
                             date(2036, 3, 1 + i), date(2036, 3, 1 + i),
                             date(2036, 3, 1 + i))
            _add_expense(db, p.id, cat.id, test_currency.id, Decimal("50.00"), "RecCatItem")
        db.commit()

        patterns = analytics_service.detect_recurring_patterns(db, test_user.id)
        item = next((p for p in patterns if p["item_name"] == "RecCatItem"), None)

        assert item is not None
        assert "category" in item
        assert item["category"] == "KillRecCatKey"


# ---------------------------------------------------------------------------
# Kill-tests for surviving mutants
# ---------------------------------------------------------------------------

class TestKillMutantsSpendingByCategory:

    def test_currency_breakdown_sums_not_subtracts(
        self, db: Session, test_user, test_currency
    ):
        """currency_breakdown must ADD row totals, not subtract (kills += → -=)."""
        cat = _make_category(db, test_user.id, "KillBreakCat")
        period = _make_period(db, test_user.id, "KillBreak",
                              date(2030, 1, 1), date(2030, 1, 31), date(2030, 1, 31))
        _add_expense(db, period.id, cat.id, test_currency.id, Decimal("300.00"), "E1")
        _add_expense(db, period.id, cat.id, test_currency.id, Decimal("200.00"), "E2")
        db.commit()

        result = analytics_service.get_spending_by_category(db, test_user.id, period_id=period.id)

        # currency_breakdown for this ticker must be 500, not -500
        ticker = test_currency.ticker
        assert result["currency_breakdown"][ticker] == 500.0
        assert result["currency_breakdown"][ticker] > 0

    def test_end_date_boundary_inclusive(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Expense ON end_date must be INCLUDED (kills <= → <)."""
        period = _make_period(db, test_user.id, "KillEndDate",
                              date(2030, 2, 1), date(2030, 2, 28), date(2030, 2, 28))
        # expense_date exactly equals end_date
        _add_expense(db, period.id, test_category.id, test_currency.id,
                     Decimal("777.00"), "OnBoundary", exp_date=date(2030, 2, 28))
        _add_expense(db, period.id, test_category.id, test_currency.id,
                     Decimal("111.00"), "AfterBoundary", exp_date=date(2030, 3, 1))
        db.commit()

        result = analytics_service.get_spending_by_category(
            db, test_user.id,
            start_date=date(2030, 2, 1), end_date=date(2030, 2, 28)
        )

        assert result["total_expenses"] == 777.0

    def test_currency_breakdown_key_present(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Return dict must contain 'currency_breakdown' key (kills XXcurrency_breakdownXX)."""
        period = _make_period(db, test_user.id, "KillCBKey",
                              date(2030, 3, 1), date(2030, 3, 31), date(2030, 3, 31))
        _add_expense(db, period.id, test_category.id, test_currency.id, Decimal("100.00"))
        db.commit()

        result = analytics_service.get_spending_by_category(db, test_user.id, period_id=period.id)

        assert "currency_breakdown" in result
        assert isinstance(result["currency_breakdown"], dict)


class TestKillMutantsIncomeTrend:

    def test_total_income_sums_all_periods(
        self, db: Session, test_user, test_currency
    ):
        """totals.total_income must be SUM of all periods (kills += → = and += → -=)."""
        cat = _make_category(db, test_user.id, "KillTrendCat")
        p1 = _make_period(db, test_user.id, "KillTrI1",
                          date(2030, 4, 1), date(2030, 4, 30), date(2030, 4, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillTrI2",
                          date(2030, 5, 1), date(2030, 5, 31), date(2030, 5, 31),
                          status="FINALIZED")
        _add_income(db, p1.id, test_currency.id, Decimal("1000.00"))
        _add_income(db, p2.id, test_currency.id, Decimal("2000.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id, num_periods=6)

        # total_income = 1000 + 2000 = 3000, NOT just 2000 (last) or -1000 (subtraction)
        assert result["totals"]["total_income"] == 3000.0

    def test_total_expenses_sums_all_periods(
        self, db: Session, test_user, test_currency
    ):
        """totals.total_expenses must be SUM of all periods (kills += → = and += → -=)."""
        cat = _make_category(db, test_user.id, "KillTrendCatExp")
        p1 = _make_period(db, test_user.id, "KillTrE1",
                          date(2030, 6, 1), date(2030, 6, 30), date(2030, 6, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillTrE2",
                          date(2030, 7, 1), date(2030, 7, 31), date(2030, 7, 31),
                          status="FINALIZED")
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("400.00"))
        _add_expense(db, p2.id, cat.id, test_currency.id, Decimal("600.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id, num_periods=6)

        # total_expenses = 400 + 600 = 1000
        assert result["totals"]["total_expenses"] == 1000.0

    def test_total_net_subtracts_expenses(
        self, db: Session, test_user, test_currency
    ):
        """total_net = total_income - total_expenses (kills + → -, None assignment)."""
        cat = _make_category(db, test_user.id, "KillNetCat")
        p1 = _make_period(db, test_user.id, "KillNet1",
                          date(2030, 8, 1), date(2030, 8, 31), date(2030, 8, 31),
                          status="FINALIZED")
        _add_income(db, p1.id, test_currency.id, Decimal("5000.00"))
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("2000.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id, num_periods=6)

        entry = next((p for p in result["periods"] if p["period_name"] == "KillNet1"), None)
        assert entry is not None
        assert entry["net"] == 3000.0  # 5000 - 2000
        assert result["totals"]["total_net"] == 3000.0

    def test_total_income_key_present(
        self, db: Session, test_user, test_currency
    ):
        """totals dict must have 'total_income' key (kills XXtotal_incomeXX mutation)."""
        cat = _make_category(db, test_user.id, "KillKeyInc")
        p = _make_period(db, test_user.id, "KillKeyIncP",
                         date(2030, 9, 1), date(2030, 9, 30), date(2030, 9, 30),
                         status="FINALIZED")
        _add_income(db, p.id, test_currency.id, Decimal("100.00"))
        db.commit()

        result = analytics_service.get_income_vs_expenses_trend(db, test_user.id, num_periods=6)

        assert "total_income" in result["totals"]
        assert "total_net" in result["totals"]


class TestKillMutantsNetWorthTrend:

    def test_balance_from_correct_period_only(
        self, db: Session, test_user, test_currency
    ):
        """Net worth uses snapshots FROM each period, not != (kills period_id != p.id)."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="KillNWAcc", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        p1 = _make_period(db, test_user.id, "KillNW_P1",
                          date(2030, 10, 1), date(2030, 10, 31), date(2030, 10, 31),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillNW_P2",
                          date(2030, 11, 1), date(2030, 11, 30), date(2030, 11, 30),
                          status="FINALIZED")
        _add_snapshot(db, p1.id, account.id, Decimal("1000.00"))
        _add_snapshot(db, p2.id, account.id, Decimal("3000.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id, num_periods=12)

        period_entries = {p["period_name"]: p["total_balance"] for p in result["periods"]}
        assert period_entries["KillNW_P1"] == 1000.0
        assert period_entries["KillNW_P2"] == 3000.0
        # net_change = 3000 - 1000 = 2000 (not -2000 if periods are swapped)
        assert result["net_change"] == 2000.0

    def test_by_currency_key_present(
        self, db: Session, test_user, test_currency
    ):
        """Each period entry must have 'by_currency' dict (kills by_currency = None)."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="KillByCurAcc", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        p = _make_period(db, test_user.id, "KillByCur",
                         date(2030, 12, 1), date(2030, 12, 31), date(2030, 12, 31),
                         status="FINALIZED")
        _add_snapshot(db, p.id, account.id, Decimal("500.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id, num_periods=12)

        entry = next((e for e in result["periods"] if e["period_name"] == "KillByCur"), None)
        assert entry is not None
        assert "by_currency" in entry
        assert isinstance(entry["by_currency"], dict)
        assert test_currency.ticker in entry["by_currency"]

    def test_percentage_change_zero_for_single_period(
        self, db: Session, test_user, test_currency
    ):
        """Single period → percentage_change must be 0.0 (kills init = 1.0)."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="KillPctAcc", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        p = _make_period(db, test_user.id, "KillPctSingle",
                         date(2031, 1, 1), date(2031, 1, 31), date(2031, 1, 31),
                         status="FINALIZED")
        _add_snapshot(db, p.id, account.id, Decimal("9000.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id, num_periods=12)

        assert result["percentage_change"] == 0.0

    def test_net_change_key_present(
        self, db: Session, test_user, test_currency
    ):
        """Result must have 'net_change' key (kills XXnet_changeXX mutation)."""
        account = Account(
            id=uuid.uuid4(), user_id=test_user.id,
            account_name="KillNCAcc", account_type="BANK",
            currency_id=test_currency.id, opening_balance=Decimal("0.00")
        )
        db.add(account)
        p1 = _make_period(db, test_user.id, "KillNC1",
                          date(2031, 2, 1), date(2031, 2, 28), date(2031, 2, 28),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillNC2",
                          date(2031, 3, 1), date(2031, 3, 31), date(2031, 3, 31),
                          status="FINALIZED")
        _add_snapshot(db, p1.id, account.id, Decimal("100.00"))
        _add_snapshot(db, p2.id, account.id, Decimal("200.00"))
        db.commit()

        result = analytics_service.get_net_worth_trend(db, test_user.id, num_periods=12)

        assert "net_change" in result
        assert "percentage_change" in result


class TestKillMutantsCategoryTrends:

    def test_exactly_two_periods_detects_trend(
        self, db: Session, test_user, test_currency
    ):
        """Exactly 2 periods must detect trend (kills >= 2 → > 2 requiring 3)."""
        cat = _make_category(db, test_user.id, "KillCT2")
        p1 = _make_period(db, test_user.id, "KillCT2_P1",
                          date(2031, 4, 1), date(2031, 4, 30), date(2031, 4, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillCT2_P2",
                          date(2031, 5, 1), date(2031, 5, 31), date(2031, 5, 31),
                          status="FINALIZED")
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("100.00"))
        _add_expense(db, p2.id, cat.id, test_currency.id, Decimal("300.00"))  # +200%
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id, num_periods=2)

        assert result["trend"] == "increasing"

    def test_increasing_requires_more_than_5pct(
        self, db: Session, test_user, test_currency
    ):
        """Increasing requires last > prev*1.05, NOT >= (kills > → >=)."""
        cat = _make_category(db, test_user.id, "KillCT5pct")
        p1 = _make_period(db, test_user.id, "KillCT5_P1",
                          date(2031, 6, 1), date(2031, 6, 30), date(2031, 6, 30),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillCT5_P2",
                          date(2031, 7, 1), date(2031, 7, 31), date(2031, 7, 31),
                          status="FINALIZED")
        # last == prev * 1.05 exactly → should be "stable" not "increasing"
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("100.00"))
        _add_expense(db, p2.id, cat.id, test_currency.id, Decimal("105.00"))  # exactly 1.05x
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id, num_periods=2)

        assert result["trend"] == "stable"  # 105 is NOT > 1.05*100

    def test_decreasing_requires_more_than_5pct(
        self, db: Session, test_user, test_currency
    ):
        """Decreasing requires last < prev*0.95, NOT <= (kills < → <=)."""
        cat = _make_category(db, test_user.id, "KillCTDec5pct")
        p1 = _make_period(db, test_user.id, "KillCTD_P1",
                          date(2031, 8, 1), date(2031, 8, 31), date(2031, 8, 31),
                          status="FINALIZED")
        p2 = _make_period(db, test_user.id, "KillCTD_P2",
                          date(2031, 9, 1), date(2031, 9, 30), date(2031, 9, 30),
                          status="FINALIZED")
        # last == prev * 0.95 exactly → should be "stable" not "decreasing"
        _add_expense(db, p1.id, cat.id, test_currency.id, Decimal("100.00"))
        _add_expense(db, p2.id, cat.id, test_currency.id, Decimal("95.00"))  # exactly 0.95x
        db.commit()

        result = analytics_service.get_category_trends(db, test_user.id, cat.id, num_periods=2)

        assert result["trend"] == "stable"  # 95 is NOT < 0.95*100


class TestKillMutantsPeriodComparison:

    def test_p2_exists_required(
        self, db: Session, test_user, test_currency, test_category
    ):
        """p2 being None should return {} (kills 'not p1 or not p2' → 'not p1 or p2')."""
        p1 = _make_period(db, test_user.id, "KillCompP1",
                          date(2031, 10, 1), date(2031, 10, 31), date(2031, 10, 31))
        db.commit()

        # p2_id doesn't exist → p2 is None → should return {}
        result = analytics_service.get_period_comparison(
            db, test_user.id, p1.id, uuid.uuid4()
        )
        assert result == {}

    def test_period_2_key_present(
        self, db: Session, test_user, test_currency, test_category
    ):
        """Result must have 'period_2' key (kills XXperiod_2XX mutation)."""
        p1 = _make_period(db, test_user.id, "KillP2Key1",
                          date(2031, 11, 1), date(2031, 11, 30), date(2031, 11, 30))
        p2 = _make_period(db, test_user.id, "KillP2Key2",
                          date(2031, 12, 1), date(2031, 12, 31), date(2031, 12, 31))
        _add_income(db, p1.id, test_currency.id, Decimal("1000.00"))
        _add_income(db, p2.id, test_currency.id, Decimal("2000.00"))
        db.commit()

        result = analytics_service.get_period_comparison(db, test_user.id, p1.id, p2.id)

        assert "period_1" in result
        assert "period_2" in result
        assert result["period_2"]["income"] == 2000.0

    def test_income_diff_uses_both_periods_income(
        self, db: Session, test_user, test_currency, test_category
    ):
        """income_diff = p2.income - p1.income (kills XXincomeXX key mutations)."""
        p1 = _make_period(db, test_user.id, "KillIDiff1",
                          date(2032, 1, 1), date(2032, 1, 31), date(2032, 1, 31))
        p2 = _make_period(db, test_user.id, "KillIDiff2",
                          date(2032, 2, 1), date(2032, 2, 28), date(2032, 2, 28))
        _add_income(db, p1.id, test_currency.id, Decimal("1000.00"))
        _add_income(db, p2.id, test_currency.id, Decimal("4000.00"))
        db.commit()

        result = analytics_service.get_period_comparison(db, test_user.id, p1.id, p2.id)

        # income_diff = 4000 - 1000 = 3000 (not 0 if one income key is wrong)
        assert result["differences"]["income_diff"] == 3000.0

    def test_net_diff_key_present(
        self, db: Session, test_user, test_currency, test_category
    ):
        """differences dict must have 'net_diff' key (kills XXnet_diffXX mutation)."""
        p1 = _make_period(db, test_user.id, "KillNetDiff1",
                          date(2032, 3, 1), date(2032, 3, 31), date(2032, 3, 31))
        p2 = _make_period(db, test_user.id, "KillNetDiff2",
                          date(2032, 4, 1), date(2032, 4, 30), date(2032, 4, 30))
        _add_income(db, p1.id, test_currency.id, Decimal("2000.00"))
        _add_income(db, p2.id, test_currency.id, Decimal("3000.00"))
        db.commit()

        result = analytics_service.get_period_comparison(db, test_user.id, p1.id, p2.id)

        assert "net_diff" in result["differences"]


class TestKillMutantsRecurringAndAnomalies:

    def test_exactly_5_occurrences_is_medium_confidence(
        self, db: Session, test_user, test_currency
    ):
        """5 occurrences = 'medium' confidence (> 5, not >= 5) (kills > → >=)."""
        cat = _make_category(db, test_user.id, "KillConf5")
        for i in range(5):
            p = _make_period(db, test_user.id, f"KillConf5P{i}",
                             date(2032, 5, 1 + i), date(2032, 5, 1 + i),
                             date(2032, 5, 1 + i))
            _add_expense(db, p.id, cat.id, test_currency.id, Decimal("50.00"), "Conf5Item")
        db.commit()

        patterns = analytics_service.detect_recurring_patterns(db, test_user.id)

        item = next((p for p in patterns if p["item_name"] == "Conf5Item"), None)
        assert item is not None
        assert item["confidence"] == "medium"  # 5 is NOT > 5

    def test_exactly_6_occurrences_is_high_confidence(
        self, db: Session, test_user, test_currency
    ):
        """6 occurrences = 'high' confidence (r.occurrences > 5) — boundary confirmation."""
        cat = _make_category(db, test_user.id, "KillConf6")
        for i in range(6):
            p = _make_period(db, test_user.id, f"KillConf6P{i}",
                             date(2032, 6, 1 + i), date(2032, 6, 1 + i),
                             date(2032, 6, 1 + i))
            _add_expense(db, p.id, cat.id, test_currency.id, Decimal("50.00"), "Conf6Item")
        db.commit()

        patterns = analytics_service.detect_recurring_patterns(db, test_user.id)

        item = next((p for p in patterns if p["item_name"] == "Conf6Item"), None)
        assert item is not None
        assert item["confidence"] == "high"

    def test_anomaly_exactly_2_5x_not_flagged(
        self, db: Session, test_user, test_currency
    ):
        """Expense exactly 2.5x average is NOT flagged (> 2.5, not >=) (kills > → >=)."""
        cat = _make_category(db, test_user.id, "KillAno25x")
        p_hist = _make_period(db, test_user.id, "KillAno25Hist",
                              date(2032, 7, 1), date(2032, 7, 31), date(2032, 7, 31),
                              status="FINALIZED")
        p_curr = _make_period(db, test_user.id, "KillAno25Curr",
                              date(2032, 8, 1), date(2032, 8, 31), date(2032, 8, 31),
                              status="DRAFT")
        _add_expense(db, p_hist.id, cat.id, test_currency.id, Decimal("100.00"), "Hist")
        # exactly 2.5x = 250. Should NOT be flagged (> 2.5, not >=)
        _add_expense(db, p_curr.id, cat.id, test_currency.id, Decimal("250.00"), "Exact25x")
        db.commit()

        anomalies = analytics_service.detect_anomalies(db, test_user.id, p_curr.id)

        names = [a["item_name"] for a in anomalies]
        assert "Exact25x" not in names  # 250 is NOT > 2.5*100

    def test_anomaly_type_and_message_keys_present(
        self, db: Session, test_user, test_currency
    ):
        """Anomaly dict must have 'type' and 'message' keys (kills XX key mutations)."""
        cat = _make_category(db, test_user.id, "KillAnoKeys")
        p_hist = _make_period(db, test_user.id, "KillAnoKeysHist",
                              date(2032, 9, 1), date(2032, 9, 30), date(2032, 9, 30),
                              status="FINALIZED")
        p_curr = _make_period(db, test_user.id, "KillAnoKeysCurr",
                              date(2032, 10, 1), date(2032, 10, 31), date(2032, 10, 31),
                              status="DRAFT")
        _add_expense(db, p_hist.id, cat.id, test_currency.id, Decimal("100.00"), "Baseline")
        _add_expense(db, p_curr.id, cat.id, test_currency.id, Decimal("400.00"), "BigOne")
        db.commit()

        anomalies = analytics_service.detect_anomalies(db, test_user.id, p_curr.id)

        assert len(anomalies) == 1
        assert "type" in anomalies[0]
        assert "message" in anomalies[0]
        assert anomalies[0]["type"] == "LARGE_EXPENSE"
