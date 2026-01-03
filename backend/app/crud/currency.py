from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.currency import Currency

def get_currency(db: Session, user_id: UUID, currency_id: UUID) -> Optional[Currency]:
    """Get a currency by ID and user ID."""
    stmt = select(Currency).where(
        Currency.id == currency_id,
        Currency.user_id == user_id
    )
    return db.execute(stmt).scalar_one_or_none()
