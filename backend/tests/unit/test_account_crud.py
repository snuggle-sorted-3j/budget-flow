"""Unit tests for app/crud/account.py — targeting 90%+ coverage."""
import uuid
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.crud.account import (
    create_account,
    deactivate_account,
    delete_account,
    get_account,
    list_accounts,
)
from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.calculation_period import CalculationPeriod
from app.models.currency import Currency
from app.models.investment import Investment
from app.models.investment_transfer import InvestmentTransfer
from app.schemas.account import AccountCreate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_account_data(
    currency_id: uuid.UUID,
    name: str = "Checking",
    account_type: str = "BANK",
) -> AccountCreate:
    return AccountCreate(
        account_name=name,
        account_type=account_type,
        currency_id=currency_id,
        opening_balance=1000.0,
        opening_balance_date=date(2025, 1, 1),
    )


def _orm_account(
    db: Session,
    user_id: uuid.UUID,
    currency_id: uuid.UUID,
    name: str = "Checking",
    account_type: str = "BANK",
    is_active: bool = True,
) -> Account:
    """Create an Account directly via ORM (no CRUD commit) so callers can
    still call one CRUD function per test without double-commit issues."""
    account = Account(
        id=uuid.uuid4(),
        user_id=user_id,
        account_name=name,
        account_type=account_type,
        currency_id=currency_id,
        opening_balance=1000.0,
        opening_balance_date=date(2025, 1, 1),
        is_active=is_active,
    )
    db.add(account)
    db.flush()
    return account


def _make_period(db: Session, user_id: uuid.UUID) -> CalculationPeriod:
    period = CalculationPeriod(
        id=uuid.uuid4(),
        user_id=user_id,
        period_name="Test Period",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        snapshot_date=date(2025, 1, 31),
        status="DRAFT",
    )
    db.add(period)
    db.flush()
    return period


def _make_investment(db: Session, user_id: uuid.UUID) -> Investment:
    investment = Investment(
        id=uuid.uuid4(),
        user_id=user_id,
        category_name="Test Fund",
    )
    db.add(investment)
    db.flush()
    return investment


def _make_user(db: Session):
    """Create a standalone user for isolation tests."""
    from app.models.user import User
    from app.core.security import get_password_hash

    email = f"isolated-{uuid.uuid4()}@example.com"
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=get_password_hash("password"),
        full_name="Isolated User",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


# ---------------------------------------------------------------------------
# create_account
# ---------------------------------------------------------------------------

class TestCreateAccount:
    def test_create_bank_account_happy_path(self, db: Session, test_user, test_currency):
        data = _make_account_data(test_currency.id, name="My Bank", account_type="BANK")
        account = create_account(db, test_user.id, data)

        assert account.id is not None
        assert account.account_name == "My Bank"
        assert account.account_type == "BANK"
        assert account.currency_id == test_currency.id
        assert account.user_id == test_user.id
        assert account.is_active is True
        assert float(account.opening_balance) == 1000.0
        assert account.opening_balance_date == date(2025, 1, 1)

    def test_create_cash_account(self, db: Session, test_user, test_currency):
        data = _make_account_data(test_currency.id, name="Wallet", account_type="CASH")
        account = create_account(db, test_user.id, data)

        assert account.account_type == "CASH"

    def test_create_account_zero_opening_balance(self, db: Session, test_user, test_currency):
        data = AccountCreate(
            account_name="Empty Account",
            account_type="BANK",
            currency_id=test_currency.id,
            opening_balance=0.0,
        )
        account = create_account(db, test_user.id, data)
        assert float(account.opening_balance) == 0.0
        assert account.opening_balance_date is None

    def test_create_account_without_opening_balance_date(self, db: Session, test_user, test_currency):
        data = AccountCreate(
            account_name="No Date Account",
            account_type="BANK",
            currency_id=test_currency.id,
        )
        account = create_account(db, test_user.id, data)
        assert account.opening_balance_date is None

    def test_create_duplicate_active_name_raises_value_error(self, db: Session, test_user, test_currency):
        # Pre-create an active account via ORM (no CRUD commit)
        _orm_account(db, test_user.id, test_currency.id, name="Duplicate", is_active=True)

        # Now CRUD create should fail — only one CRUD commit in this test
        with pytest.raises(ValueError, match="already exists"):
            create_account(db, test_user.id, _make_account_data(test_currency.id, name="Duplicate"))

    def test_duplicate_name_different_users_allowed(self, db: Session):
        """Two different users can have accounts with the same name."""
        user1 = _make_user(db)
        user2 = _make_user(db)

        cur1 = Currency(id=uuid.uuid4(), user_id=user1.id, ticker="EUR", name="Euro", is_default=False)
        cur2 = Currency(id=uuid.uuid4(), user_id=user2.id, ticker="EUR", name="Euro2", is_default=False)
        db.add_all([cur1, cur2])
        db.flush()

        # Pre-create user1's account via ORM, then CRUD create user2's (one commit)
        _orm_account(db, user1.id, cur1.id, name="Shared Name")
        acc2 = create_account(db, user2.id, _make_account_data(cur2.id, name="Shared Name"))

        assert acc2.account_name == "Shared Name"
        assert acc2.user_id == user2.id

    def test_create_duplicate_inactive_account_allowed(self, db: Session, test_user, test_currency):
        """Duplicate name is only blocked when existing account is active."""
        # Pre-create an INACTIVE account via ORM so create_account can succeed (one commit)
        _orm_account(db, test_user.id, test_currency.id, name="CanRecreate", is_active=False)

        new_account = create_account(db, test_user.id, _make_account_data(test_currency.id, name="CanRecreate"))
        assert new_account.is_active is True

    def test_create_account_persisted_in_db(self, db: Session, test_user, test_currency):
        data = _make_account_data(test_currency.id, name="PersistCheck")
        account = create_account(db, test_user.id, data)

        fetched = get_account(db, test_user.id, account.id)
        assert fetched is not None
        assert fetched.account_name == "PersistCheck"


