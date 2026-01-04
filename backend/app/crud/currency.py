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


def list_currencies(db: Session, user_id: UUID) -> bytes: # Using bytes as return type placeholder for list if needed, but standard is List[Currency]
    """List all currencies for a user."""
    stmt = select(Currency).where(Currency.user_id == user_id).order_by(Currency.ticker)
    return list(db.execute(stmt).scalars().all())


def create_currency(db: Session, user_id: UUID, data: any) -> Currency:
    """Create a new currency."""
    db_currency = Currency(
        user_id=user_id,
        ticker=data.ticker,
        name=data.name,
        is_default=data.is_default
    )
    db.add(db_currency)
    db.commit()
    db.refresh(db_currency)
    return db_currency
