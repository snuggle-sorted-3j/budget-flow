from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.expense_item import ExpenseItem
    from app.models.user import User


class ExpenseCategory(Base):
    """Hierarchical expense categories with optional parent."""

    __tablename__ = "expense_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expense_categories.id", ondelete="RESTRICT")
    )
    is_system_category: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="expense_categories")
    parent: Mapped["ExpenseCategory | None"] = relationship(
        "ExpenseCategory",
        remote_side=lambda: ExpenseCategory.id,
        back_populates="children",
    )
    children: Mapped[list["ExpenseCategory"]] = relationship(
        "ExpenseCategory",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    expense_items: Mapped[list["ExpenseItem"]] = relationship(back_populates="category")

    __table_args__ = (
        Index("idx_categories_user", "user_id"),
        Index("idx_categories_parent", "parent_category_id"),
        Index("idx_categories_active", "user_id", "is_active"),
        Index("idx_categories_sort", "user_id", "sort_order"),
    )