# ---------------------------------------------------------------------------
# list_accounts
# ---------------------------------------------------------------------------

class TestListAccounts:
    def test_list_empty_for_new_user(self, db: Session, test_user):
        accounts = list_accounts(db, test_user.id)
        assert accounts == []

    def test_list_returns_all_accounts_for_user(self, db: Session, test_user, test_currency):
        for name in ["Account A", "Account B", "Account C"]:
            _orm_account(db, test_user.id, test_currency.id, name=name)

        accounts = list_accounts(db, test_user.id)
        assert len(accounts) == 3

    def test_list_isolates_accounts_by_user(self, db: Session):
        """Each user should only see their own accounts."""
        user1 = _make_user(db)
        user2 = _make_user(db)

        cur1 = Currency(id=uuid.uuid4(), user_id=user1.id, ticker="GBP", name="Pound", is_default=False)
        cur2 = Currency(id=uuid.uuid4(), user_id=user2.id, ticker="GBP", name="Pound2", is_default=False)
        db.add_all([cur1, cur2])
        db.flush()

        _orm_account(db, user1.id, cur1.id, name="User1 Acct")
        _orm_account(db, user2.id, cur2.id, name="User2 Acct")

        user1_accounts = list_accounts(db, user1.id)
        user2_accounts = list_accounts(db, user2.id)

        assert len(user1_accounts) == 1
        assert user1_accounts[0].account_name == "User1 Acct"
        assert len(user2_accounts) == 1
        assert user2_accounts[0].account_name == "User2 Acct"

    def test_list_includes_inactive_accounts(self, db: Session, test_user, test_currency):
        """list_accounts returns all accounts regardless of is_active status."""
        _orm_account(db, test_user.id, test_currency.id, name="InactiveOne", is_active=False)

        accounts = list_accounts(db, test_user.id)
        assert len(accounts) == 1
        assert accounts[0].is_active is False

    def test_list_includes_both_active_and_inactive(self, db: Session, test_user, test_currency):
        _orm_account(db, test_user.id, test_currency.id, name="ActiveAcct", is_active=True)
        _orm_account(db, test_user.id, test_currency.id, name="InactiveAcct", is_active=False)

        accounts = list_accounts(db, test_user.id)
        assert len(accounts) == 2

    def test_list_ordered_by_created_at_descending(self, db: Session, test_user, test_currency):
        """All three accounts returned (order by created_at desc)."""
        _orm_account(db, test_user.id, test_currency.id, name="First")
        _orm_account(db, test_user.id, test_currency.id, name="Second")
        _orm_account(db, test_user.id, test_currency.id, name="Third")

        accounts = list_accounts(db, test_user.id)
        assert len(accounts) == 3
        names = {a.account_name for a in accounts}
        assert names == {"First", "Second", "Third"}


