from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReconciliationSummary(BaseModel):
    """Breakdown of reconciliation for a single currency."""

    currency_ticker: str
    starting_balance: Decimal
    total_income: Decimal
    total_expenses: Decimal
    total_installments: Decimal
    expected_balance: Decimal
    actual_balance: Decimal
    difference: Decimal
    is_balanced: bool

    model_config = ConfigDict(from_attributes=True)


class PeriodReconciliation(BaseModel):
    """Overall reconciliation result for a calculation period."""

    period_id: UUID
    period_name: str
    status: str
    reconciliations: List[ReconciliationSummary]
    overall_balanced: bool

    model_config = ConfigDict(from_attributes=True)
