from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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
    from app.models.expense_category import ExpenseCategory


class ExpenseItem(Base):
    """Individual expense entries linked to categories and periods."""

    __tablename__ = "expense_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calculation_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calculation_periods.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expense_categories.id", ondelete="RESTRICT"), nullable=False
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    currency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id", ondelete="RESTRICT"), nullable=False
    )
    expense_date: Mapped[date | None] = mapped_column(Date)
    expense_type: Mapped[str] = mapped_column(String(50), default="REGULAR", nullable=False)
    is_tax_deductible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tax_category: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    period: Mapped["CalculationPeriod"] = relationship(back_populates="expense_items")
    category: Mapped["ExpenseCategory"] = relationship(back_populates="expense_items")
    currency: Mapped["Currency"] = relationship(back_populates="expense_items")

    @property
    def category_name(self) -> str:
        """Helper to get category name without nested access in frontend or schema logic."""
        return self.category.category_name if self.category else "Uncategorized"

    @property
    def currency_code(self) -> str:
        """Helper to get currency ticker."""
        return self.currency.ticker if self.currency else ""

    __table_args__ = (
        CheckConstraint("amount >= 0", name="positive_expense_amount"),
        CheckConstraint(
            "expense_type IN ('REGULAR', 'INSTALLMENT_PAYMENT')", name="check_expense_type"
        ),
        Index("idx_expenses_period", "calculation_period_id"),
        Index("idx_expenses_category", "category_id"),
        Index("idx_expenses_currency", "currency_id"),
        Index("idx_expenses_date", "expense_date"),
        Index("idx_expenses_tax_deductible", "calculation_period_id", "is_tax_deductible"),
    )



