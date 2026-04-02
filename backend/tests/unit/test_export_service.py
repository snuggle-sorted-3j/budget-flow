import pytest

pytestmark = pytest.mark.unit

from uuid import uuid4, UUID
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
import json
import pandas as pd
from app.services import export_service
from app.services.export_service import _to_dict
from app.models.calculation_period import CalculationPeriod
from app.models.expense_item import ExpenseItem
from app.models.expense_category import ExpenseCategory
from app.models.currency import Currency
from app.models.income_entry import IncomeEntry
from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.suspended_expense import SuspendedExpense
from app.models.installment_item import InstallmentItem
from app.models.installment_payment import InstallmentPayment
from app.models.investment_account import InvestmentAccount
from app.models.investment import Investment
from app.models.investment_transfer import InvestmentTransfer
from app.models.currency_conversion import CurrencyConversion
from app.models.template import Template
from app.models.custom_expense_type import CustomExpenseType
from app.models.user import User
from app.core.security import get_password_hash

def test_generate_period_csv(db, test_user):
    # Setup
    curr = Currency(id=uuid4(), user_id=test_user.id, ticker="USD", name="Dollar", is_default=True)
    cat = ExpenseCategory(id=uuid4(), user_id=test_user.id, category_name="Food", is_active=True)
    db.add_all([curr, cat])
    db.commit()
    
    p = CalculationPeriod(
        id=uuid4(), user_id=test_user.id, period_name="Jan 2024", 
        start_date=date(2024, 1, 1), end_date=date(2024, 1, 31), 
        snapshot_date=date(2024, 1, 31), status="FINALIZED"
    )
    db.add(p)
    db.commit()
    
    e = ExpenseItem(
        id=uuid4(), category_id=cat.id, calculation_period_id=p.id, 
        item_name="Groceries", amount=100.0, currency_id=curr.id, 
        expense_date=date(2024, 1, 5)
    )
    i = IncomeEntry(
        id=uuid4(), calculation_period_id=p.id, source_name="Salary", 
        amount=5000.0, currency_id=curr.id, income_date=date(2024, 1, 1)
    )
    db.add_all([e, i])
    db.commit()
    
    csv_bytes = export_service.generate_period_csv(db, test_user.id, p.id)
    assert isinstance(csv_bytes, bytes)
    
    df = pd.read_csv(BytesIO(csv_bytes))
    assert len(df) == 2
    assert "Groceries" in df["Item/Source"].values
    assert "Salary" in df["Item/Source"].values

def test_generate_full_backup_json(db, test_user):
    # Setup some data
    curr = Currency(id=uuid4(), user_id=test_user.id, ticker="EUR", name="Euro", is_default=True)
    db.add(curr)
    db.commit()
    
    backup = export_service.generate_full_backup_json(db, test_user.id)
    assert "currencies" in backup
    assert len(backup["currencies"]) >= 1
    assert backup["currencies"][0]["ticker"] == "EUR"
    assert "version" in backup

def test_import_backup_json(db, test_user):
    # Create a small backup dict
    cat_id = str(uuid4())
    backup_data = {
        "version": "1.0",
        "categories": [{
            "id": cat_id,
            "category_name": "Imported Category",
            "is_active": True,
            "is_system_category": False,
            "sort_order": 0
        }],
        "currencies": [],
        "periods": [],
        "accounts": [],
        "income_entries": [],
        "expense_items": [],
        "suspended_expenses": [],
        "installment_items": [],
        "templates": []
    }
    
    result = export_service.import_backup_json(db, test_user.id, backup_data)
    assert result["categories_imported"] == 1
    
    # Verify in DB
    cat = db.query(ExpenseCategory).filter_by(category_name="Imported Category", user_id=test_user.id).first()
    assert cat is not None


def test_to_dict_handles_decimal_fields(db, test_user):
    """_to_dict should serialize Decimal fields as strings to preserve precision."""
    curr = Currency(id=uuid4(), user_id=test_user.id, ticker="GBP", name="Pound", is_default=False)
    db.add(curr)
    db.commit()

    p = CalculationPeriod(
        id=uuid4(), user_id=test_user.id, period_name="Dec Test",
        start_date=date(2024, 12, 1), end_date=date(2024, 12, 31),
        snapshot_date=date(2024, 12, 31), status="DRAFT"
    )
    db.add(p)
    db.commit()

    income = IncomeEntry(
        id=uuid4(), calculation_period_id=p.id, source_name="Freelance",
        amount=Decimal("1234.56"), currency_id=curr.id, income_date=date(2024, 12, 15)
    )
    db.add(income)
    db.commit()

    result = _to_dict(income)
    assert result["amount"] == "1234.56"
    # Must be JSON-serializable
    json.dumps(result)


