from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class CurrencyBase(BaseModel):
    """Base schema for Currency."""

    ticker: str = Field(..., max_length=10)
    name: str = Field(..., max_length=100)
    is_default: bool = False


class CurrencyCreate(CurrencyBase):
    """Schema for creating a Currency."""
    pass


class CurrencyResponse(CurrencyBase):
    """Schema for Currency response."""
    
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
