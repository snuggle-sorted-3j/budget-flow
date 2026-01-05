from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.currency_conversion import CurrencyConversion
from app.schemas.currency_conversion import CurrencyConversionCreate, CurrencyConversionUpdate


def create_currency_conversion(
    db: Session, conversion_in: CurrencyConversionCreate, period_id: UUID
) -> CurrencyConversion:
    db_obj = CurrencyConversion(
        calculation_period_id=period_id,
        **conversion_in.model_dump()
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_currency_conversions(
    db: Session, period_id: UUID
) -> List[CurrencyConversion]:
    stmt = (
        select(CurrencyConversion)
        .where(CurrencyConversion.calculation_period_id == period_id)
        .order_by(CurrencyConversion.conversion_date.desc())
    )
    return db.execute(stmt).scalars().all()


def get_currency_conversion(db: Session, conversion_id: UUID) -> Optional[CurrencyConversion]:
    return db.get(CurrencyConversion, conversion_id)


def update_currency_conversion(
    db: Session, db_obj: CurrencyConversion, conversion_update: CurrencyConversionUpdate
) -> CurrencyConversion:
    update_data = conversion_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_currency_conversion(db: Session, db_obj: CurrencyConversion) -> None:
    db.delete(db_obj)
    db.commit()
