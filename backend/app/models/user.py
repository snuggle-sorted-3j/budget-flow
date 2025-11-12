from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.calculation_period import CalculationPeriod
    from app.models.currency import Currency
    from app.models.custom_expense_type import CustomExpenseType
    from app.models.expense_category import ExpenseCategory
    from app.models.investment import Investment
    from app.models.investment_account import InvestmentAccount
    from app.models.installment_item import InstallmentItem
    from app.models.suspended_expense import SuspendedExpense
    from app.models.template import Template
    from app.models.user_settings import UserSettings


class User(Base):
    """User authentication and ownership model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    settings: Mapped["UserSettings"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    currencies: Mapped[list["Currency"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    periods: Mapped[list["CalculationPeriod"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    expense_categories: Mapped[list["ExpenseCategory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    suspended_expenses: Mapped[list["SuspendedExpense"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    installment_items: Mapped[list["InstallmentItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    investments: Mapped[list["Investment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    investment_accounts: Mapped[list["InvestmentAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    templates: Mapped[list["Template"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    custom_expense_types: Mapped[list["CustomExpenseType"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_active", "is_active"),
    )

