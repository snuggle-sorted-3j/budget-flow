from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    TIMESTAMP,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.balance_snapshot import BalanceSnapshot
    from app.models.currency_conversion import CurrencyConversion
    from app.models.expense_item import ExpenseItem
    from app.models.income_entry import IncomeEntry
    from app.models.investment_transfer import InvestmentTransfer
    from app.models.installment_payment import InstallmentPayment
    from app.models.suspended_expense import SuspendedExpense
    from app.models.user import User


class CalculationPeriod(Base):
    """Flexible calculation periods representing paycheck-based cycles."""

    __tablename__ = "calculation_periods"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    period_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    finalized_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="periods")
    balance_snapshots: Mapped[list["BalanceSnapshot"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    income_entries: Mapped[list["IncomeEntry"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    expense_items: Mapped[list["ExpenseItem"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    created_suspended_expenses: Mapped[list["SuspendedExpense"]] = relationship(
        back_populates="created_period",
        foreign_keys="SuspendedExpense.created_period_id",
    )
    settled_suspended_expenses: Mapped[list["SuspendedExpense"]] = relationship(
        back_populates="settled_period",
        foreign_keys="SuspendedExpense.settled_period_id",
    )
    installment_payments: Mapped[list["InstallmentPayment"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    currency_conversions: Mapped[list["CurrencyConversion"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    investment_transfers: Mapped[list["InvestmentTransfer"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("status IN ('DRAFT', 'FINALIZED', 'ARCHIVED')", name="check_status"),
        CheckConstraint("end_date >= start_date", name="valid_date_range"),
        CheckConstraint("snapshot_date = end_date", name="valid_snapshot_date"),
        Index("idx_periods_user", "user_id"),
        Index("idx_periods_user_date", "user_id", "snapshot_date"),
        Index("idx_periods_status", "user_id", "status"),
    )



