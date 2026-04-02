from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_settings import UserSettings
from app.schemas.settings import UserSettingsUpdate


def get_settings(db: Session, user_id: UUID) -> UserSettings | None:
    """Get user settings or None if not configured."""
    return db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    ).scalar_one_or_none()


def upsert_settings(db: Session, user_id: UUID, data: UserSettingsUpdate) -> UserSettings | None:
    """Create or update user settings.

    Creates a new row when none exists (requires default_currency_id to be set).
    Returns None if creating and default_currency_id is absent.
    """
    settings = get_settings(db, user_id)
    update_data = data.model_dump(exclude_none=True)

    if not settings:
        if "default_currency_id" not in update_data:
            return None
        settings = UserSettings(user_id=user_id, **update_data)
        db.add(settings)
    else:
        for field, value in update_data.items():
            setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings
