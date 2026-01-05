from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CurrencyConversionBase(BaseModel):
    from_currency_id: UUID
    to_currency_id: UUID
    from_amount: Decimal = Field(..., gt=0)
    to_amount: Decimal = Field(..., gt=0)
    rate: Decimal = Field(..., gt=0)
    conversion_date: date
    source_account_id: Optional[UUID] = None
    notes: Optional[str] = None


class CurrencyConversionCreate(CurrencyConversionBase):
    pass


class CurrencyConversionUpdate(BaseModel):
    from_currency_id: Optional[UUID] = None
    to_currency_id: Optional[UUID] = None
    from_amount: Optional[Decimal] = Field(None, gt=0)
    to_amount: Optional[Decimal] = Field(None, gt=0)
    rate: Optional[Decimal] = Field(None, gt=0)
    conversion_date: Optional[date] = None
    source_account_id: Optional[UUID] = None
    notes: Optional[str] = None


class CurrencyConversionResponse(CurrencyConversionBase):
    id: UUID
    calculation_period_id: UUID
    created_at: datetime
    
    # Helpers for UI
    from_currency_ticker: Optional[str] = None
    to_currency_ticker: Optional[str] = None
    source_account_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