# ---------------------------------------------------------------------------
# get_account
# ---------------------------------------------------------------------------

class TestGetAccount:
    def test_get_existing_account(self, db: Session, test_user, test_currency):
        existing = _orm_account(db, test_user.id, test_currency.id)
        fetched = get_account(db, test_user.id, existing.id)

        assert fetched is not None
        assert fetched.id == existing.id

    def test_get_nonexistent_account_returns_none(self, db: Session, test_user):
        result = get_account(db, test_user.id, uuid.uuid4())
        assert result is None

    def test_get_account_wrong_user_returns_none(self, db: Session, test_user, test_currency):
        """Account owned by test_user must not be visible to a random user_id."""
        account = _orm_account(db, test_user.id, test_currency.id)
        other_user_id = uuid.uuid4()

        result = get_account(db, other_user_id, account.id)
        assert result is None

    def test_get_inactive_account_still_returns(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id, is_active=False)

        fetched = get_account(db, test_user.id, account.id)
        assert fetched is not None
        assert fetched.is_active is False

    def test_get_correct_account_among_many(self, db: Session, test_user, test_currency):
        _orm_account(db, test_user.id, test_currency.id, name="First")
        target = _orm_account(db, test_user.id, test_currency.id, name="Target")
        _orm_account(db, test_user.id, test_currency.id, name="Third")

        fetched = get_account(db, test_user.id, target.id)
        assert fetched.account_name == "Target"


# ---------------------------------------------------------------------------
# deactivate_account
# ---------------------------------------------------------------------------

