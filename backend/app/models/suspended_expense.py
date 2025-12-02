from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DECIMAL,
    ForeignKey,
    Index,
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
    from app.models.user import User


class SuspendedExpense(Base):
    """Transactions temporarily removed from circulation."""

    __tablename__ = "suspended_expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    currency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id", ondelete="RESTRICT"), nullable=False
    )
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    created_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calculation_periods.id", ondelete="RESTRICT"), nullable=False
    )
    settled_period_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calculation_periods.id", ondelete="RESTRICT")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="suspended_expenses")
    currency: Mapped["Currency"] = relationship(back_populates="suspended_expenses")
    created_period: Mapped["CalculationPeriod"] = relationship(
        back_populates="created_suspended_expenses", foreign_keys=[created_period_id]
    )
    settled_period: Mapped["CalculationPeriod | None"] = relationship(
        back_populates="settled_suspended_expenses", foreign_keys=[settled_period_id]
    )

    __table_args__ = (
        CheckConstraint("amount >= 0", name="positive_suspended_amount"),
        CheckConstraint(
            "transaction_type IN ('LOAN_OUT', 'PURCHASE_RETURN', 'OTHER')",
            name="check_transaction_type",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'SETTLED', 'CONVERTED_TO_EXPENSE')", name="check_suspended_status"
        ),
        Index("idx_suspended_user", "user_id"),
        Index("idx_suspended_status", "status", "created_period_id"),
        Index("idx_suspended_created_period", "created_period_id"),
        Index("idx_suspended_settled_period", "settled_period_id"),
    )



