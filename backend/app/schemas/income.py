from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncomeBase(BaseModel):
    """Base schema for IncomeEntry."""

    source_name: str = Field(..., max_length=255)
    amount: Decimal = Field(..., ge=0)
    currency_id: UUID
    income_date: date | None = None
    tax_applicable: bool = False
    notes: str | None = None
    is_recurring: bool = False


class IncomeCreate(IncomeBase):
    """Schema for creating an IncomeEntry."""
    pass


class IncomeUpdate(BaseModel):
    """Schema for updating an IncomeEntry."""
    
    source_name: str | None = Field(None, max_length=255)
    amount: Decimal | None = Field(None, ge=0)
    currency_id: UUID | None = None
    income_date: date | None = None
    tax_applicable: bool | None = None
    notes: str | None = None
    is_recurring: bool | None = None


class IncomeResponse(IncomeBase):
    """Schema for IncomeEntry response."""
    
    id: UUID
    calculation_period_id: UUID
    currency_code: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