def test_to_dict_handles_uuid_fields(db, test_user):
    """_to_dict should serialize UUID fields as hex strings."""
    curr = Currency(id=uuid4(), user_id=test_user.id, ticker="JPY", name="Yen", is_default=False)
    db.add(curr)
    db.commit()

    result = _to_dict(curr)
    assert isinstance(result["id"], str)
    assert isinstance(result["user_id"], str)
    # Should be valid hex (no dashes)
    UUID(result["id"])
    UUID(result["user_id"])


def test_to_dict_handles_date_and_datetime(db, test_user):
    """_to_dict should serialize date/datetime to ISO format strings."""
    p = CalculationPeriod(
        id=uuid4(), user_id=test_user.id, period_name="Date Test",
        start_date=date(2024, 6, 1), end_date=date(2024, 6, 30),
        snapshot_date=date(2024, 6, 30), status="DRAFT"
    )
    db.add(p)
    db.commit()

    result = _to_dict(p)
    assert result["start_date"] == "2024-06-01"
    assert result["end_date"] == "2024-06-30"
    # created_at should be an ISO datetime string
    if result["created_at"] is not None:
        datetime.fromisoformat(result["created_at"])


def _create_full_dataset(db, user):
    """Helper to create one record of every entity type for a user."""
    curr = Currency(id=uuid4(), user_id=user.id, ticker="PLN", name="Zloty", is_default=True)
    curr2 = Currency(id=uuid4(), user_id=user.id, ticker="EUR", name="Euro", is_default=False)
    db.add_all([curr, curr2])
    db.flush()

    acct = Account(
        id=uuid4(), user_id=user.id, account_name="Main Bank",
        account_type="BANK", currency_id=curr.id, is_active=True,
        opening_balance=Decimal("1000.00"), opening_balance_date=date(2024, 1, 1)
    )
    db.add(acct)
    db.flush()

    parent_cat = ExpenseCategory(
        id=uuid4(), user_id=user.id, category_name="Living", is_active=True, sort_order=1
    )
    db.add(parent_cat)
    db.flush()
    child_cat = ExpenseCategory(
        id=uuid4(), user_id=user.id, category_name="Rent",
        parent_category_id=parent_cat.id, is_active=True, sort_order=2
    )
    db.add(child_cat)
    db.flush()

    period = CalculationPeriod(
        id=uuid4(), user_id=user.id, period_name="Jan 2024",
        start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        snapshot_date=date(2024, 1, 31), status="DRAFT"
    )
    db.add(period)
    db.flush()

    snap = BalanceSnapshot(
        id=uuid4(), calculation_period_id=period.id, account_id=acct.id,
        balance=Decimal("1500.00"), snapshot_date=date(2024, 1, 31)
    )
    db.add(snap)

    income = IncomeEntry(
        id=uuid4(), calculation_period_id=period.id, source_name="Salary",
        amount=Decimal("5000.00"), currency_id=curr.id, income_date=date(2024, 1, 5)
    )
    db.add(income)

    expense = ExpenseItem(
        id=uuid4(), calculation_period_id=period.id, category_id=child_cat.id,
        item_name="Apartment Rent", amount=Decimal("2000.00"), currency_id=curr.id,
        expense_date=date(2024, 1, 10)
    )
    db.add(expense)

    suspended = SuspendedExpense(
        id=uuid4(), user_id=user.id, item_name="Refund Pending",
        amount=Decimal("150.00"), currency_id=curr.id,
        transaction_type="PURCHASE_RETURN", status="PENDING",
        created_period_id=period.id
    )
    db.add(suspended)

    installment = InstallmentItem(
        id=uuid4(), user_id=user.id, item_name="Laptop",
        total_price=Decimal("4000.00"), currency_id=curr.id,
        initial_period_id=period.id, remaining_balance=Decimal("3500.00"),
        monthly_payment_amount=Decimal("500.00"), months_to_pay=8, status="ACTIVE"
    )
    db.add(installment)
    db.flush()

    payment = InstallmentPayment(
        id=uuid4(), installment_item_id=installment.id,
        calculation_period_id=period.id, payment_amount=Decimal("500.00"),
        payment_date=date(2024, 1, 15)
    )
    db.add(payment)

    inv_acct = InvestmentAccount(
        id=uuid4(), user_id=user.id, account_name="Brokerage",
        account_type="BROKERAGE", is_active=True
    )
    db.add(inv_acct)
    db.flush()

    investment = Investment(
        id=uuid4(), user_id=user.id, category_name="ETFs",
        investment_account_id=inv_acct.id, opening_balance=Decimal("0.00"),
        opening_balance_date=date(2024, 1, 1), opening_balance_currency_id=curr.id
    )
    db.add(investment)
    db.flush()

    transfer = InvestmentTransfer(
        id=uuid4(), investment_id=investment.id, calculation_period_id=period.id,
        amount_transferred=Decimal("1000.00"), currency_id=curr.id,
        source_account_id=acct.id, transfer_date=date(2024, 1, 20)
    )
    db.add(transfer)

    conversion = CurrencyConversion(
        id=uuid4(), calculation_period_id=period.id,
        from_currency_id=curr.id, to_currency_id=curr2.id,
        from_amount=Decimal("1000.00"), to_amount=Decimal("230.00"),
        rate=Decimal("0.230000"), conversion_date=date(2024, 1, 25),
        source_account_id=acct.id
    )
    db.add(conversion)

    template = Template(
        id=uuid4(), user_id=user.id, template_name="Monthly Basics",
        template_type="EXPENSE_CATEGORIES",
        template_data={"categories": ["Rent", "Food", "Transport"]},
        is_default=False
    )
    db.add(template)

    custom_type = CustomExpenseType(
        id=uuid4(), user_id=user.id, type_name="Subscription",
        description="Monthly subscriptions", is_active=True
    )
    db.add(custom_type)

    db.commit()
    return {
        "currency": curr, "currency2": curr2, "account": acct,
        "parent_cat": parent_cat, "child_cat": child_cat, "period": period,
    }


