from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.investment import Investment
    from app.models.user import User


class InvestmentAccount(Base):
    """Accounts holding investment assets (brokerage, crypto, physical)."""

    __tablename__ = "investment_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="investment_accounts")
    investments: Mapped[list["Investment"]] = relationship(
        back_populates="investment_account"
    )

    __table_args__ = (
        CheckConstraint(
            "account_type IN ('BROKERAGE', 'CRYPTO_EXCHANGE', 'PHYSICAL')",
            name="check_investment_account_type",
        ),
        Index("idx_investment_accounts_user", "user_id"),
        Index("idx_investment_accounts_active", "user_id", "is_active"),
    )



