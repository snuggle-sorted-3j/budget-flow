from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import income as crud_income
from app.crud import period as crud_period
from app.crud import currency as crud_currency
from app.models.user import User
from app.schemas.income import IncomeCreate, IncomeResponse, IncomeUpdate

router = APIRouter()


@router.post("/periods/{period_id}/incomes", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
def create_income(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    income_in: IncomeCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new income entry in a period.
    """
    # Verify period belongs to user
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    # Verify currency belongs to user
    currency = crud_currency.get_currency_by_id(db=db, user_id=current_user.id, currency_id=income_in.currency_id)
    if not currency:
        raise HTTPException(status_code=400, detail="Currency not found or access denied")

    return crud_income.create_income(db=db, period_id=period_id, data=income_in)


@router.get("/periods/{period_id}/incomes", response_model=List[IncomeResponse])
def read_incomes(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve income entries for a period.
    """
    # Verify period belongs to user
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
        
    return crud_income.list_incomes_for_period(db=db, period_id=period_id)


@router.patch("/incomes/{income_id}", response_model=IncomeResponse)
def update_income(
    *,
    db: Session = Depends(deps.get_db),
    income_id: UUID,
    income_in: IncomeUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update an income entry.
    """
    income = crud_income.get_income(db=db, income_id=income_id)
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")

    # Verify period belongs to user
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=income.calculation_period_id)
    if not period:
        raise HTTPException(status_code=403, detail="Not authorized to update this income")

    # If currency is changing, verify it
    if income_in.currency_id:
        currency = crud_currency.get_currency_by_id(db=db, user_id=current_user.id, currency_id=income_in.currency_id)
        if not currency:
            raise HTTPException(status_code=400, detail="Currency not found or access denied")

    return crud_income.update_income(db=db, db_obj=income, obj_in=income_in)


@router.delete("/incomes/{income_id}", status_code=status.HTTP_200_OK)
def delete_income_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    income_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete an income entry.
    """
    # Verify existence and permissions (indirectly by period ownership or direct fetch)
    income = crud_income.get_income(db=db, income_id=income_id)
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
        
    # Verify period belongs to user to authorize deletion
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=income.calculation_period_id)
    if not period:
        raise HTTPException(status_code=403, detail="Not authorized to delete this income")
        
    crud_income.delete_income(db=db, income_id=income_id)
    return {"message": "Income deleted successfully"}
