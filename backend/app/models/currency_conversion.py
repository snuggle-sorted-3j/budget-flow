from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DECIMAL, ForeignKey, Index, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.calculation_period import CalculationPeriod
    from app.models.currency import Currency


class CurrencyConversion(Base):
    """Currency exchange transactions tracked per period."""

    __tablename__ = "currency_conversions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calculation_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calculation_periods.id", ondelete="CASCADE"), nullable=False
    )
    from_currency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id", ondelete="RESTRICT"), nullable=False
    )
    to_currency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id", ondelete="RESTRICT"), nullable=False
    )
    from_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    to_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    rate: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False)
    conversion_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    period: Mapped["CalculationPeriod"] = relationship(back_populates="currency_conversions")
    from_currency: Mapped["Currency"] = relationship(
        back_populates="from_currency_conversions", foreign_keys=[from_currency_id]
    )
    to_currency: Mapped["Currency"] = relationship(
        back_populates="to_currency_conversions", foreign_keys=[to_currency_id]
    )
    source_account: Mapped["Account | None"] = relationship()

    __table_args__ = (
        CheckConstraint("from_amount > 0", name="check_from_amount_positive"),
        CheckConstraint("to_amount > 0", name="check_to_amount_positive"),
        CheckConstraint("rate > 0", name="check_conversion_rate_positive"),
        CheckConstraint("from_currency_id <> to_currency_id", name="different_currencies"),
        Index("idx_conversions_period", "calculation_period_id"),
        Index("idx_conversions_from_currency", "from_currency_id"),
        Index("idx_conversions_to_currency", "to_currency_id"),
        Index("idx_conversions_date", "conversion_date"),
    )

