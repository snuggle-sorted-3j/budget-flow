from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate


def create_account(db: Session, user_id: UUID, data: AccountCreate) -> Account:
    """Create a new account."""
    # Check for existing account with same name for this user
    stmt = select(Account).where(
        Account.user_id == user_id, 
        Account.account_name == data.account_name,
        Account.is_active == True
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise ValueError(f"Account with name '{data.account_name}' already exists.")

    db_account = Account(
        user_id=user_id,
        account_name=data.account_name,
        account_type=data.account_type,
        currency_id=data.currency_id,
        opening_balance=data.opening_balance,
        opening_balance_date=data.opening_balance_date,
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def list_accounts(db: Session, user_id: UUID) -> List[Account]:
    """List all accounts for a user."""
    stmt = select(Account).where(
        Account.user_id == user_id
    ).order_by(Account.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_account(db: Session, user_id: UUID, account_id: UUID) -> Optional[Account]:
    """Get an account by ID and user ID."""
    stmt = select(Account).where(Account.id == account_id, Account.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def deactivate_account(db: Session, user_id: UUID, account_id: UUID) -> Optional[Account]:
    """Deactivate an account."""
    account = get_account(db, user_id, account_id)
    if not account:
        return None
    
    account.is_active = False
    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, user_id: UUID, account_id: UUID) -> bool:
    """Hard delete an account if it has no transactions/snapshots."""
    account = get_account(db, user_id, account_id)
    if not account:
        return False
        
    # Check for snapshots
    from app.models.balance_snapshot import BalanceSnapshot
    snap_stmt = select(BalanceSnapshot).where(BalanceSnapshot.account_id == account_id).limit(1)
    if db.execute(snap_stmt).scalar_one_or_none():
        raise ValueError("Cannot delete account: It has balance snapshots from previous periods. Deactivate it instead.")

    # Check for investment transfers
    from app.models.investment_transfer import InvestmentTransfer
    trans_stmt = select(InvestmentTransfer).where(InvestmentTransfer.source_account_id == account_id).limit(1)
    if db.execute(trans_stmt).scalar_one_or_none():
        raise ValueError("Cannot delete account: It has linked investment transfers. Deactivate it instead.")
        
    db.delete(account)
    db.commit()
    return True
