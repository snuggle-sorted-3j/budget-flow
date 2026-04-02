import io
import csv
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import extract
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.calculation_period import CalculationPeriod
from app.models.expense_item import ExpenseItem
from app.models.income_entry import IncomeEntry
from app.models.expense_category import ExpenseCategory
from app.models.currency import Currency
from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.suspended_expense import SuspendedExpense
from app.models.installment_item import InstallmentItem
from app.models.installment_payment import InstallmentPayment
from app.models.template import Template
from app.models.investment_account import InvestmentAccount
from app.models.investment import Investment
from app.models.investment_transfer import InvestmentTransfer
from app.models.currency_conversion import CurrencyConversion
from app.models.custom_expense_type import CustomExpenseType
from app.models.user_settings import UserSettings
from app.services import analytics_service, reconciliation_service


def _to_dict(obj) -> Dict[str, Any]:
    """Serialize a SQLAlchemy model instance to a JSON-compatible dictionary."""
    d = {}
    for column in obj.__table__.columns:
        val = getattr(obj, column.name)
        if isinstance(val, (date, datetime)):
            val = val.isoformat()
        elif isinstance(val, Decimal):
            val = str(val)
        elif hasattr(val, 'hex'):  # UUID
            val = val.hex
        d[column.name] = val
    return d

