from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import balance_snapshot as crud_snapshot
from app.crud import period as crud_period
from app.crud import account as crud_account
from app.models.user import User
from app.schemas.balance_snapshot import BalanceSnapshotCreate, BalanceSnapshotResponse

router = APIRouter()


@router.post("/periods/{period_id}/snapshots", response_model=List[BalanceSnapshotResponse])
def create_or_update_snapshots(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    snapshots_in: List[BalanceSnapshotCreate],
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create or update balance snapshots for a specific period.
    """
    # Verify period belongs to user
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    results = []
    for snapshot_in in snapshots_in:
        # Verify account belongs to user (optional but good practice)
        account = crud_account.get_account(db=db, user_id=current_user.id, account_id=snapshot_in.account_id)
        if not account:
            raise HTTPException(status_code=400, detail=f"Account {snapshot_in.account_id} not found or access denied")
            
        result = crud_snapshot.upsert_snapshot(
            db=db,
            period_id=period_id,
            account_id=snapshot_in.account_id,
            balance=snapshot_in.balance
        )
        results.append(result)
    
    return results


@router.get("/periods/{period_id}/snapshots", response_model=List[BalanceSnapshotResponse])
def read_snapshots(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve snapshots for a period.
    """
    # Verify period belongs to user
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
        
    return crud_snapshot.list_snapshots_for_period(db=db, period_id=period_id)
