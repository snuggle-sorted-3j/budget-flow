from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TIMESTAMP,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.calculation_period import CalculationPeriod
    from app.models.currency import Currency
    from app.models.installment_payment import InstallmentPayment
    from app.models.user import User


class InstallmentItem(Base):
    """Items purchased on installment payment plans."""

    __tablename__ = "installment_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    currency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id", ondelete="RESTRICT"), nullable=False
    )
    initial_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calculation_periods.id", ondelete="RESTRICT"), nullable=False
    )
    remaining_balance: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    monthly_payment_amount: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2))
    months_to_pay: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="installment_items")
    currency: Mapped["Currency"] = relationship(back_populates="installment_items")
    initial_period: Mapped["CalculationPeriod"] = relationship(foreign_keys=[initial_period_id])
    payments: Mapped[list["InstallmentPayment"]] = relationship(
        back_populates="installment_item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("total_price > 0", name="check_total_price_positive"),
        CheckConstraint("remaining_balance >= 0", name="check_remaining_balance_positive"),
        CheckConstraint("status IN ('ACTIVE', 'PAID_OFF')", name="check_installment_status"),
        Index("idx_installments_user", "user_id"),
        Index("idx_installments_status", "user_id", "status"),
        Index("idx_installments_period", "initial_period_id"),
    )