def test_full_backup_includes_all_entity_types(db, test_user):
    """Full backup should include all entity types."""
    _create_full_dataset(db, test_user)

    backup = export_service.generate_full_backup_json(db, test_user.id)

    # Verify all keys exist
    expected_keys = [
        "version", "export_date", "currencies", "categories", "periods", "accounts",
        "income_entries", "expense_items", "suspended_expenses", "installment_items",
        "installment_payments", "investment_accounts", "investments",
        "investment_transfers", "currency_conversions", "balance_snapshots",
        "templates", "custom_expense_types", "user_settings",
    ]
    for key in expected_keys:
        assert key in backup, f"Missing key: {key}"

    # Verify non-empty for entities we created
    assert len(backup["currencies"]) >= 2
    assert len(backup["categories"]) >= 2
    assert len(backup["periods"]) >= 1
    assert len(backup["accounts"]) >= 1
    assert len(backup["income_entries"]) >= 1
    assert len(backup["expense_items"]) >= 1
    assert len(backup["suspended_expenses"]) >= 1
    assert len(backup["installment_items"]) >= 1
    assert len(backup["installment_payments"]) >= 1
    assert len(backup["investment_accounts"]) >= 1
    assert len(backup["investments"]) >= 1
    assert len(backup["investment_transfers"]) >= 1
    assert len(backup["currency_conversions"]) >= 1
    assert len(backup["balance_snapshots"]) >= 1
    assert len(backup["templates"]) >= 1
    assert len(backup["custom_expense_types"]) >= 1

    # Verify JSON-serializable
    json.dumps(backup)


def test_full_backup_excludes_other_users_data(db, test_user):
    """Backup for user A must not contain user B's data."""
    _create_full_dataset(db, test_user)

    # Create user B with some data
    user_b = User(
        id=uuid4(), email=f"other-{uuid4()}@test.com",
        password_hash=get_password_hash("pw123"), full_name="Other User", is_active=True
    )
    db.add(user_b)
    db.commit()
    curr_b = Currency(id=uuid4(), user_id=user_b.id, ticker="CHF", name="Franc", is_default=True)
    db.add(curr_b)
    db.commit()

    # Export user A's backup
    backup = export_service.generate_full_backup_json(db, test_user.id)

    # None of user B's data should appear
    currency_tickers = [c["ticker"] for c in backup["currencies"]]
    assert "CHF" not in currency_tickers


