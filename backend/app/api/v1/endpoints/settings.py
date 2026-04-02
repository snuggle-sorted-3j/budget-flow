from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import settings as crud_settings
from app.models.user import User
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdate

router = APIRouter()


@router.get("/", response_model=UserSettingsResponse)
def get_settings(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get current user's settings."""
    settings = crud_settings.get_settings(db=db, user_id=current_user.id)
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")
    return settings


@router.put("/", response_model=UserSettingsResponse)
def update_settings(
    *,
    db: Session = Depends(deps.get_db),
    settings_in: UserSettingsUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Update current user's settings."""
    settings = crud_settings.upsert_settings(db=db, user_id=current_user.id, data=settings_in)
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")
    return settings
