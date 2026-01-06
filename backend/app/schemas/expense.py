from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExpenseBase(BaseModel):
    """Base schema for ExpenseItem."""

    item_name: str = Field(..., max_length=255)
    amount: Decimal = Field(..., ge=0)
    category_id: UUID
    currency_id: UUID
    expense_date: date | None = None
    expense_type: str = "REGULAR"
    is_tax_deductible: bool = False
    tax_category: str | None = Field(None, max_length=100)
    notes: str | None = None


class ExpenseCreate(ExpenseBase):
    """Schema for creating an ExpenseItem."""
    pass


class ExpenseResponse(ExpenseBase):
    """Schema for ExpenseItem response."""
    
    id: UUID
    calculation_period_id: UUID
    category_name: str | None = None
    currency_code: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
