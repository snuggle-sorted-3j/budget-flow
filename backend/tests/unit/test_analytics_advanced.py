import pytest
from uuid import uuid4
from datetime import date, timedelta
from decimal import Decimal
from app.services import analytics_service
from app.models.expense_item import ExpenseItem
from app.models.expense_category import ExpenseCategory
from app.models.calculation_period import CalculationPeriod
from app.models.currency import Currency

def test_detect_recurring_patterns(db, test_user):
    # Setup: Create a category
    cat = ExpenseCategory(id=uuid4(), user_id=test_user.id, category_name="Subscription", is_active=True)
    db.add(cat)
    
    # Create a currency
    curr = Currency(id=uuid4(), user_id=test_user.id, ticker="USD", name="Dollar", is_default=True)
    db.add(curr)
    db.commit()
    
    # Create 3 periods
    p1 = CalculationPeriod(id=uuid4(), user_id=test_user.id, period_name="P1", start_date=date(2023, 1, 1), end_date=date(2023, 1, 31), snapshot_date=date(2023, 1, 31), status="FINALIZED")
    p2 = CalculationPeriod(id=uuid4(), user_id=test_user.id, period_name="P2", start_date=date(2023, 2, 1), end_date=date(2023, 2, 28), snapshot_date=date(2023, 2, 28), status="FINALIZED")
    p3 = CalculationPeriod(id=uuid4(), user_id=test_user.id, period_name="P3", start_date=date(2023, 3, 1), end_date=date(2023, 3, 31), snapshot_date=date(2023, 3, 31), status="FINALIZED")
    db.add_all([p1, p2, p3])
    db.commit()
    
    # Add same expense in all periods
    e1 = ExpenseItem(id=uuid4(), category_id=cat.id, calculation_period_id=p1.id, item_name="Netflix", amount=Decimal("40.00"), currency_id=curr.id)
    e2 = ExpenseItem(id=uuid4(), category_id=cat.id, calculation_period_id=p2.id, item_name="Netflix", amount=Decimal("40.00"), currency_id=curr.id)
    e3 = ExpenseItem(id=uuid4(), category_id=cat.id, calculation_period_id=p3.id, item_name="Netflix", amount=Decimal("40.00"), currency_id=curr.id)
    db.add_all([e1, e2, e3])
    db.commit()
    
    patterns = analytics_service.detect_recurring_patterns(db, test_user.id)
    assert len(patterns) == 1
    assert patterns[0]["item_name"] == "Netflix"
    assert patterns[0]["average_amount"] == 40.0

def test_detect_anomalies(db, test_user):
    # Setup
    cat = ExpenseCategory(id=uuid4(), user_id=test_user.id, category_name="Food", is_active=True)
    db.add(cat)
    curr = Currency(id=uuid4(), user_id=test_user.id, ticker="EUR", name="Euro", is_default=False)
    db.add(curr)
    db.commit()
    
    p_hist = CalculationPeriod(id=uuid4(), user_id=test_user.id, period_name="Hist", start_date=date(2023, 1, 1), end_date=date(2023, 1, 31), snapshot_date=date(2023, 1, 31), status="FINALIZED")
    p_curr = CalculationPeriod(id=uuid4(), user_id=test_user.id, period_name="Curr", start_date=date(2023, 2, 1), end_date=date(2023, 2, 28), snapshot_date=date(2023, 2, 28), status="DRAFT")
    db.add_all([p_hist, p_curr])
    db.commit()
    
    # Historical avg = 100
    e_hist = ExpenseItem(id=uuid4(), category_id=cat.id, calculation_period_id=p_hist.id, item_name="Groceries", amount=Decimal("100.00"), currency_id=curr.id)
    # Current = 300 ( > 2.5x historical)
    e_curr = ExpenseItem(id=uuid4(), category_id=cat.id, calculation_period_id=p_curr.id, item_name="Big Feast", amount=Decimal("300.00"), currency_id=curr.id)
    db.add_all([e_hist, e_curr])
    db.commit()
    
    anomalies = analytics_service.detect_anomalies(db, test_user.id, p_curr.id)
    assert len(anomalies) == 1
    assert anomalies[0]["type"] == "LARGE_EXPENSE"
    assert anomalies[0]["amount"] == 300.0