class TestDeactivateAccount:
    def test_deactivate_sets_is_active_false(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        assert account.is_active is True

        result = deactivate_account(db, test_user.id, account.id)

        assert result is not None
        assert result.is_active is False

    def test_deactivate_returns_account_object(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        result = deactivate_account(db, test_user.id, account.id)

        assert isinstance(result, Account)
        assert result.id == account.id

    def test_deactivate_nonexistent_returns_none(self, db: Session, test_user):
        result = deactivate_account(db, test_user.id, uuid.uuid4())
        assert result is None

    def test_deactivate_wrong_user_returns_none(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        other_user_id = uuid.uuid4()

        result = deactivate_account(db, other_user_id, account.id)
        assert result is None

    def test_deactivate_wrong_user_does_not_change_original(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        other_user_id = uuid.uuid4()

        deactivate_account(db, other_user_id, account.id)

        # Original account should still be active (refresh from DB)
        db.expire(account)
        still_active = get_account(db, test_user.id, account.id)
        assert still_active.is_active is True

    def test_deactivate_already_inactive_is_idempotent(self, db: Session, test_user, test_currency):
        """Deactivating an already-inactive account returns the account and keeps it inactive."""
        account = _orm_account(db, test_user.id, test_currency.id, is_active=False)
        result = deactivate_account(db, test_user.id, account.id)

        assert result is not None
        assert result.is_active is False

    def test_deactivated_account_visible_via_get(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        deactivate_account(db, test_user.id, account.id)

        fetched = get_account(db, test_user.id, account.id)
        assert fetched is not None
        assert fetched.is_active is False


# ---------------------------------------------------------------------------
# delete_account
# ---------------------------------------------------------------------------

class TestDeleteAccount:
    def test_delete_clean_account_returns_true(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        result = delete_account(db, test_user.id, account.id)

        assert result is True

    def test_delete_removes_account_from_db(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        account_id = account.id
        delete_account(db, test_user.id, account_id)

        fetched = get_account(db, test_user.id, account_id)
        assert fetched is None

    def test_delete_nonexistent_returns_false(self, db: Session, test_user):
        result = delete_account(db, test_user.id, uuid.uuid4())
        assert result is False

    def test_delete_wrong_user_returns_false(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        other_user_id = uuid.uuid4()

        result = delete_account(db, other_user_id, account.id)
        assert result is False

    def test_delete_wrong_user_does_not_remove_account(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        delete_account(db, uuid.uuid4(), account.id)

        still_exists = get_account(db, test_user.id, account.id)
        assert still_exists is not None

    def test_delete_with_balance_snapshot_raises(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        period = _make_period(db, test_user.id)

        snapshot = BalanceSnapshot(
            id=uuid.uuid4(),
            calculation_period_id=period.id,
            account_id=account.id,
            balance=500.0,
            snapshot_date=date(2025, 1, 31),
        )
        db.add(snapshot)
        db.flush()

        with pytest.raises(ValueError, match="balance snapshots"):
            delete_account(db, test_user.id, account.id)

    def test_delete_with_investment_transfer_raises(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        period = _make_period(db, test_user.id)
        investment = _make_investment(db, test_user.id)

        transfer = InvestmentTransfer(
            id=uuid.uuid4(),
            investment_id=investment.id,
            calculation_period_id=period.id,
            amount_transferred=100.0,
            currency_id=test_currency.id,
            source_account_id=account.id,
            transfer_date=date(2025, 1, 15),
        )
        db.add(transfer)
        db.flush()

        with pytest.raises(ValueError, match="investment transfers"):
            delete_account(db, test_user.id, account.id)

    def test_delete_snapshot_error_suggests_deactivate(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        period = _make_period(db, test_user.id)
        snapshot = BalanceSnapshot(
            id=uuid.uuid4(),
            calculation_period_id=period.id,
            account_id=account.id,
            balance=100.0,
            snapshot_date=date(2025, 1, 31),
        )
        db.add(snapshot)
        db.flush()

        with pytest.raises(ValueError, match="Deactivate"):
            delete_account(db, test_user.id, account.id)

    def test_delete_transfer_error_suggests_deactivate(self, db: Session, test_user, test_currency):
        account = _orm_account(db, test_user.id, test_currency.id)
        period = _make_period(db, test_user.id)
        investment = _make_investment(db, test_user.id)

        transfer = InvestmentTransfer(
            id=uuid.uuid4(),
            investment_id=investment.id,
            calculation_period_id=period.id,
            amount_transferred=200.0,
            currency_id=test_currency.id,
            source_account_id=account.id,
            transfer_date=date(2025, 1, 20),
        )
        db.add(transfer)
        db.flush()

        with pytest.raises(ValueError, match="Deactivate"):
            delete_account(db, test_user.id, account.id)


# ---------------------------------------------------------------------------
# Multi-account scenarios
# ---------------------------------------------------------------------------

class TestMultiAccountScenarios:
    def test_multiple_accounts_per_user(self, db: Session, test_user, test_currency):
        names = ["Savings", "Checking", "Wallet"]
        types = {"Wallet": "CASH"}
        for name in names:
            _orm_account(db, test_user.id, test_currency.id, name=name, account_type=types.get(name, "BANK"))

        accounts = list_accounts(db, test_user.id)
        assert len(accounts) == 3
        assert {a.account_name for a in accounts} == set(names)

    def test_mixed_active_inactive_accounts_listed(self, db: Session, test_user, test_currency):
        _orm_account(db, test_user.id, test_currency.id, name="Active", is_active=True)
        _orm_account(db, test_user.id, test_currency.id, name="Inactive", is_active=False)

        accounts = list_accounts(db, test_user.id)
        assert len(accounts) == 2

        statuses = {a.account_name: a.is_active for a in accounts}
        assert statuses["Active"] is True
        assert statuses["Inactive"] is False

    def test_get_specific_account_among_multiple(self, db: Session, test_user, test_currency):
        _orm_account(db, test_user.id, test_currency.id, name="First")
        target = _orm_account(db, test_user.id, test_currency.id, name="Second")
        _orm_account(db, test_user.id, test_currency.id, name="Third")

        fetched = get_account(db, test_user.id, target.id)
        assert fetched.account_name == "Second"

    def test_delete_one_account_leaves_others(self, db: Session, test_user, test_currency):
        _orm_account(db, test_user.id, test_currency.id, name="Keep1")
        to_delete = _orm_account(db, test_user.id, test_currency.id, name="DeleteMe")
        _orm_account(db, test_user.id, test_currency.id, name="Keep2")

        delete_account(db, test_user.id, to_delete.id)

        remaining = list_accounts(db, test_user.id)
        assert len(remaining) == 2
        names = {a.account_name for a in remaining}
        assert "DeleteMe" not in names
        assert "Keep1" in names
        assert "Keep2" in names

    def test_create_then_list_contains_new_account(self, db: Session, test_user, test_currency):
        """create_account result should appear in list_accounts."""
        new = create_account(db, test_user.id, _make_account_data(test_currency.id, name="NewAccount"))

        accounts = list_accounts(db, test_user.id)
        ids = {a.id for a in accounts}
        assert new.id in ids
