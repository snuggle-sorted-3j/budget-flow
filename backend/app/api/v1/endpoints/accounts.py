from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import account as crud_account
from app.crud import currency as crud_currency
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse

router = APIRouter()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    *,
    db: Session = Depends(deps.get_db),
    account_in: AccountCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new account.
    """
    # Ensure currency exists and belongs to user
    currency = crud_currency.get_currency_by_id(db=db, user_id=current_user.id, currency_id=account_in.currency_id)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency not found or access denied",
        )
    
    try:
        account = crud_account.create_account(db=db, user_id=current_user.id, data=account_in)
        return account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=List[AccountResponse])
def read_accounts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve user's accounts.
    """
    return crud_account.list_accounts(db=db, user_id=current_user.id)


@router.patch("/{account_id}/deactivate", response_model=AccountResponse)
def deactivate_account(
    *,
    db: Session = Depends(deps.get_db),
    account_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Deactivate an account.
    """
    account = crud_account.deactivate_account(db=db, user_id=current_user.id, account_id=account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


@router.delete("/{account_id}")
def delete_account(
    *,
    db: Session = Depends(deps.get_db),
    account_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete an account.
    """
    try:
        success = crud_account.delete_account(db=db, user_id=current_user.id, account_id=account_id)
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        return {"message": "Account deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
