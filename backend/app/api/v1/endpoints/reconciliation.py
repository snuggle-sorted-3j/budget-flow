from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import period as crud_period
from app.models.currency import Currency as CurrencyModel
from app.models.expense_category import ExpenseCategory
from app.models.user import User
from app.schemas.expense import ExpenseResponse
from app.schemas.reconciliation import PeriodReconciliation, TaxBenefitsResult
from app.services import reconciliation_service


class QuickBalanceRequest(BaseModel):
    currency_ticker: str

router = APIRouter()


@router.get("/periods/{period_id}/reconciliation", response_model=PeriodReconciliation)
def get_reconciliation(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get reconciliation summary for a period.
    """
    result = reconciliation_service.calculate_reconciliation(
        db=db, user_id=current_user.id, period_id=period_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not found",
        )
    return result


@router.patch("/periods/{period_id}/finalize", response_model=PeriodReconciliation)
def finalize_period(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Finalize a period if it is balanced.
    """
    # 1. Check if period exists and isn't already finalized
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not found",
        )
    
    if period.status == "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period is already finalized",
        )

    # 2. Calculate reconciliation
    result = reconciliation_service.calculate_reconciliation(
        db=db, user_id=current_user.id, period_id=period_id
    )
    
    # 3. Check if balanced
    if not result.overall_balanced:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=jsonable_encoder({
                "message": "Cannot finalize: Period is not balanced across all currencies",
                "reconciliation": result.model_dump()
            }),
        )

    # 4. Update status
    crud_period.update_period_status(db=db, user_id=current_user.id, period_id=period_id, status="FINALIZED")

    # Return updated result
    result.status = "FINALIZED"
    return result


@router.get("/periods/{period_id}/tax-benefits", response_model=TaxBenefitsResult, response_model_exclude_none=True)
def get_tax_benefits(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Calculate tax benefits for a period based on user's tax system settings.

    Returns 204 when tax_system is NONE or user has no settings configured.
    Returns 404 when the period does not exist.
    """
    # Verify period exists and belongs to user
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not found",
        )

    result = reconciliation_service.calculate_tax_benefits(
        db=db, user_id=current_user.id, period_id=period_id
    )
    if result is None:
        # No active tax system — return 204 No Content
        from fastapi.responses import Response
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # Convert deductible_items list of dicts to list of DeductibleItem instances
    from app.schemas.reconciliation import DeductibleItem
    result["deductible_items"] = [DeductibleItem(**item) for item in result["deductible_items"]]
    return TaxBenefitsResult(**result)


@router.post("/periods/{period_id}/quick-balance", response_model=ExpenseResponse)
def quick_balance(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    body: QuickBalanceRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Auto-create an 'Untracked Expenses' entry to close the reconciliation gap.

    Calculates the difference for the requested currency and creates an expense
    in the system 'Untracked Expenses' category. Returns 400 if already balanced.
    """
    from app.crud import expense as crud_expense
    from app.schemas.expense import ExpenseCreate

    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Period not found")

    if period.status == "FINALIZED":
        raise HTTPException(status_code=400, detail="Cannot quick-balance a finalized period")

    # Calculate current reconciliation
    recon = reconciliation_service.calculate_reconciliation(
        db=db, user_id=current_user.id, period_id=period_id
    )
    if not recon:
        raise HTTPException(status_code=404, detail="Period not found")

    # Find the requested currency summary
    summary = next(
        (s for s in recon.reconciliations if s.currency_ticker == body.currency_ticker),
        None,
    )
    if not summary:
        raise HTTPException(status_code=400, detail=f"Currency '{body.currency_ticker}' not found in reconciliation")

    difference = summary.difference  # expected - actual; positive = too much expected → add expense
    if difference == 0:
        raise HTTPException(status_code=400, detail="Period is already balanced for this currency")

    # The gap to fill: if difference > 0 we have more expected than actual → add expense of 'difference'
    # if difference < 0 we have less expected → would need income; quick-balance only covers expenses
    if difference < 0:
        raise HTTPException(
            status_code=400,
            detail="Positive balance gap requires adding income, not an untracked expense"
        )

    # Get currency
    currency = db.execute(
        select(CurrencyModel).where(
            CurrencyModel.user_id == current_user.id,
            CurrencyModel.ticker == body.currency_ticker,
        )
    ).scalar_one_or_none()
    if not currency:
        raise HTTPException(status_code=400, detail="Currency not found")

    # Find (or create) 'Untracked Expenses' system category for this user
    untracked_cat = db.execute(
        select(ExpenseCategory).where(
            ExpenseCategory.user_id == current_user.id,
            ExpenseCategory.is_system_category == True,  # noqa: E712
            ExpenseCategory.category_name == "Untracked Expenses",
        )
    ).scalar_one_or_none()

    if not untracked_cat:
        untracked_cat = ExpenseCategory(
            user_id=current_user.id,
            category_name="Untracked Expenses",
            is_system_category=True,
            icon="❓",
            sort_order=99,
        )
        db.add(untracked_cat)
        db.flush()

    expense_data = ExpenseCreate(
        item_name="Untracked Expenses",
        amount=difference,
        currency_id=currency.id,
        category_id=untracked_cat.id,
    )
    return crud_expense.create_expense(db=db, period_id=period_id, data=expense_data)
