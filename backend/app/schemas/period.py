from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class PeriodBase(BaseModel):
    """Base schema for CalculationPeriod."""

    period_name: str = Field(..., max_length=255)
    start_date: date
    end_date: date
    snapshot_date: date


class PeriodCreate(PeriodBase):
    """Schema for creating a CalculationPeriod."""

    @field_validator("snapshot_date")
    @classmethod
    def validate_snapshot_date(cls, v: date, info) -> date:
        if "end_date" in info.data and v != info.data["end_date"]:
            raise ValueError("snapshot_date must be equal to end_date")
        return v
    
    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: date, info) -> date:
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class PeriodUpdateStatus(BaseModel):
    """Schema for updating Period status."""

    status: str = Field(..., pattern="^(DRAFT|FINALIZED|ARCHIVED)$")


class PeriodResponse(PeriodBase):
    """Schema for CalculationPeriod response."""
    
    id: UUID
    user_id: UUID
    status: str
    finalized_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
