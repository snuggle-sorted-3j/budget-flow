from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.account import Account
from app.models.currency import Currency
from app.models.investment import Investment
from app.models.investment_account import InvestmentAccount
from app.models.investment_transfer import InvestmentTransfer
from app.schemas.investment import (
    InvestmentAccountCreate,
    InvestmentAccountUpdate,
    InvestmentCreate,
    InvestmentTransferCreate,
)


# --- Investment Accounts ---
def create_investment_account(
    db: Session, user_id: UUID, obj_in: InvestmentAccountCreate
) -> InvestmentAccount:
    db_obj = InvestmentAccount(
        user_id=user_id,
        account_name=obj_in.account_name,
        account_type=obj_in.account_type,
        notes=obj_in.notes,
        is_active=obj_in.is_active,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_investment_accounts(db: Session, user_id: UUID) -> List[InvestmentAccount]:
    stmt = select(InvestmentAccount).where(InvestmentAccount.user_id == user_id)
    return list(db.execute(stmt).scalars().all())


# --- Investments (Categories) ---
def create_investment(db: Session, user_id: UUID, obj_in: InvestmentCreate) -> Investment:
    db_obj = Investment(
        user_id=user_id,
        category_name=obj_in.category_name,
        investment_account_id=obj_in.investment_account_id,
        opening_balance=obj_in.opening_balance,
        opening_balance_date=obj_in.opening_balance_date,
        opening_balance_currency_id=obj_in.opening_balance_currency_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_investments(db: Session, user_id: UUID) -> List[Investment]:
    # Join to get details
    stmt = (
        select(Investment)
        .options(
            joinedload(Investment.investment_account),
            joinedload(Investment.opening_balance_currency),
        )
        .where(Investment.user_id == user_id)
    )
    results = db.execute(stmt).scalars().all()
    # Pydantic will handle the extraction if the schema expects flattened fields or nested objects.
    # Our schema expects matching fields, but we might need to map them if we want 'account_name' etc directly.
    # For now, let's rely on standard ORM loading.
    return list(results)


# --- Investment Transfers ---
def create_investment_transfer(
    db: Session, period_id: UUID, obj_in: InvestmentTransferCreate
) -> InvestmentTransfer:
    db_obj = InvestmentTransfer(
        investment_id=obj_in.investment_id,
        calculation_period_id=period_id,
        amount_transferred=obj_in.amount_transferred,
        currency_id=obj_in.currency_id,
        source_account_id=obj_in.source_account_id,
        transfer_date=obj_in.transfer_date,
        units_added=obj_in.units_added,
        notes=obj_in.notes,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_investment_transfers_by_period(
    db: Session, period_id: UUID
) -> List[InvestmentTransfer]:
    stmt = (
        select(InvestmentTransfer)
        .options(
            joinedload(InvestmentTransfer.investment),
            joinedload(InvestmentTransfer.source_account),
            joinedload(InvestmentTransfer.currency),
        )
        .where(InvestmentTransfer.calculation_period_id == period_id)
        .order_by(InvestmentTransfer.transfer_date.desc())
    )
    return list(db.execute(stmt).scalars().all())