def generate_period_csv(db: Session, user_id: Any, period_id: Any) -> bytes:
    """Export all transactions for a specific period as CSV."""
    # Query income
    income = db.query(IncomeEntry).filter(
        IncomeEntry.calculation_period_id == period_id
    ).all()
    
    # Query expenses
    expenses = db.query(ExpenseItem).filter(
        ExpenseItem.calculation_period_id == period_id
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Date", "Type", "Category", "Item/Source", "Amount", "Currency", "Notes", "Tax Deductible", "Recurring"])
    
    # Process Income
    for i in income:
        writer.writerow([
            i.income_date,
            "Income",
            "Income", # Default category for income in this export format
            i.source_name,
            i.amount,
            i.currency.ticker,
            i.notes or "",
            "N/A",
            "Yes" if i.is_recurring else "No"
        ])
        
    # Process Expenses
    for e in expenses:
        writer.writerow([
            e.expense_date,
            "Expense",
            e.category.category_name,
            e.item_name,
            e.amount,
            e.currency.ticker,
            e.notes or "",
            "Yes" if e.is_tax_deductible else "No",
            "Yes" if e.is_recurring else "No"
        ])
        
    return output.getvalue().encode('utf-8')

def generate_reconciliation_pdf(db: Session, user_id: Any, period_id: Any) -> bytes:
    """Generate a detailed PDF reconciliation report."""
    period = db.query(CalculationPeriod).filter(
        CalculationPeriod.id == period_id, 
        CalculationPeriod.user_id == user_id
    ).first()
    
    if not period:
        return b""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"Reconciliation Report: {period.period_name}", styles['Title']))
    elements.append(Paragraph(f"Dates: {period.start_date} to {period.end_date}", styles['Normal']))
    elements.append(Paragraph(f"Status: {period.status}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Reconciliation Data (using existing service logic)
    recon_obj = reconciliation_service.calculate_reconciliation(db, user_id, period_id)
    recon_data = recon_obj.model_dump() if recon_obj else {}
    
    for recon in recon_data.get("reconciliations", []):
        ticker = recon.get("currency_ticker")
        elements.append(Paragraph(f"Currency: {ticker}", styles['Heading2']))
        
        data = [
            ["Item", "Amount"],
            ["Starting Balance", f"{recon.get('starting_balance', 0):.2f}"],
            ["Total Income", f"{recon.get('total_income', 0):.2f}"],
            ["Total Expenses", f"-{recon.get('total_expenses', 0):.2f}"],
            ["Expected Balance", f"{recon.get('expected_balance', 0):.2f}"],
            ["Actual Balance", f"{recon.get('actual_balance', 0) or 0:.2f}"],
            ["Difference", f"{recon.get('difference', 0):.2f}"]
        ]
        
        t = Table(data, colWidths=[200, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

    doc.build(elements)
    return buffer.getvalue()

def generate_annual_csv(db: Session, user_id: Any, year: int) -> bytes:
    """Generate an annual summary CSV."""
    periods = db.query(CalculationPeriod).filter(
        CalculationPeriod.user_id == user_id,
        extract('year', CalculationPeriod.start_date) == year
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Period", "Start Date", "End Date", "Income", "Expenses", "Net"])
    
    for p in sorted(periods, key=lambda x: x.start_date):
        recon_obj = reconciliation_service.calculate_reconciliation(db, user_id, p.id)
        recon_data = recon_obj.model_dump() if recon_obj else {}
        # Summing across all currencies (simplified for annual summary)
        total_inc = sum(r.get("total_income", 0) for r in recon_data.get("reconciliations", []))
        total_exp = sum(r.get("total_expenses", 0) for r in recon_data.get("reconciliations", []))
        
        writer.writerow([
            p.period_name,
            p.start_date,
            p.end_date,
            f"{total_inc:.2f}",
            f"{total_exp:.2f}",
            f"{(total_inc - total_exp):.2f}"
        ])
        
    return output.getvalue().encode('utf-8')

def generate_full_backup_json(db: Session, user_id: Any) -> Dict[str, Any]:
    """Serialize all user financial data to a JSON-compatible dictionary."""
    data: Dict[str, Any] = {
        "version": "1.0",
        "export_date": datetime.now().isoformat(),
    }

    data["currencies"] = [_to_dict(c) for c in db.query(Currency).filter_by(user_id=user_id).all()]
    data["categories"] = [_to_dict(c) for c in db.query(ExpenseCategory).filter_by(user_id=user_id).all()]
    data["periods"] = [_to_dict(p) for p in db.query(CalculationPeriod).filter_by(user_id=user_id).all()]
    data["accounts"] = [_to_dict(a) for a in db.query(Account).filter_by(user_id=user_id).all()]

    period_ids = [p.id for p in db.query(CalculationPeriod).filter_by(user_id=user_id).all()]
    data["income_entries"] = [
        _to_dict(i) for i in db.query(IncomeEntry).filter(
            IncomeEntry.calculation_period_id.in_(period_ids)
        ).all()
    ] if period_ids else []
    data["expense_items"] = [
        _to_dict(e) for e in db.query(ExpenseItem).filter(
            ExpenseItem.calculation_period_id.in_(period_ids)
        ).all()
    ] if period_ids else []

    # Suspended expenses & installments
    data["suspended_expenses"] = [
        _to_dict(s) for s in db.query(SuspendedExpense).filter_by(user_id=user_id).all()
    ]
    data["installment_items"] = [
        _to_dict(i) for i in db.query(InstallmentItem).filter_by(user_id=user_id).all()
    ]
    installment_item_ids = [
        i.id for i in db.query(InstallmentItem).filter_by(user_id=user_id).all()
    ]
    data["installment_payments"] = [
        _to_dict(p) for p in db.query(InstallmentPayment).filter(
            InstallmentPayment.installment_item_id.in_(installment_item_ids)
        ).all()
    ] if installment_item_ids else []

    # Investments
    data["investment_accounts"] = [
        _to_dict(a) for a in db.query(InvestmentAccount).filter_by(user_id=user_id).all()
    ]
    data["investments"] = [
        _to_dict(i) for i in db.query(Investment).filter_by(user_id=user_id).all()
    ]
    investment_ids = [i.id for i in db.query(Investment).filter_by(user_id=user_id).all()]
    data["investment_transfers"] = [
        _to_dict(t) for t in db.query(InvestmentTransfer).filter(
            InvestmentTransfer.investment_id.in_(investment_ids)
        ).all()
    ] if investment_ids else []

    # Currency conversions & balance snapshots
    data["currency_conversions"] = [
        _to_dict(c) for c in db.query(CurrencyConversion).filter(
            CurrencyConversion.calculation_period_id.in_(period_ids)
        ).all()
    ] if period_ids else []
    data["balance_snapshots"] = [
        _to_dict(b) for b in db.query(BalanceSnapshot).filter(
            BalanceSnapshot.calculation_period_id.in_(period_ids)
        ).all()
    ] if period_ids else []

    # Templates & custom expense types
    data["templates"] = [
        _to_dict(t) for t in db.query(Template).filter_by(user_id=user_id).all()
    ]
    data["custom_expense_types"] = [
        _to_dict(c) for c in db.query(CustomExpenseType).filter_by(user_id=user_id).all()
    ]

    # User settings
    settings = db.query(UserSettings).filter_by(user_id=user_id).first()
    data["user_settings"] = _to_dict(settings) if settings else None

    return data

def _resolve_fk(
    uuid_map: Dict[str, "uuid.UUID"], old_hex: Any, nullable: bool = False
) -> Any:
    """Look up an old UUID hex in the map and return the new UUID."""
    if old_hex is None:
        if nullable:
            return None
        raise ValueError(f"Non-nullable FK reference is None")
    key = str(old_hex)
    if key not in uuid_map:
        if nullable:
            return None
        raise ValueError(f"FK reference not found in backup: {key}")
    return uuid_map[key]


def import_backup_json(db: Session, user_id: Any, backup_data: Dict[str, Any]) -> Dict[str, Any]:
    """Import data from a backup JSON with full UUID remapping."""
    import uuid as _uuid

    uuid_map: Dict[str, _uuid.UUID] = {}
    summary: Dict[str, int] = {
        "currencies_imported": 0,
        "custom_expense_types_imported": 0,
        "templates_imported": 0,
        "accounts_imported": 0,
        "categories_imported": 0,
        "periods_imported": 0,
        "investment_accounts_imported": 0,
        "balance_snapshots_imported": 0,
        "income_imported": 0,
        "expenses_imported": 0,
        "suspended_expenses_imported": 0,
        "installment_items_imported": 0,
        "installment_payments_imported": 0,
        "investments_imported": 0,
        "investment_transfers_imported": 0,
        "currency_conversions_imported": 0,
    }

    try:
        # Phase 1: Entities with no FK deps beyond user_id
        for c in backup_data.get("currencies", []):
            existing = db.query(Currency).filter_by(
                user_id=user_id, ticker=c["ticker"]
            ).first()
            if existing:
                uuid_map[str(c["id"])] = existing.id
            else:
                new_id = _uuid.uuid4()
                uuid_map[str(c["id"])] = new_id
                db.add(Currency(
                    id=new_id, user_id=user_id, ticker=c["ticker"],
                    name=c.get("name", c["ticker"]),
                    is_default=c.get("is_default", False),
                ))
                summary["currencies_imported"] += 1

        for ct in backup_data.get("custom_expense_types", []):
            existing = db.query(CustomExpenseType).filter_by(
                user_id=user_id, type_name=ct["type_name"]
            ).first()
            if existing:
                uuid_map[str(ct["id"])] = existing.id
            else:
                new_id = _uuid.uuid4()
                uuid_map[str(ct["id"])] = new_id
                db.add(CustomExpenseType(
                    id=new_id, user_id=user_id, type_name=ct["type_name"],
                    description=ct.get("description"),
                    is_active=ct.get("is_active", True),
                ))
                summary["custom_expense_types_imported"] += 1

        for t in backup_data.get("templates", []):
            new_id = _uuid.uuid4()
            uuid_map[str(t["id"])] = new_id
            db.add(Template(
                id=new_id, user_id=user_id,
                template_name=t["template_name"],
                template_type=t.get("template_type", "EXPENSE_CATEGORIES"),
                template_data=t.get("template_data", {}),
                is_default=t.get("is_default", False),
            ))
            summary["templates_imported"] += 1

        db.flush()

        # Phase 2: Entities depending on Phase 1
        for a in backup_data.get("accounts", []):
            new_id = _uuid.uuid4()
            uuid_map[str(a["id"])] = new_id
            db.add(Account(
                id=new_id, user_id=user_id, account_name=a["account_name"],
                account_type=a.get("account_type", "BANK"),
                currency_id=_resolve_fk(uuid_map, a.get("currency_id")),
                is_active=a.get("is_active", True),
                opening_balance=Decimal(str(a["opening_balance"])) if a.get("opening_balance") else None,
                opening_balance_date=date.fromisoformat(a["opening_balance_date"]) if a.get("opening_balance_date") else None,
            ))
            summary["accounts_imported"] += 1

        # Categories: parents first (parent_category_id is None), then children
        parents = [c for c in backup_data.get("categories", []) if not c.get("parent_category_id")]
        children = [c for c in backup_data.get("categories", []) if c.get("parent_category_id")]

        for cat in parents:
            existing = db.query(ExpenseCategory).filter_by(
                user_id=user_id, category_name=cat["category_name"]
            ).filter(ExpenseCategory.parent_category_id.is_(None)).first()
            if existing:
                uuid_map[str(cat["id"])] = existing.id
            else:
                new_id = _uuid.uuid4()
                uuid_map[str(cat["id"])] = new_id
                db.add(ExpenseCategory(
                    id=new_id, user_id=user_id,
                    category_name=cat["category_name"],
                    icon=cat.get("icon"), sort_order=cat.get("sort_order", 0),
                    is_system_category=cat.get("is_system_category", False),
                    is_active=cat.get("is_active", True),
                ))
                summary["categories_imported"] += 1

        db.flush()

        for cat in children:
            existing = db.query(ExpenseCategory).filter_by(
                user_id=user_id, category_name=cat["category_name"],
                parent_category_id=_resolve_fk(uuid_map, cat["parent_category_id"], nullable=True),
            ).first()
            if existing:
                uuid_map[str(cat["id"])] = existing.id
            else:
                new_id = _uuid.uuid4()
                uuid_map[str(cat["id"])] = new_id
                db.add(ExpenseCategory(
                    id=new_id, user_id=user_id,
                    category_name=cat["category_name"],
                    parent_category_id=_resolve_fk(uuid_map, cat["parent_category_id"], nullable=True),
                    icon=cat.get("icon"), sort_order=cat.get("sort_order", 0),
                    is_system_category=cat.get("is_system_category", False),
                    is_active=cat.get("is_active", True),
                ))
                summary["categories_imported"] += 1

        for p in backup_data.get("periods", []):
            existing = db.query(CalculationPeriod).filter_by(
                user_id=user_id, period_name=p["period_name"]
            ).first()
            if existing:
                uuid_map[str(p["id"])] = existing.id
            else:
                new_id = _uuid.uuid4()
                uuid_map[str(p["id"])] = new_id
                db.add(CalculationPeriod(
                    id=new_id, user_id=user_id, period_name=p["period_name"],
                    start_date=date.fromisoformat(p["start_date"]),
                    end_date=date.fromisoformat(p["end_date"]),
                    snapshot_date=date.fromisoformat(p["snapshot_date"]),
                    status=p.get("status", "DRAFT"),
                ))
                summary["periods_imported"] += 1

        for ia in backup_data.get("investment_accounts", []):
            new_id = _uuid.uuid4()
            uuid_map[str(ia["id"])] = new_id
            db.add(InvestmentAccount(
                id=new_id, user_id=user_id, account_name=ia["account_name"],
                account_type=ia.get("account_type", "BROKERAGE"),
                notes=ia.get("notes"), is_active=ia.get("is_active", True),
            ))
            summary["investment_accounts_imported"] += 1

        db.flush()

        # Phase 3: Entities depending on Phase 2
        for bs in backup_data.get("balance_snapshots", []):
            new_id = _uuid.uuid4()
            uuid_map[str(bs["id"])] = new_id
            db.add(BalanceSnapshot(
                id=new_id,
                calculation_period_id=_resolve_fk(uuid_map, bs["calculation_period_id"]),
                account_id=_resolve_fk(uuid_map, bs["account_id"]),
                balance=Decimal(str(bs["balance"])),
                snapshot_date=date.fromisoformat(bs["snapshot_date"]),
            ))
            summary["balance_snapshots_imported"] += 1

        for i in backup_data.get("income_entries", []):
            new_id = _uuid.uuid4()
            uuid_map[str(i["id"])] = new_id
            db.add(IncomeEntry(
                id=new_id,
                calculation_period_id=_resolve_fk(uuid_map, i["calculation_period_id"]),
                source_name=i["source_name"],
                amount=Decimal(str(i["amount"])),
                currency_id=_resolve_fk(uuid_map, i["currency_id"]),
                income_date=date.fromisoformat(i["income_date"]) if i.get("income_date") else None,
                notes=i.get("notes"),
                is_recurring=i.get("is_recurring", False),
                tax_applicable=i.get("tax_applicable", False),
            ))
            summary["income_imported"] += 1

        for e in backup_data.get("expense_items", []):
            new_id = _uuid.uuid4()
            uuid_map[str(e["id"])] = new_id
            db.add(ExpenseItem(
                id=new_id,
                calculation_period_id=_resolve_fk(uuid_map, e["calculation_period_id"]),
                category_id=_resolve_fk(uuid_map, e["category_id"]),
                item_name=e["item_name"],
                amount=Decimal(str(e["amount"])),
                currency_id=_resolve_fk(uuid_map, e["currency_id"]),
                expense_date=date.fromisoformat(e["expense_date"]) if e.get("expense_date") else None,
                expense_type=e.get("expense_type", "REGULAR"),
                is_tax_deductible=e.get("is_tax_deductible", False),
                tax_category=e.get("tax_category"),
                notes=e.get("notes"),
                is_recurring=e.get("is_recurring", False),
            ))
            summary["expenses_imported"] += 1

        for se in backup_data.get("suspended_expenses", []):
            new_id = _uuid.uuid4()
            uuid_map[str(se["id"])] = new_id
            db.add(SuspendedExpense(
                id=new_id, user_id=user_id, item_name=se["item_name"],
                amount=Decimal(str(se["amount"])),
                currency_id=_resolve_fk(uuid_map, se["currency_id"]),
                transaction_type=se.get("transaction_type", "OTHER"),
                status=se.get("status", "PENDING"),
                created_period_id=_resolve_fk(uuid_map, se.get("created_period_id"), nullable=True),
                settled_period_id=_resolve_fk(uuid_map, se.get("settled_period_id"), nullable=True),
                notes=se.get("notes"),
            ))
            summary["suspended_expenses_imported"] += 1

        for ii in backup_data.get("installment_items", []):
            new_id = _uuid.uuid4()
            uuid_map[str(ii["id"])] = new_id
            db.add(InstallmentItem(
                id=new_id, user_id=user_id, item_name=ii["item_name"],
                total_price=Decimal(str(ii["total_price"])),
                currency_id=_resolve_fk(uuid_map, ii["currency_id"]),
                initial_period_id=_resolve_fk(uuid_map, ii.get("initial_period_id"), nullable=True),
                remaining_balance=Decimal(str(ii["remaining_balance"])),
                monthly_payment_amount=Decimal(str(ii.get("monthly_payment_amount", 0))),
                months_to_pay=ii.get("months_to_pay", 0),
                status=ii.get("status", "ACTIVE"),
                notes=ii.get("notes"),
            ))
            summary["installment_items_imported"] += 1

        db.flush()

        # Phase 4: Entities depending on Phase 3
        for ip in backup_data.get("installment_payments", []):
            new_id = _uuid.uuid4()
            uuid_map[str(ip["id"])] = new_id
            db.add(InstallmentPayment(
                id=new_id,
                installment_item_id=_resolve_fk(uuid_map, ip["installment_item_id"]),
                calculation_period_id=_resolve_fk(uuid_map, ip["calculation_period_id"]),
                payment_amount=Decimal(str(ip["payment_amount"])),
                payment_date=date.fromisoformat(ip["payment_date"]) if ip.get("payment_date") else None,
                notes=ip.get("notes"),
            ))
            summary["installment_payments_imported"] += 1

        for inv in backup_data.get("investments", []):
            new_id = _uuid.uuid4()
            uuid_map[str(inv["id"])] = new_id
            db.add(Investment(
                id=new_id, user_id=user_id, category_name=inv["category_name"],
                investment_account_id=_resolve_fk(uuid_map, inv.get("investment_account_id"), nullable=True),
                opening_balance=Decimal(str(inv["opening_balance"])) if inv.get("opening_balance") else None,
                opening_balance_date=date.fromisoformat(inv["opening_balance_date"]) if inv.get("opening_balance_date") else None,
                opening_balance_currency_id=_resolve_fk(uuid_map, inv.get("opening_balance_currency_id"), nullable=True),
            ))
            summary["investments_imported"] += 1

        db.flush()

        # Phase 5: Leaf entities
        for it in backup_data.get("investment_transfers", []):
            new_id = _uuid.uuid4()
            uuid_map[str(it["id"])] = new_id
            db.add(InvestmentTransfer(
                id=new_id,
                investment_id=_resolve_fk(uuid_map, it["investment_id"]),
                calculation_period_id=_resolve_fk(uuid_map, it["calculation_period_id"]),
                amount_transferred=Decimal(str(it["amount_transferred"])),
                currency_id=_resolve_fk(uuid_map, it["currency_id"]),
                source_account_id=_resolve_fk(uuid_map, it["source_account_id"]),
                transfer_date=date.fromisoformat(it["transfer_date"]),
            ))
            summary["investment_transfers_imported"] += 1

        for cc in backup_data.get("currency_conversions", []):
            new_id = _uuid.uuid4()
            uuid_map[str(cc["id"])] = new_id
            db.add(CurrencyConversion(
                id=new_id,
                calculation_period_id=_resolve_fk(uuid_map, cc["calculation_period_id"]),
                from_currency_id=_resolve_fk(uuid_map, cc["from_currency_id"]),
                to_currency_id=_resolve_fk(uuid_map, cc["to_currency_id"]),
                from_amount=Decimal(str(cc["from_amount"])),
                to_amount=Decimal(str(cc["to_amount"])),
                rate=Decimal(str(cc["rate"])),
                conversion_date=date.fromisoformat(cc["conversion_date"]),
                source_account_id=_resolve_fk(uuid_map, cc.get("source_account_id"), nullable=True),
                notes=cc.get("notes"),
            ))
            summary["currency_conversions_imported"] += 1

        db.commit()

    except Exception:
        db.rollback()
        raise

    return summary
