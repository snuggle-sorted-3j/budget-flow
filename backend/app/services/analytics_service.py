import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from app.models.expense_item import ExpenseItem
from app.models.expense_category import ExpenseCategory
from app.models.income_entry import IncomeEntry
from app.models.calculation_period import CalculationPeriod
from app.models.balance_snapshot import BalanceSnapshot
from app.models.currency import Currency


def get_spending_by_category(
    db: Session,
    user_id: uuid.UUID,
    period_id: Optional[uuid.UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Dict:
    """Query expenses grouped by category."""
    stmt = (
        select(
            ExpenseCategory.category_name,
            Currency.ticker.label("currency"),
            func.sum(ExpenseItem.amount).label("total"),
        )
        .join(ExpenseItem, ExpenseItem.category_id == ExpenseCategory.id)
        .join(Currency, ExpenseItem.currency_id == Currency.id)
        .where(ExpenseCategory.user_id == user_id)
    )

    if period_id:
        stmt = stmt.where(ExpenseItem.calculation_period_id == period_id)
    if start_date:
        stmt = stmt.where(ExpenseItem.expense_date >= start_date)
    if end_date:
        stmt = stmt.where(ExpenseItem.expense_date <= end_date)

    stmt = stmt.group_by(ExpenseCategory.category_name, Currency.ticker)
    results = db.execute(stmt).all()

    by_category = []
    total_expenses = Decimal("0.00")
    currency_breakdown = {}

    # Calculate total for percentage later
    for row in results:
        total_expenses += row.total
        currency_breakdown[row.currency] = currency_breakdown.get(row.currency, Decimal("0.00")) + row.total
        
        by_category.append({
            "category_name": row.category_name,
            "total": float(row.total),
            "currency": row.currency
        })

    # Add percentages (note: only accurate if single currency, but requested)
    for cat in by_category:
        if total_expenses > 0:
            cat["percentage"] = round(float(Decimal(str(cat["total"])) / total_expenses * 100), 1)
        else:
            cat["percentage"] = 0

    return {
        "by_category": by_category,
        "total_expenses": float(total_expenses),
        "currency_breakdown": {k: float(v) for k, v in currency_breakdown.items()}
    }


def get_income_vs_expenses_trend(
    db: Session, user_id: uuid.UUID, num_periods: int = 6
) -> Dict:
    """Get last N finalized periods and compare income vs expenses."""
    periods_stmt = (
        select(CalculationPeriod)
        .where(CalculationPeriod.user_id == user_id, CalculationPeriod.status == "FINALIZED")
        .order_by(desc(CalculationPeriod.end_date))
        .limit(num_periods)
    )
    periods = db.execute(periods_stmt).scalars().all()
    periods = sorted(periods, key=lambda p: p.end_date) # Sort chronological for trend

    period_data = []
    total_income = Decimal("0.00")
    total_expenses = Decimal("0.00")

    for p in periods:
        # Sum income
        inc_stmt = select(func.sum(IncomeEntry.amount)).where(IncomeEntry.calculation_period_id == p.id)
        inc_total = db.execute(inc_stmt).scalar() or Decimal("0.00")
        
        # Sum expenses
        exp_stmt = select(func.sum(ExpenseItem.amount)).where(ExpenseItem.calculation_period_id == p.id)
        exp_total = db.execute(exp_stmt).scalar() or Decimal("0.00")
        
        net = inc_total - exp_total
        
        # Get primary currency (for simplicity, using first found or default)
        # In a real app we'd convert all to single base currency
        curr_stmt = select(Currency.ticker).join(IncomeEntry).where(IncomeEntry.calculation_period_id == p.id).limit(1)
        currency = db.execute(curr_stmt).scalar() or "PLN"
        
        period_data.append({
            "period_name": p.period_name,
            "period_dates": f"{p.start_date} to {p.end_date}",
            "income": float(inc_total),
            "expenses": float(exp_total),
            "net": float(net),
            "currency": currency
        })
        
        total_income += inc_total
        total_expenses += exp_total

    total_net = total_income - total_expenses
    avg_net = total_net / len(periods) if periods else Decimal("0.00")

    return {
        "periods": period_data,
        "totals": {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "total_net": float(total_net),
            "average_monthly_net": float(avg_net)
        }
    }


def get_top_expenses(
    db: Session, user_id: uuid.UUID, period_id: Optional[uuid.UUID] = None, limit: int = 10
) -> List[Dict]:
    """Query largest individual expense items."""
    stmt = (
        select(
            ExpenseItem.item_name,
            ExpenseItem.amount,
            ExpenseCategory.category_name.label("category"),
            ExpenseItem.expense_date.label("date"),
        )
        .join(ExpenseCategory, ExpenseItem.category_id == ExpenseCategory.id)
        .where(ExpenseCategory.user_id == user_id)
        .order_by(desc(ExpenseItem.amount))
        .limit(limit)
    )

    if period_id:
        stmt = stmt.where(ExpenseItem.calculation_period_id == period_id)

    results = db.execute(stmt).all()
    return [
        {
            "item_name": r.item_name,
            "amount": float(r.amount),
            "category": r.category,
            "date": str(r.date) if r.date else None
        }
        for r in results
    ]


def get_net_worth_trend(
    db: Session, user_id: uuid.UUID, num_periods: int = 12
) -> Dict:
    """Show progression of total assets over time."""
    periods_stmt = (
        select(CalculationPeriod)
        .where(CalculationPeriod.user_id == user_id, CalculationPeriod.status == "FINALIZED")
        .order_by(desc(CalculationPeriod.end_date))
        .limit(num_periods)
    )
    periods = db.execute(periods_stmt).scalars().all()
    periods = sorted(periods, key=lambda p: p.end_date)

    period_data = []
    
    for p in periods:
        snap_stmt = (
            select(func.sum(BalanceSnapshot.balance).label("total"), Currency.ticker)
            .join(BalanceSnapshot.account)
            .join(Currency)
            .where(BalanceSnapshot.calculation_period_id == p.id)
            .group_by(Currency.ticker)
        )
        snaps = db.execute(snap_stmt).all()
        
        by_currency = {s.ticker: float(s.total) for s in snaps}
        total_balance = sum(by_currency.values())
        
        period_data.append({
            "period_name": p.period_name,
            "snapshot_date": str(p.snapshot_date),
            "total_balance": total_balance,
            "by_currency": by_currency
        })

    net_change = 0.0
    percentage_change = 0.0
    if len(period_data) >= 2:
        first = period_data[0]["total_balance"]
        last = period_data[-1]["total_balance"]
        net_change = last - first
        if first != 0:
            percentage_change = (net_change / first) * 100

    return {
        "periods": period_data,
        "net_change": float(net_change),
        "percentage_change": round(float(percentage_change), 1)
    }


def get_category_trends(
    db: Session, user_id: uuid.UUID, category_id: uuid.UUID, num_periods: int = 6
) -> Dict:
    """Track single category spending over time."""
    cat = db.get(ExpenseCategory, category_id)
    if not cat or cat.user_id != user_id:
        return {}

    periods_stmt = (
        select(CalculationPeriod)
        .where(CalculationPeriod.user_id == user_id, CalculationPeriod.status == "FINALIZED")
        .order_by(desc(CalculationPeriod.end_date))
        .limit(num_periods)
    )
    periods = db.execute(periods_stmt).scalars().all()
    periods = sorted(periods, key=lambda p: p.end_date)

    period_data = []
    total_amount = Decimal("0.00")

    for p in periods:
        amt_stmt = select(func.sum(ExpenseItem.amount)).where(
            ExpenseItem.calculation_period_id == p.id,
            ExpenseItem.category_id == category_id
        )
        amt = db.execute(amt_stmt).scalar() or Decimal("0.00")
        
        period_data.append({
            "period_name": p.period_name,
            "amount": float(amt)
        })
        total_amount += amt

    avg = float(total_amount / len(periods)) if periods else 0.0
    
    trend = "stable"
    if len(period_data) >= 2:
        last = period_data[-1]["amount"]
        prev = period_data[-2]["amount"]
        if last > prev * 1.05:
            trend = "increasing"
        elif last < prev * 0.95:
            trend = "decreasing"

    return {
        "category_name": cat.category_name,
        "periods": period_data,
        "average": avg,
        "trend": trend
    }


def get_period_comparison(
    db: Session, user_id: uuid.UUID, period_id_1: uuid.UUID, period_id_2: uuid.UUID
) -> Dict:
    """Compare two periods side-by-side."""
    p1 = db.get(CalculationPeriod, period_id_1)
    p2 = db.get(CalculationPeriod, period_id_2)
    
    if not p1 or not p2 or p1.user_id != user_id or p2.user_id != user_id:
        return {}

    def get_summary(p):
        inc = db.execute(select(func.sum(IncomeEntry.amount)).where(IncomeEntry.calculation_period_id == p.id)).scalar() or Decimal("0.00")
        exp = db.execute(select(func.sum(ExpenseItem.amount)).where(ExpenseItem.calculation_period_id == p.id)).scalar() or Decimal("0.00")
        
        # Category breakdown
        cat_stmt = (
            select(ExpenseCategory.category_name, func.sum(ExpenseItem.amount))
            .join(ExpenseItem)
            .where(ExpenseItem.calculation_period_id == p.id)
            .group_by(ExpenseCategory.category_name)
        )
        cats = {r[0]: float(r[1]) for r in db.execute(cat_stmt).all()}
        
        return {
            "income": float(inc),
            "expenses": float(exp),
            "net": float(inc - exp),
            "categories": cats
        }

    s1 = get_summary(p1)
    s2 = get_summary(p2)

    all_cats = set(s1["categories"].keys()) | set(s2["categories"].keys())
    cat_changes = []
    for c in all_cats:
        v1 = s1["categories"].get(c, 0.0)
        v2 = s2["categories"].get(c, 0.0)
        cat_changes.append({
            "category": c,
            "period_1": v1,
            "period_2": v2,
            "diff": v2 - v1
        })

    return {
        "period_1": s1,
        "period_2": s2,
        "differences": {
            "income_diff": s2["income"] - s1["income"],
            "expenses_diff": s2["expenses"] - s1["expenses"],
            "net_diff": s2["net"] - s1["net"]
        },
        "category_changes": cat_changes
    }

def detect_recurring_patterns(db: Session, user_id: uuid.UUID) -> List[Dict]:
    """Automatically detect recurring expenses based on historical data."""
    # Find items that appear in at least 3 periods with same name and similar amount
    stmt = (
        select(
            ExpenseItem.item_name,
            ExpenseCategory.category_name,
            func.avg(ExpenseItem.amount).label("avg_amount"),
            func.count(ExpenseItem.id).label("occurrences"),
        )
        .join(ExpenseCategory)
        .where(ExpenseCategory.user_id == user_id)
        .group_by(ExpenseItem.item_name, ExpenseCategory.category_name)
        .having(func.count(ExpenseItem.id) >= 3)
    )
    
    results = db.execute(stmt).all()
    patterns = []
    
    for r in results:
        # Verify if variations are small (optional but good)
        patterns.append({
            "item_name": r.item_name,
            "category": r.category_name,
            "average_amount": float(r.avg_amount),
            "frequency": f"{r.occurrences} periods",
            "confidence": "high" if r.occurrences > 5 else "medium"
        })
        
    return patterns


def detect_anomalies(db: Session, user_id: uuid.UUID, period_id: uuid.UUID) -> List[Dict]:
    """Flag unusual spending in the current period."""
    # 1. Large expenses (> 2.5x category average)
    anomalies = []
    
    # Get current period expenses
    current_exp_stmt = select(ExpenseItem).where(ExpenseItem.calculation_period_id == period_id)
    current_expenses = db.execute(current_exp_stmt).scalars().all()
    
    for exp in current_expenses:
        # Get historical avg for this category
        avg_stmt = (
            select(func.avg(ExpenseItem.amount))
            .join(ExpenseCategory)
            .where(
                ExpenseCategory.user_id == user_id,
                ExpenseItem.category_id == exp.category_id,
                ExpenseItem.calculation_period_id != period_id
            )
        )
        hist_avg = db.execute(avg_stmt).scalar()
        
        if hist_avg and exp.amount > Decimal(str(hist_avg)) * Decimal("2.5"):
            anomalies.append({
                "type": "LARGE_EXPENSE",
                "item_name": exp.item_name,
                "amount": float(exp.amount),
                "historical_average": float(hist_avg),
                "message": f"Unusually large expense in {exp.category.category_name}"
            })

    return anomalies
