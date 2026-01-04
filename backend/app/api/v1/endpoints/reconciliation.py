from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import period as crud_period
from app.models.user import User
from app.schemas.reconciliation import PeriodReconciliation
from app.services import reconciliation_service

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
