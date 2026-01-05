from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.balance_snapshot import BalanceSnapshot
from app.models.calculation_period import CalculationPeriod
from app.models.currency import Currency
from app.models.expense_item import ExpenseItem
from app.models.income_entry import IncomeEntry
from app.models.installment_payment import InstallmentPayment
from app.models.investment_transfer import InvestmentTransfer
from app.models.suspended_expense import SuspendedExpense
from app.models.currency_conversion import CurrencyConversion
from app.schemas.reconciliation import PeriodReconciliation, ReconciliationSummary


def calculate_reconciliation(
    db: Session, user_id: UUID, period_id: UUID
) -> Optional[PeriodReconciliation]:
    """
    Calculate reconciliation for all currencies in a given period.
    """
    # 1. Get current period
    current_period = db.execute(
        select(CalculationPeriod).where(
            CalculationPeriod.id == period_id, 
            CalculationPeriod.user_id == user_id
        )
    ).scalar_one_or_none()

    if not current_period:
        return None

    # 2. Get previous period (immediately preceding by end_date)
    previous_period = db.execute(
        select(CalculationPeriod)
        .where(
            CalculationPeriod.user_id == user_id,
            CalculationPeriod.snapshot_date < current_period.start_date
        )
        .order_by(CalculationPeriod.snapshot_date.desc())
        .limit(1)
    ).scalar_one_or_none()

    # 3. Get all currencies for the user
    currencies = db.execute(
        select(Currency).where(Currency.user_id == user_id)
    ).scalars().all()

    reconciliations: List[ReconciliationSummary] = []
    overall_balanced = True

    for currency in currencies:
        # a) Get all accounts with this currency
        # b) Get balance snapshots for these accounts in current period
        actual_balance = Decimal("0.00")
        current_snapshots = db.execute(
            select(BalanceSnapshot)
            .join(Account)
            .where(
                BalanceSnapshot.calculation_period_id == current_period.id,
                Account.currency_id == currency.id
            )
        ).scalars().all()
        for snap in current_snapshots:
            actual_balance += snap.balance

        # d) Get starting balance from previous period 
        # (or from opening balances if this is the first period)
        starting_balance = Decimal("0.00")
        if previous_period:
            prev_snapshots = db.execute(
                select(BalanceSnapshot)
                .join(Account)
                .where(
                    BalanceSnapshot.calculation_period_id == previous_period.id,
                    Account.currency_id == currency.id
                )
            ).scalars().all()
            for snap in prev_snapshots:
                starting_balance += snap.balance
        else:
            # Use opening balances for the very first period
            accounts_stmt = select(Account).where(
                Account.user_id == user_id,
                Account.currency_id == currency.id
            )
            accounts = db.execute(accounts_stmt).scalars().all()
            for acc in accounts:
                starting_balance += Decimal(str(acc.opening_balance))

        # e) Sum income entries
        total_income = Decimal("0.00")
        incomes = db.execute(
            select(IncomeEntry).where(
                IncomeEntry.calculation_period_id == current_period.id,
                IncomeEntry.currency_id == currency.id
            )
        ).scalars().all()
        for inc in incomes:
            total_income += inc.amount

        # f) Sum expense items
        total_expenses = Decimal("0.00")
        expenses = db.execute(
            select(ExpenseItem).where(
                ExpenseItem.calculation_period_id == current_period.id,
                ExpenseItem.currency_id == currency.id
            )
        ).scalars().all()
        for exp in expenses:
            total_expenses += exp.amount

        # g) Sum investment transfers (money moving OUT to investments)
        total_transfers = Decimal("0.00")
        transfers = db.execute(
            select(InvestmentTransfer).where(
                InvestmentTransfer.calculation_period_id == current_period.id,
                InvestmentTransfer.currency_id == currency.id
            )
        ).scalars().all()
        for t in transfers:
            total_transfers += t.amount_transferred

        # h) Suspended Out (Money leaving circulation - Loans/Returns initiated)
        total_suspended_out = Decimal("0.00")
        susp_out = db.execute(
            select(SuspendedExpense).where(
                SuspendedExpense.created_period_id == current_period.id,
                SuspendedExpense.currency_id == currency.id,
                SuspendedExpense.status != "CONVERTED_TO_EXPENSE"
            )
        ).scalars().all()
        for s in susp_out:
            total_suspended_out += s.amount

        # i) Suspended In (Money returning - Settled loans/returns)
        total_suspended_in = Decimal("0.00")
        susp_in = db.execute(
            select(SuspendedExpense).where(
                SuspendedExpense.settled_period_id == current_period.id,
                SuspendedExpense.currency_id == currency.id,
                SuspendedExpense.status == "SETTLED"
            )
        ).scalars().all()
        for s in susp_in:
            total_suspended_in += s.amount

        # k) Installment Payments
        total_installments = Decimal("0.00")
        inst_payments = db.execute(
            select(InstallmentPayment).where(
                InstallmentPayment.calculation_period_id == current_period.id,
                # InstallmentPayment doesn't have direct currency_id?
                # It links to InstallmentItem which has currency_id.
                InstallmentPayment.installment_item.has(currency_id=currency.id)
            )
        ).scalars().all()
        for ip in inst_payments:
            total_installments += ip.payment_amount

        # m) Currency Conversions
        total_conversions_out = Decimal("0.00")
        total_conversions_in = Decimal("0.00")
        
        # Conversions FROM this currency
        convs_out = db.execute(
            select(CurrencyConversion).where(
                CurrencyConversion.calculation_period_id == current_period.id,
                CurrencyConversion.from_currency_id == currency.id
            )
        ).scalars().all()
        for co in convs_out:
            total_conversions_out += co.from_amount
            
        # Conversions TO this currency
        convs_in = db.execute(
            select(CurrencyConversion).where(
                CurrencyConversion.calculation_period_id == current_period.id,
                CurrencyConversion.to_currency_id == currency.id
            )
        ).scalars().all()
        for ci in convs_in:
            total_conversions_in += ci.to_amount

        # l) expected_balance = starting + income - expenses - transfers - susp_out + susp_in - installments - conv_out + conv_in
        expected_balance = (
            starting_balance + total_income - total_expenses - total_transfers - 
            total_suspended_out + total_suspended_in - total_installments - 
            total_conversions_out + total_conversions_in
        )
        
        # m) difference = expected_balance - actual_balance
        difference = expected_balance - actual_balance
        is_balanced = (difference == 0)
        
        if not is_balanced:
            overall_balanced = False

        reconciliations.append(
            ReconciliationSummary(
                currency_ticker=currency.ticker,
                starting_balance=starting_balance,
                total_income=total_income,
                total_expenses=total_expenses,
                total_installments=total_installments,
                total_conversions_out=total_conversions_out,
                total_conversions_in=total_conversions_in,
                expected_balance=expected_balance,
                actual_balance=actual_balance,
                difference=difference,
                is_balanced=is_balanced,
            )
        )

    return PeriodReconciliation(
        period_id=current_period.id,
        period_name=current_period.period_name,
        status=current_period.status,
        reconciliations=reconciliations,
        overall_balanced=overall_balanced,
    )
