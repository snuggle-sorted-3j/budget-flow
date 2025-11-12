from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.currency_conversion import CurrencyConversion
    from app.models.expense_item import ExpenseItem
    from app.models.income_entry import IncomeEntry
    from app.models.installment_item import InstallmentItem
    from app.models.investment import Investment
    from app.models.investment_transfer import InvestmentTransfer
    from app.models.suspended_expense import SuspendedExpense
    from app.models.template import Template
    from app.models.user import User
    from app.models.user_settings import UserSettings


class Currency(Base):
    """User-defined currencies supporting multi-currency operations."""

    __tablename__ = "currencies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="currencies")
    accounts: Mapped[list["Account"]] = relationship(back_populates="currency")
    income_entries: Mapped[list["IncomeEntry"]] = relationship(back_populates="currency")
    expense_items: Mapped[list["ExpenseItem"]] = relationship(back_populates="currency")
    suspended_expenses: Mapped[list["SuspendedExpense"]] = relationship(back_populates="currency")
    installment_items: Mapped[list["InstallmentItem"]] = relationship(back_populates="currency")
    investment_transfers: Mapped[list["InvestmentTransfer"]] = relationship(back_populates="currency")
    investments: Mapped[list["Investment"]] = relationship(
        back_populates="opening_balance_currency", foreign_keys="Investment.opening_balance_currency_id"
    )
    from_currency_conversions: Mapped[list["CurrencyConversion"]] = relationship(
        back_populates="from_currency", foreign_keys="CurrencyConversion.from_currency_id"
    )
    to_currency_conversions: Mapped[list["CurrencyConversion"]] = relationship(
        back_populates="to_currency", foreign_keys="CurrencyConversion.to_currency_id"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="unique_ticker_per_user"),
        Index("idx_currencies_user", "user_id"),
        Index("idx_currencies_default", "user_id", "is_default"),
    )

