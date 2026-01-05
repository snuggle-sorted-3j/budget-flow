from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models.currency import Currency

def get_currency_by_id(db: Session, user_id: UUID, currency_id: UUID) -> Optional[Currency]:
    """Get a currency by ID and user ID."""
    stmt = select(Currency).where(
        Currency.id == currency_id,
        Currency.user_id == user_id
    )
    return db.execute(stmt).scalar_one_or_none()


def list_currencies(db: Session, user_id: UUID) -> List[Currency]:
    """List all currencies for a user."""
    stmt = select(Currency).where(Currency.user_id == user_id).order_by(Currency.ticker)
    return list(db.execute(stmt).scalars().all())


def create_currency(db: Session, user_id: UUID, data: any) -> Currency:
    """Create a new currency."""
    # If this is set as default, unset others first
    if getattr(data, "is_default", False):
        db.execute(
            update(Currency)
            .where(Currency.user_id == user_id)
            .values(is_default=False)
        )

    db_currency = Currency(
        user_id=user_id,
        ticker=data.ticker.upper(),
        name=data.name,
        is_default=getattr(data, "is_default", False)
    )
    db.add(db_currency)
    db.commit()
    db.refresh(db_currency)
    return db_currency


def set_default_currency(db: Session, user_id: UUID, currency_id: UUID) -> Optional[Currency]:
    """Set a currency as default and unset others."""
    # First, unset all defaults for this user
    db.execute(
        update(Currency)
        .where(Currency.user_id == user_id)
        .values(is_default=False)
    )
    
    # Set the target currency as default
    currency = get_currency_by_id(db, user_id, currency_id)
    if currency:
        currency.is_default = True
        db.commit()
        db.refresh(currency)
    return currency


def delete_currency(db: Session, user_id: UUID, currency_id: UUID) -> Optional[Currency]:
    """Delete a currency."""
    currency = get_currency_by_id(db, user_id, currency_id)
    if currency:
        db.delete(currency)
        db.commit()
    return currency


def initialize_default_currencies(db: Session, user_id: UUID):
    """Initialize a default set of currencies for a new user. Adds missing ones."""
    default_currencies = [
        # European
        {"ticker": "EUR", "name": "Euro", "is_default": True},
        {"ticker": "PLN", "name": "Polish Zloty", "is_default": False},
        {"ticker": "GBP", "name": "British Pound", "is_default": False},
        {"ticker": "CHF", "name": "Swiss Franc", "is_default": False},
        {"ticker": "SEK", "name": "Swedish Krona", "is_default": False},
        {"ticker": "NOK", "name": "Norwegian Krone", "is_default": False},
        {"ticker": "DKK", "name": "Danish Krone", "is_default": False},
        {"ticker": "CZK", "name": "Czech Koruna", "is_default": False},
        {"ticker": "HUF", "name": "Hungarian Forint", "is_default": False},
        {"ticker": "RON", "name": "Romanian Leu", "is_default": False},
        # Americas
        {"ticker": "USD", "name": "US Dollar", "is_default": False},
        {"ticker": "CAD", "name": "Canadian Dollar", "is_default": False},
        {"ticker": "MXN", "name": "Mexican Peso", "is_default": False},
        {"ticker": "BRL", "name": "Brazilian Real", "is_default": False},
        {"ticker": "ARS", "name": "Argentine Peso", "is_default": False},
        # Asia-Pacific
        {"ticker": "JPY", "name": "Japanese Yen", "is_default": False},
        {"ticker": "CNY", "name": "Chinese Yuan", "is_default": False},
        {"ticker": "KRW", "name": "South Korean Won", "is_default": False},
        {"ticker": "INR", "name": "Indian Rupee", "is_default": False},
        {"ticker": "AUD", "name": "Australian Dollar", "is_default": False},
        {"ticker": "NZD", "name": "New Zealand Dollar", "is_default": False},
        {"ticker": "SGD", "name": "Singapore Dollar", "is_default": False},
        # Other Major
        {"ticker": "TRY", "name": "Turkish Lira", "is_default": False},
        {"ticker": "ZAR", "name": "South African Rand", "is_default": False},
        {"ticker": "RUB", "name": "Russian Ruble", "is_default": False},
    ]
    
    # Get existing tickers
    existing_currencies = db.execute(
        select(Currency.ticker).where(Currency.user_id == user_id)
    ).scalars().all()
    existing_tickers = {t.upper() for t in existing_currencies}
    
    # Check if any default is set
    has_default = db.execute(
        select(Currency).where(Currency.user_id == user_id, Currency.is_default == True)
    ).first() is not None

    for cur_data in default_currencies:
        if cur_data["ticker"] not in existing_tickers:
            # Only set as default if requested AND user has no default set yet
            should_be_default = cur_data["is_default"] and not has_default
            
            db_currency = Currency(
                user_id=user_id,
                ticker=cur_data["ticker"],
                name=cur_data["name"],
                is_default=should_be_default
            )
            db.add(db_currency)
            
            if should_be_default:
                has_default = True
    
    db.commit()
