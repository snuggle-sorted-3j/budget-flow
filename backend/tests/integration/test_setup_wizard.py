"""Integration tests for the Initial Setup Wizard endpoint."""
import pytest
import uuid
from datetime import date

pytestmark = pytest.mark.integration

from app.models.account import Account
from app.models.calculation_period import CalculationPeriod
from app.models.currency import Currency


def test_setup_status_new_user_needs_setup(client, db, test_user, auth_headers):
    """A brand-new user with no accounts or periods needs setup."""
    resp = client.get("/api/v1/auth/setup-status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["needs_setup"] is True
    assert "accounts" in data["missing"]
    assert "periods" in data["missing"]


def test_setup_status_after_account_created(client, db, test_user, auth_headers):
    """Still needs setup when account exists but no period."""
    curr = Currency(
        id=uuid.uuid4(), user_id=test_user.id,
        ticker="USD", name="Dollar", is_default=True
    )
    db.add(curr)
    db.commit()
    acct = Account(
        id=uuid.uuid4(), user_id=test_user.id,
        account_name="Bank", account_type="BANK",
        currency_id=curr.id, is_active=True,
        opening_balance=0
    )
    db.add(acct)
    db.commit()

    resp = client.get("/api/v1/auth/setup-status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["needs_setup"] is True
    assert "periods" in data["missing"]
    assert "accounts" not in data["missing"]


def test_setup_status_complete_no_setup_needed(client, db, test_user, auth_headers):
    """User with at least 1 account and 1 period does not need setup."""
    curr = Currency(
        id=uuid.uuid4(), user_id=test_user.id,
        ticker="EUR", name="Euro", is_default=True
    )
    db.add(curr)
    db.commit()
    acct = Account(
        id=uuid.uuid4(), user_id=test_user.id,
        account_name="Main", account_type="BANK",
        currency_id=curr.id, is_active=True,
        opening_balance=0
    )
    period = CalculationPeriod(
        id=uuid.uuid4(), user_id=test_user.id,
        period_name="Jan 2024",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        snapshot_date=date(2024, 1, 31),
        status="DRAFT"
    )
    db.add_all([acct, period])
    db.commit()

    resp = client.get("/api/v1/auth/setup-status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["needs_setup"] is False
    assert data["missing"] == []


def test_setup_status_requires_auth(client):
    """Setup status endpoint must be authenticated."""
    resp = client.get("/api/v1/auth/setup-status")
    assert resp.status_code == 401


def test_setup_status_has_currencies_count(client, db, test_user, auth_headers):
    """Setup status response includes count of existing currencies."""
    curr = Currency(
        id=uuid.uuid4(), user_id=test_user.id,
        ticker="PLN", name="Zloty", is_default=True
    )
    db.add(curr)
    db.commit()

    resp = client.get("/api/v1/auth/setup-status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["currencies_count"] >= 1
