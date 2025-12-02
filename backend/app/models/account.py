from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.balance_snapshot import BalanceSnapshot
    from app.models.currency import Currency
    from app.models.investment_transfer import InvestmentTransfer
    from app.models.user import User


class Account(Base):
    """Bank and cash accounts with currency linkage."""

    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    currency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id", ondelete="RESTRICT"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="accounts")
    currency: Mapped["Currency"] = relationship(back_populates="accounts")
    balance_snapshots: Mapped[list["BalanceSnapshot"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    investment_transfers: Mapped[list["InvestmentTransfer"]] = relationship(
        back_populates="source_account"
    )

    __table_args__ = (
        CheckConstraint("account_type IN ('BANK', 'CASH')", name="check_account_type"),
        Index("idx_accounts_user", "user_id"),
        Index("idx_accounts_active", "user_id", "is_active"),
        Index("idx_accounts_currency", "currency_id"),
    )



