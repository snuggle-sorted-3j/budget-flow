from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import period as crud_period
from app.models.user import User
from app.schemas.period import PeriodCreate, PeriodResponse, PeriodUpdateStatus

router = APIRouter()


@router.post("/", response_model=PeriodResponse, status_code=status.HTTP_201_CREATED)
def create_period(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    period_in: PeriodCreate,
) -> Any:
    """
    Create a new calculation period.
    """
    period = crud_period.create_period(db=db, user_id=current_user.id, data=period_in)
    return period


@router.get("/", response_model=List[PeriodResponse])
def read_periods(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve user's calculation periods.
    """
    return crud_period.list_periods(db=db, user_id=current_user.id)


@router.get("/{period_id}", response_model=PeriodResponse)
def read_period(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific calculation period.
    """
    period = crud_period.get_period(db=db, user_id=current_user.id, period_id=period_id)
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not found",
        )
    return period


@router.patch("/{period_id}/status", response_model=PeriodResponse)
def update_period_status(
    *,
    db: Session = Depends(deps.get_db),
    period_id: UUID,
    status_in: PeriodUpdateStatus,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update status of a calculation period.
    """
    period = crud_period.update_period_status(
        db=db, user_id=current_user.id, period_id=period_id, status=status_in.status
    )
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not found",
        )
    return period
