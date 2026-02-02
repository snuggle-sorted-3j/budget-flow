import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services import analytics_service

router = APIRouter()


@router.get("/spending-by-category")
def get_spending_by_category(
    period_id: Optional[uuid.UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """Get spending by category data for visualizations."""
    return analytics_service.get_spending_by_category(
        db, current_user.id, period_id=period_id, start_date=start_date, end_date=end_date
    )


@router.get("/income-vs-expenses")
def get_income_vs_expenses(
    num_periods: int = Query(6, ge=1, le=24),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """Get income vs expenses trend data."""
    return analytics_service.get_income_vs_expenses_trend(
        db, current_user.id, num_periods=num_periods
    )


@router.get("/top-expenses")
def get_top_expenses(
    period_id: Optional[uuid.UUID] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """Get largest individual expense items."""
    return analytics_service.get_top_expenses(
        db, current_user.id, period_id=period_id, limit=limit
    )


@router.get("/net-worth-trend")
def get_net_worth_trend(
    num_periods: int = Query(12, ge=1, le=60),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """Get net worth progression data."""
    return analytics_service.get_net_worth_trend(
        db, current_user.id, num_periods=num_periods
    )


@router.get("/category-trends/{category_id}")
def get_category_trends(
    category_id: uuid.UUID,
    num_periods: int = Query(6, ge=1, le=24),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """Track single category spending over time."""
    data = analytics_service.get_category_trends(
        db, current_user.id, category_id=category_id, num_periods=num_periods
    )
    if not data:
        raise HTTPException(status_code=404, detail="Category not found")
    return data


@router.get("/compare-periods")
def compare_periods(
    period_id_1: uuid.UUID,
    period_id_2: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """Compare two periods side-by-side."""
    data = analytics_service.get_period_comparison(
        db, current_user.id, period_id_1, period_id_2
    )
    if not data:
        raise HTTPException(status_code=404, detail="One or both periods not found")
    return data

@router.get("/recurring-patterns")
def get_recurring_patterns(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """Detect recurring expense patterns."""
    return analytics_service.detect_recurring_patterns(db, current_user.id)


@router.get("/anomalies")
def get_anomalies(
    period_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """Flag unusual spending in a period."""
    return analytics_service.detect_anomalies(db, current_user.id, period_id)
