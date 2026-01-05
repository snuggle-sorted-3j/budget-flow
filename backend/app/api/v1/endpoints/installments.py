from typing import Any, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import installment as crud_installment
from app.models.user import User
from app.models.installment_item import InstallmentItem
from app.models.installment_payment import InstallmentPayment
from app.models.calculation_period import CalculationPeriod
from app.schemas.installment import (
    InstallmentItemCreate,
    InstallmentItemResponse,
    InstallmentItemUpdate,
    InstallmentPaymentCreate,
    InstallmentPaymentResponse,
)

router = APIRouter()

@router.post("/items", response_model=InstallmentItemResponse)
def create_installment_item(
    item_in: InstallmentItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Create a new installment item."""
    return crud_installment.create_installment_item(db, current_user.id, item_in)

@router.get("/items", response_model=List[InstallmentItemResponse])
def get_installment_items(
    status: str | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get all installment items (optionally filtered by status)."""
    items = crud_installment.get_installment_items(db, current_user.id, status)
    # Populate currency ticker if needed, but pydantic schema handles basic fields.
    # currency_ticker is not in model, so might be None unless we eagerly load or map it.
    # Let's simple-map it here for UI convenience if model doesn't have it property.
    for item in items:
        if item.currency:
            item.currency_ticker = item.currency.ticker
    return items

@router.patch("/items/{item_id}", response_model=InstallmentItemResponse)
def patch_installment_item(
    item_id: UUID,
    item_update: InstallmentItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Update an installment item."""
    item = crud_installment.get_installment_item(db, item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Installment item not found")
        
    return crud_installment.update_installment_item(db, item, item_update)

@router.get("/items/{item_id}/payments", response_model=List[InstallmentPaymentResponse])
def get_installment_payments(
    item_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get payments for a specific item."""
    item = crud_installment.get_installment_item(db, item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Installment item not found")
        
    payments = crud_installment.get_installment_payments(db, item_id)
    # Map period name
    for p in payments:
        if p.period:
             p.period_name = p.period.period_name
    return payments

@router.post("/items/{item_id}/payments", response_model=InstallmentPaymentResponse)
def create_installment_payment(
    item_id: UUID,
    payment_in: InstallmentPaymentCreate,
    period_id: UUID,  # Passed as query param or part of body? Let's use Query for consistency with other parts or Body?
                      # Schema doesn't have period_id. So Query param.
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Add a payment to an installment item."""
    item = crud_installment.get_installment_item(db, item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Installment item not found")
        
    period = db.get(CalculationPeriod, period_id)
    if not period or period.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Period not found")

    payment = crud_installment.create_installment_payment(db, item_id, period_id, payment_in)
    return payment

@router.delete("/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_installment_payment(
    payment_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Delete a payment and revert balance."""
    payment = db.get(InstallmentPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    # Verify ownership via item
    if payment.installment_item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    crud_installment.delete_installment_payment(db, payment)
    return None