def test_import_currencies_with_uuid_remapping(db, test_user):
    """Imported currencies get new UUIDs, not the ones from the backup."""
    old_id = uuid4().hex
    backup = {
        "version": "1.0",
        "currencies": [{"id": old_id, "ticker": "SEK", "name": "Krona", "is_default": False}],
    }
    result = export_service.import_backup_json(db, test_user.id, backup)
    assert result["currencies_imported"] == 1

    imported = db.query(Currency).filter_by(user_id=test_user.id, ticker="SEK").first()
    assert imported is not None
    assert imported.id.hex != old_id  # new UUID assigned


def test_import_accounts_resolves_currency_fk(db, test_user):
    """Imported accounts should resolve currency_id via UUID map."""
    curr_id = uuid4().hex
    acct_id = uuid4().hex
    backup = {
        "version": "1.0",
        "currencies": [{"id": curr_id, "ticker": "NOK", "name": "Krone", "is_default": True}],
        "accounts": [{
            "id": acct_id, "account_name": "Savings", "account_type": "BANK",
            "currency_id": curr_id, "is_active": True,
            "opening_balance": "500.00", "opening_balance_date": "2024-01-01",
        }],
    }
    result = export_service.import_backup_json(db, test_user.id, backup)
    assert result["currencies_imported"] == 1
    assert result["accounts_imported"] == 1

    acct = db.query(Account).filter_by(user_id=test_user.id, account_name="Savings").first()
    curr = db.query(Currency).filter_by(user_id=test_user.id, ticker="NOK").first()
    assert acct is not None
    assert acct.currency_id == curr.id


def test_import_categories_handles_hierarchy(db, test_user):
    """Import should correctly wire parent/child category relationships."""
    parent_id = uuid4().hex
    child_id = uuid4().hex
    backup = {
        "version": "1.0",
        "categories": [
            {"id": parent_id, "category_name": "Transport", "parent_category_id": None,
             "is_active": True, "sort_order": 1},
            {"id": child_id, "category_name": "Gas", "parent_category_id": parent_id,
             "is_active": True, "sort_order": 2},
        ],
    }
    result = export_service.import_backup_json(db, test_user.id, backup)
    assert result["categories_imported"] == 2

    parent = db.query(ExpenseCategory).filter_by(
        user_id=test_user.id, category_name="Transport"
    ).first()
    child = db.query(ExpenseCategory).filter_by(
        user_id=test_user.id, category_name="Gas"
    ).first()
    assert parent is not None
    assert child is not None
    assert child.parent_category_id == parent.id


def test_import_skips_duplicate_currencies(db, test_user):
    """Importing the same backup twice should skip duplicate currencies."""
    backup = {
        "version": "1.0",
        "currencies": [{"id": uuid4().hex, "ticker": "DKK", "name": "Krone", "is_default": False}],
    }
    r1 = export_service.import_backup_json(db, test_user.id, backup)
    assert r1["currencies_imported"] == 1

    r2 = export_service.import_backup_json(db, test_user.id, backup)
    assert r2["currencies_imported"] == 0

    count = db.query(Currency).filter_by(user_id=test_user.id, ticker="DKK").count()
    assert count == 1


