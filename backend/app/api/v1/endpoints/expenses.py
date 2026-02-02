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
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate

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
    currency = crud_currency.get_currency_by_id(db=db, user_id=current_user.id, currency_id=expense_in.currency_id)
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


@router.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    *,
    db: Session = Depends(deps.get_db),
    expense_id: UUID,
    expense_in: ExpenseUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update an expense entry.
    """
    expense = crud_expense.get_expense(db=db, expense_id=expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Verify period belongs to user
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=expense.calculation_period_id)
    if not period:
        raise HTTPException(status_code=403, detail="Not authorized to update this expense")

    # If category or currency changing, verify them
    if expense_in.category_id:
        category = crud_category.get_category(db=db, user_id=current_user.id, category_id=expense_in.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found or access denied")
            
    if expense_in.currency_id:
        currency = crud_currency.get_currency_by_id(db=db, user_id=current_user.id, currency_id=expense_in.currency_id)
        if not currency:
            raise HTTPException(status_code=400, detail="Currency not found or access denied")

    return crud_expense.update_expense(db=db, db_obj=expense, obj_in=expense_in)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_200_OK)
def delete_expense_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    expense_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete an expense entry.
    """
    # Verify existence
    expense = crud_expense.get_expense(db=db, expense_id=expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    # Verify period belongs to user to authorize deletion
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=expense.calculation_period_id)
    if not period:
        raise HTTPException(status_code=403, detail="Not authorized to delete this expense")
        
    crud_expense.delete_expense(db=db, expense_id=expense_id)
    return {"message": "Expense deleted successfully"}
