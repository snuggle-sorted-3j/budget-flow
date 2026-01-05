from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import currency_conversion as crud_conversion
from app.models.user import User
from app.schemas.currency_conversion import (
    CurrencyConversionCreate,
    CurrencyConversionResponse,
    CurrencyConversionUpdate,
)

router = APIRouter()


@router.post("/periods/{period_id}/currency-conversions", response_model=CurrencyConversionResponse)
def create_conversion(
    period_id: UUID,
    conversion_in: CurrencyConversionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Record a new currency conversion."""
    # Logic to check if from_currency != to_currency is already in model CheckConstraint,
    # but let's add it here for cleaner error.
    if conversion_in.from_currency_id == conversion_in.to_currency_id:
        raise HTTPException(status_code=400, detail="From and To currencies must be different.")
        
    return crud_conversion.create_currency_conversion(db, conversion_in, period_id)


@router.get("/periods/{period_id}/currency-conversions", response_model=List[CurrencyConversionResponse])
def get_conversions(
    period_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get all conversions for a period."""
    conversions = crud_conversion.get_currency_conversions(db, period_id)
    # Enrich with tickers/account names for UI
    for c in conversions:
        c.from_currency_ticker = c.from_currency.ticker if c.from_currency else None
        c.to_currency_ticker = c.to_currency.ticker if c.to_currency else None
        c.source_account_name = c.source_account.account_name if c.source_account else None
    return conversions


@router.delete("/currency-conversions/{conversion_id}")
def delete_conversion(
    conversion_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Delete a conversion."""
    conversion = crud_conversion.get_currency_conversion(db, conversion_id)
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    # Check ownership via period -> user? 
    # For now, simplistic check.
    crud_conversion.delete_currency_conversion(db, conversion)
    return {"success": True}
