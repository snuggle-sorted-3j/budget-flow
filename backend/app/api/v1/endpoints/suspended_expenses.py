from typing import Any, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import suspended_expense as crud_suspended
from app.crud import expense as crud_expense
from app.models.user import User
from app.models.suspended_expense import SuspendedExpense
from app.models.calculation_period import CalculationPeriod
from app.schemas.suspended_expense import (
    SuspendedExpenseCreate,
    SuspendedExpenseResponse,
    SuspendedExpenseUpdate,
)
from app.schemas.expense import ExpenseCreate

router = APIRouter()

@router.post("/{period_id}", response_model=SuspendedExpenseResponse)
def create_suspended_expense(
    period_id: UUID,
    expense_in: SuspendedExpenseCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Create new suspended expense in a specific period."""
    period = db.get(CalculationPeriod, period_id)
    if not period or period.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Period not found")
        
    return crud_suspended.create_suspended_expense(db, current_user.id, period_id, expense_in)

@router.get("/", response_model=List[SuspendedExpenseResponse])
def get_suspended_expenses(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get all suspended expenses."""
    expenses = crud_suspended.get_suspended_expenses(db, current_user.id)
    for exp in expenses:
        if exp.currency:
             # Pydantic validation handles this if model fields match, but for loose properties:
             # We might need to map currency_ticker manualy if not compatible with from_attributes=True auto-mapping
             pass
    return expenses

@router.patch("/{expense_id}/settle/{period_id}", response_model=SuspendedExpenseResponse)
def settle_suspended_expense(
    expense_id: UUID,
    period_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Mark a suspended expense as SETTLED in a specific period (money returned)."""
    expense = crud_suspended.get_suspended_expense(db, expense_id)
    if not expense or expense.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Suspended expense not found")
        
    period = db.get(CalculationPeriod, period_id)
    if not period or period.user_id != current_user.id:
         raise HTTPException(status_code=404, detail="Period not found")

    if expense.status != "PENDING":
        raise HTTPException(status_code=400, detail="Expense is not pending")

    update_in = SuspendedExpenseUpdate(
        status="SETTLED",
        settled_period_id=period_id
    )
    return crud_suspended.update_suspended_expense(db, expense, update_in)

@router.patch("/{expense_id}/convert", status_code=status.HTTP_204_NO_CONTENT)
def convert_suspended_to_expense(
    expense_id: UUID,
    period_id: UUID, # Period to create expense in (usually current)
    category_id: UUID, # Needed for expense creation
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Convert suspended expense to actual expense (money lost/spent)."""
    expense = crud_suspended.get_suspended_expense(db, expense_id)
    if not expense or expense.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Suspended expense not found")

    if expense.status != "PENDING":
        raise HTTPException(status_code=400, detail="Expense is not pending")
    
    # Check period validity
    period = db.get(CalculationPeriod, period_id)
    if not period or period.user_id != current_user.id:
         raise HTTPException(status_code=404, detail="Period not found")

    # Create Expense
    expense_create = ExpenseCreate(
        item_name=expense.item_name,
        amount=expense.amount,
        currency_id=expense.currency_id,
        category_id=category_id,
        expense_date=date.today(), # Default to today or period start? Let's use today.
        is_tax_deductible=False,
        notes=f"Converted from suspended: {expense.notes or ''}"
    )
    crud_expense.create_expense_item(db, period_id, expense_create)
    
    # Mark suspended as converted
    update_in = SuspendedExpenseUpdate(status="CONVERTED_TO_EXPENSE")
    crud_suspended.update_suspended_expense(db, expense, update_in)
    
    return None

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_suspended_expense(
    expense_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Delete a suspended expense."""
    expense = crud_suspended.get_suspended_expense(db, expense_id)
    if not expense or expense.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Maybe restrict deletion if already settled?
    # User said "delete functionality...". Let's allow it but maybe warn?
    # Standard logic: if it exists, delete it.
    
    crud_suspended.delete_suspended_expense(db, expense)
    return None
