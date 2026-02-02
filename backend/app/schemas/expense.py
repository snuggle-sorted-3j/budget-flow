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
    is_recurring: bool = False


class ExpenseCreate(ExpenseBase):
    """Schema for creating an ExpenseItem."""
    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating an ExpenseItem."""
    
    item_name: str | None = Field(None, max_length=255)
    amount: Decimal | None = Field(None, ge=0)
    category_id: UUID | None = None
    currency_id: UUID | None = None
    expense_date: date | None = None
    expense_type: str | None = None
    is_tax_deductible: bool | None = None
    tax_category: str | None = None
    notes: str | None = None
    is_recurring: bool | None = None


class ExpenseResponse(ExpenseBase):
    """Schema for ExpenseItem response."""
    
    id: UUID
    calculation_period_id: UUID
    category_name: str | None = None
    currency_code: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