def test_round_trip_export_import(db, test_user):
    """Export user A's full data, import into user B, verify all entity counts and key fields."""
    _create_full_dataset(db, test_user)

    # Export user A
    backup = export_service.generate_full_backup_json(db, test_user.id)
    # Prove JSON round-trip works
    backup_json = json.dumps(backup)
    backup_parsed = json.loads(backup_json)

    # Create user B
    user_b = User(
        id=uuid4(), email=f"roundtrip-{uuid4()}@test.com",
        password_hash=get_password_hash("pw123"), full_name="User B", is_active=True
    )
    db.add(user_b)
    db.commit()

    # Import into user B
    result = export_service.import_backup_json(db, user_b.id, backup_parsed)

    # Verify counts match
    assert result["currencies_imported"] == len(backup["currencies"])
    assert result["categories_imported"] == len(backup["categories"])
    assert result["periods_imported"] == len(backup["periods"])
    assert result["accounts_imported"] == len(backup["accounts"])
    assert result["income_imported"] == len(backup["income_entries"])
    assert result["expenses_imported"] == len(backup["expense_items"])
    assert result["suspended_expenses_imported"] == len(backup["suspended_expenses"])
    assert result["installment_items_imported"] == len(backup["installment_items"])
    assert result["installment_payments_imported"] == len(backup["installment_payments"])
    assert result["investment_accounts_imported"] == len(backup["investment_accounts"])
    assert result["investments_imported"] == len(backup["investments"])
    assert result["investment_transfers_imported"] == len(backup["investment_transfers"])
    assert result["currency_conversions_imported"] == len(backup["currency_conversions"])
    assert result["balance_snapshots_imported"] == len(backup["balance_snapshots"])
    assert result["templates_imported"] == len(backup["templates"])
    assert result["custom_expense_types_imported"] == len(backup["custom_expense_types"])

    # Verify key field values survived
    b_currencies = db.query(Currency).filter_by(user_id=user_b.id).all()
    b_tickers = {c.ticker for c in b_currencies}
    assert "PLN" in b_tickers
    assert "EUR" in b_tickers

    b_income = db.query(IncomeEntry).join(CalculationPeriod).filter(
        CalculationPeriod.user_id == user_b.id
    ).all()
    assert len(b_income) >= 1
    assert b_income[0].source_name == "Salary"
    assert b_income[0].amount == Decimal("5000.00")

    # Verify FK consistency: expense items point to user B's categories
    b_expenses = db.query(ExpenseItem).join(CalculationPeriod).filter(
        CalculationPeriod.user_id == user_b.id
    ).all()
    b_category_ids = {c.id for c in db.query(ExpenseCategory).filter_by(user_id=user_b.id).all()}
    for exp in b_expenses:
        assert exp.category_id in b_category_ids

    # Verify no data from user A leaked
    for curr in b_currencies:
        assert curr.user_id == user_b.id


def test_import_empty_backup(db, test_user):
    """Importing an empty backup should succeed with zero counts."""
    result = export_service.import_backup_json(db, test_user.id, {"version": "1.0"})
    for v in result.values():
        assert v == 0


def test_export_user_with_no_data(db, test_user):
    """Exporting for a user with no data should return valid JSON with empty arrays."""
    backup = export_service.generate_full_backup_json(db, test_user.id)
    assert backup["version"] == "1.0"
    assert backup["currencies"] == []
    assert backup["periods"] == []
    assert backup["user_settings"] is None
    # Must be JSON-serializable
    json.dumps(backup)


def test_import_with_missing_fk_reference(db, test_user):
    """Import should raise ValueError when an expense references a missing category."""
    backup = {
        "version": "1.0",
        "currencies": [{"id": uuid4().hex, "ticker": "TST", "name": "Test", "is_default": True}],
        "periods": [{"id": uuid4().hex, "period_name": "X", "start_date": "2024-01-01",
                      "end_date": "2024-01-31", "snapshot_date": "2024-01-31", "status": "DRAFT"}],
        "expense_items": [{
            "id": uuid4().hex, "calculation_period_id": uuid4().hex,  # unknown period
            "category_id": uuid4().hex,  # unknown category
            "item_name": "Ghost", "amount": "10.00",
            "currency_id": uuid4().hex,  # unknown currency
            "expense_date": "2024-01-15",
        }],
    }
    with pytest.raises(ValueError, match="FK reference not found"):
        export_service.import_backup_json(db, test_user.id, backup)


def test_import_idempotent_natural_keys(db, test_user):
    """Second import of same backup should skip natural-keyed entities, add transactions."""
    _create_full_dataset(db, test_user)
    backup = export_service.generate_full_backup_json(db, test_user.id)
    backup_parsed = json.loads(json.dumps(backup))

    user_b = User(
        id=uuid4(), email=f"idempotent-{uuid4()}@test.com",
        password_hash=get_password_hash("pw123"), full_name="Idemp User", is_active=True
    )
    db.add(user_b)
    db.commit()

    r1 = export_service.import_backup_json(db, user_b.id, backup_parsed)
    r2 = export_service.import_backup_json(db, user_b.id, backup_parsed)

    # Natural-keyed: currencies, categories, periods should be 0 on second import
    assert r2["currencies_imported"] == 0
    assert r2["categories_imported"] == 0
    assert r2["periods_imported"] == 0
