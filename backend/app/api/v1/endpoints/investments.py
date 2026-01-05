from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import investment as crud_investment
from app.models.user import User
from app.models.investment_account import InvestmentAccount
from app.models.investment import Investment
from app.models.investment_transfer import InvestmentTransfer

# We need these imports for deletions
from app.models.expense_item import ExpenseItem 

from app.schemas.investment import (
    InvestmentAccountCreate,
    InvestmentAccountResponse,
    InvestmentCreate,
    InvestmentResponse,
    InvestmentTransferCreate,
    InvestmentTransferResponse,
)

router = APIRouter()

# --- Investment Accounts ---
@router.post("/accounts", response_model=InvestmentAccountResponse)
def create_investment_account(
    account_in: InvestmentAccountCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Create new investment account."""
    return crud_investment.create_investment_account(db, current_user.id, account_in)

@router.get("/accounts", response_model=List[InvestmentAccountResponse])
def get_investment_accounts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get all investment accounts."""
    return crud_investment.get_investment_accounts(db, current_user.id)

@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment_account(
    account_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Delete an investment account."""
    account = db.get(InvestmentAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Check if used in investments
    # (Actually the foreign key is set NULL on delete in the model definition? 
    #  Let's check model. No, it says ForeignKey("investment_accounts.id", ondelete="SET NULL") in Investment model.
    #  So it is safe to delete, investments will just become orphaned from account.)
    
    db.delete(account)
    db.commit()
    return None


# --- Investments (Categories) ---
@router.post("/", response_model=InvestmentResponse)
def create_investment(
    investment_in: InvestmentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Create new investment category."""
    inv = crud_investment.create_investment(db, current_user.id, investment_in)
    return inv

@router.get("/", response_model=List[InvestmentResponse])
def get_investments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get all investment categories."""
    investments = crud_investment.get_investments(db, current_user.id)
    
    response_data = []
    for inv in investments:
        resp = InvestmentResponse.model_validate(inv)
        if inv.investment_account:
            resp.account_name = inv.investment_account.account_name
        if inv.opening_balance_currency:
            resp.currency_ticker = inv.opening_balance_currency.ticker
        response_data.append(resp)
        
    return response_data

@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
    investment_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Delete an investment category."""
    inv = db.get(Investment, investment_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    if inv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check for transfers? FK calls for cascade delete-orphan in Investment model:
    # transfers: Mapped[list["InvestmentTransfer"]] = relationship(back_populates="investment", cascade="all, delete-orphan")
    # So deleting investment deletes all transfers history.
    
    db.delete(inv)
    db.commit()
    return None


# --- Investment Transfers ---
@router.post("/transfers/{period_id}", response_model=InvestmentTransferResponse)
def create_investment_transfer(
    period_id: UUID,
    transfer_in: InvestmentTransferCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Create new investment transfer for a period."""
    from app.crud import period as crud_period
    period = crud_period.get_period(db, current_user.id, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
        
    transfer = crud_investment.create_investment_transfer(db, period_id, transfer_in)
    return transfer

@router.get("/transfers/{period_id}", response_model=List[InvestmentTransferResponse])
def get_investment_transfers(
    period_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get investment transfers for a period."""
    transfers = crud_investment.get_investment_transfers_by_period(db, period_id)
    
    response_data = []
    for t in transfers:
        resp = InvestmentTransferResponse.model_validate(t)
        if t.investment:
            resp.investment_category_name = t.investment.category_name
        if t.source_account:
            resp.source_account_name = t.source_account.account_name
        if t.currency:
            resp.currency_ticker = t.currency.ticker
        response_data.append(resp)
        
    return response_data

@router.delete("/transfers/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment_transfer(
    transfer_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Delete an investment transfer."""
    transfer = db.get(InvestmentTransfer, transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    # Ensure user owns the source account (indirect check)
    # Or check via source_account relationship... 
    # Easier: check if transfer.source_account.user_id == current_user.id
    # But we might need to load it first.
    
    stmt = select(InvestmentTransfer).join(InvestmentTransfer.source_account).where(
        InvestmentTransfer.id == transfer_id,
        InvestmentAccount.user_id == current_user.id # This might be wrong logic, source_account is Account, not InvAccount
    )
    # Actually source_account is "Account" (bank account).
    # Let's just do a simpler query: get transfer, assume security by period ownership if needed?
    # Better: check period ownership.
    
    from app.models.calculation_period import CalculationPeriod
    period = db.get(CalculationPeriod, transfer.calculation_period_id)
    if not period or period.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized")

    if period.status == "FINALIZED":
         raise HTTPException(status_code=400, detail="Cannot delete transfer in finalized period")

    db.delete(transfer)
    db.commit()
    return None
