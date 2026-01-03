from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BalanceSnapshotBase(BaseModel):
    """Base schema for BalanceSnapshot."""

    account_id: UUID
    balance: Decimal


class BalanceSnapshotCreate(BalanceSnapshotBase):
    """Schema for creating a BalanceSnapshot."""
    pass


class BalanceSnapshotResponse(BalanceSnapshotBase):
    """Schema for BalanceSnapshot response."""

    id: UUID
    calculation_period_id: UUID
    snapshot_date: date
    created_at: object  # Use object for timestamp to match model or datetime

    model_config = ConfigDict(from_attributes=True)
