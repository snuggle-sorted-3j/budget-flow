from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import currency as crud_currency
from app.models.user import User
from app.schemas.currency import CurrencyCreate, CurrencyResponse

router = APIRouter()


@router.post("/initialize", response_model=List[CurrencyResponse], status_code=status.HTTP_201_CREATED)
def initialize_currencies(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Initialize a default set of currencies for the current user.
    """
    crud_currency.initialize_default_currencies(db, current_user.id)
    return crud_currency.list_currencies(db, current_user.id)


@router.post("/", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED)
def create_currency(
    *,
    db: Session = Depends(deps.get_db),
    currency_in: CurrencyCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new currency.
    """
    return crud_currency.create_currency(db=db, user_id=current_user.id, data=currency_in)


@router.get("/", response_model=List[CurrencyResponse])
def read_currencies(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve user's currencies.
    """
    return crud_currency.list_currencies(db=db, user_id=current_user.id)


@router.get("/{currency_id}", response_model=CurrencyResponse)
def read_currency(
    *,
    db: Session = Depends(deps.get_db),
    currency_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific currency.
    """
    currency = crud_currency.get_currency_by_id(db=db, user_id=current_user.id, currency_id=currency_id)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currency not found",
        )
    return currency


@router.patch("/{currency_id}/set-default", response_model=CurrencyResponse)
def set_default_currency(
    *,
    db: Session = Depends(deps.get_db),
    currency_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Set a currency as the user's default.
    """
    currency = crud_currency.set_default_currency(db=db, user_id=current_user.id, currency_id=currency_id)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currency not found",
        )
    return currency


@router.delete("/{currency_id}", response_model=CurrencyResponse)
def delete_currency(
    *,
    db: Session = Depends(deps.get_db),
    currency_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a currency.
    """
    currency = crud_currency.delete_currency(db=db, user_id=current_user.id, currency_id=currency_id)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currency not found",
        )
    return currency
