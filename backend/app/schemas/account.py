from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AccountBase(BaseModel):
    """Base schema for Account."""

    account_name: str = Field(..., max_length=255)
    account_type: str = Field(..., pattern="^(BANK|CASH)$")
    currency_id: UUID
    opening_balance: float = 0.0
    opening_balance_date: date | None = None


class AccountCreate(AccountBase):
    """Schema for creating an Account."""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating an Account."""
    
    account_name: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class AccountResponse(AccountBase):
    """Schema for Account response."""
    
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
