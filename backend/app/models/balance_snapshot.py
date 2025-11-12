from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DECIMAL, ForeignKey, Index, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.calculation_period import CalculationPeriod


class BalanceSnapshot(Base):
    """Account balance recorded for a calculation period."""

    __tablename__ = "balance_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calculation_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calculation_periods.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    balance: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    period: Mapped["CalculationPeriod"] = relationship(back_populates="balance_snapshots")
    account: Mapped["Account"] = relationship(back_populates="balance_snapshots")

    __table_args__ = (
        UniqueConstraint("account_id", "calculation_period_id", name="unique_account_period"),
        Index("idx_snapshots_period", "calculation_period_id"),
        Index("idx_snapshots_account", "account_id"),
        Index("idx_snapshots_date", "snapshot_date"),
    )

