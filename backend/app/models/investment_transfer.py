from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DECIMAL, ForeignKey, Index, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.calculation_period import CalculationPeriod
    from app.models.currency import Currency
    from app.models.investment import Investment


class InvestmentTransfer(Base):
    """Transfers of funds into investment categories."""

    __tablename__ = "investment_transfers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investments.id", ondelete="CASCADE"), nullable=False
    )
    calculation_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calculation_periods.id", ondelete="CASCADE"), nullable=False
    )
    amount_transferred: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    currency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id", ondelete="RESTRICT"), nullable=False
    )
    source_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_opening_balance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    investment: Mapped["Investment"] = relationship(back_populates="transfers")
    period: Mapped["CalculationPeriod"] = relationship(back_populates="investment_transfers")
    currency: Mapped["Currency"] = relationship(back_populates="investment_transfers")
    source_account: Mapped["Account"] = relationship(back_populates="investment_transfers")

    __table_args__ = (
        Index("idx_transfers_investment", "investment_id"),
        Index("idx_transfers_period", "calculation_period_id"),
        Index("idx_transfers_currency", "currency_id"),
        Index("idx_transfers_date", "transfer_date"),
        Index("idx_transfers_opening", "is_opening_balance"),
    )

