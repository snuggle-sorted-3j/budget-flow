from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DECIMAL,
    ForeignKey,
    Index,
    Text,
    TIMESTAMP,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.calculation_period import CalculationPeriod
    from app.models.installment_item import InstallmentItem


class InstallmentPayment(Base):
    """Payments applied toward installment items."""

    __tablename__ = "installment_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    installment_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("installment_items.id", ondelete="CASCADE"), nullable=False
    )
    calculation_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calculation_periods.id", ondelete="CASCADE"), nullable=False
    )
    payment_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    installment_item: Mapped["InstallmentItem"] = relationship(back_populates="payments")
    period: Mapped["CalculationPeriod"] = relationship(back_populates="installment_payments")

    __table_args__ = (
        CheckConstraint("payment_amount > 0", name="check_payment_amount_positive"),
        Index("idx_payments_installment", "installment_item_id"),
        Index("idx_payments_period", "calculation_period_id"),
        Index("idx_payments_date", "payment_date"),
    )



