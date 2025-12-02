from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Dict

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Template(Base):
    """Reusable templates for expenses, income, and combined data."""

    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    template_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="templates")

    __table_args__ = (
        CheckConstraint(
            "template_type IN ('EXPENSE_CATEGORIES', 'INCOME_SOURCES', 'FULL')",
            name="check_template_type",
        ),
        Index("idx_templates_user", "user_id"),
        Index("idx_templates_default", "user_id", "is_default"),
        Index("idx_templates_type", "user_id", "template_type"),
        Index("idx_templates_data", "template_data", postgresql_using="gin"),
    )



