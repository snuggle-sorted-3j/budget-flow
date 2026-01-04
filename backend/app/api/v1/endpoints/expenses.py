from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import expense as crud_expense
from app.crud import period as crud_period
from app.crud import currency as crud_currency
from app.crud import expense_category as crud_category
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseResponse

router = APIRouter()


@router.post("/periods/{period_id}/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    expense_in: ExpenseCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new expense entry in a period.
    """
    # Verify period belongs to user
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    # Verify category belongs to user
    category = crud_category.get_category(db=db, user_id=current_user.id, category_id=expense_in.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Category not found or access denied")

    # Verify currency belongs to user
    currency = crud_currency.get_currency(db=db, user_id=current_user.id, currency_id=expense_in.currency_id)
    if not currency:
        raise HTTPException(status_code=400, detail="Currency not found or access denied")

    return crud_expense.create_expense(db=db, period_id=period_id, data=expense_in)


@router.get("/periods/{period_id}/expenses", response_model=List[ExpenseResponse])
def read_expenses(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve expense entries for a period.
    """
    # Verify period belongs to user
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
        
    return crud_expense.list_expenses_for_period(db=db, period_id=period_id)
