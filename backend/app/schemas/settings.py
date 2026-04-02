from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""

    default_currency_id: Optional[UUID] = None
    tax_system: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    preferred_date_format: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator("tax_system")
    @classmethod
    def validate_tax_system(cls, v):
        if v is not None and v not in ("POLISH_B2B", "US_ANNUAL", "NONE"):
            raise ValueError("tax_system must be POLISH_B2B, US_ANNUAL, or NONE")
        return v


class UserSettingsResponse(BaseModel):
    """Schema for user settings response."""

    user_id: UUID
    default_currency_id: UUID
    tax_system: str
    tax_rate: Decimal
    preferred_date_format: str
    timezone: str

    model_config = ConfigDict(from_attributes=True)
