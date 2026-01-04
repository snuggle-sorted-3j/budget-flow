from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import currency as crud_currency
from app.models.user import User
from app.schemas.currency import CurrencyCreate, CurrencyResponse

router = APIRouter()


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
