from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DECIMAL, Date, ForeignKey, Index, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.currency import Currency
    from app.models.investment_account import InvestmentAccount
    from app.models.investment_transfer import InvestmentTransfer
    from app.models.user import User


class Investment(Base):
    """Investment categories with optional associated accounts."""

    __tablename__ = "investments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    investment_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investment_accounts.id", ondelete="SET NULL")
    )
    opening_balance: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2))
    opening_balance_date: Mapped[date | None] = mapped_column(Date)
    opening_balance_currency_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id", ondelete="RESTRICT")
    )
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="investments")
    investment_account: Mapped["InvestmentAccount | None"] = relationship(
        back_populates="investments"
    )
    opening_balance_currency: Mapped["Currency | None"] = relationship(
        back_populates="investments",
        foreign_keys=[opening_balance_currency_id],
    )
    transfers: Mapped[list["InvestmentTransfer"]] = relationship(
        back_populates="investment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_investments_user", "user_id"),
        Index("idx_investments_account", "investment_account_id"),
        Index("idx_investments_category", "user_id", "category_name"),
    )

