from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, TIMESTAMP, func
from sqlalchemy import DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.currency import Currency
    from app.models.user import User


class UserSettings(Base):
    """User preferences and defaults."""

    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    default_currency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("currencies.id", ondelete="RESTRICT"), nullable=False
    )
    tax_system: Mapped[str] = mapped_column(String(50), default="NONE", nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), default=0, nullable=False)
    preferred_date_format: Mapped[str] = mapped_column(String(20), default="YYYY-MM-DD", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Warsaw", nullable=False)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="settings")
    default_currency: Mapped["Currency"] = relationship()

    __table_args__ = (
        CheckConstraint("tax_system IN ('POLISH_B2B', 'US_ANNUAL', 'NONE')", name="check_tax_system"),
        CheckConstraint("tax_rate >= 0 AND tax_rate <= 100", name="check_tax_rate"),
    )

