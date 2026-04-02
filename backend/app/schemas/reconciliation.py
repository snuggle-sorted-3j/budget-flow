from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReconciliationSummary(BaseModel):
    """Breakdown of reconciliation for a single currency."""

    currency_ticker: str
    starting_balance: Decimal
    total_income: Decimal
    total_expenses: Decimal
    total_installments: Decimal
    total_conversions_out: Decimal = Decimal("0.00")
    total_conversions_in: Decimal = Decimal("0.00")
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


class DeductibleItem(BaseModel):
    """A single tax-deductible expense item."""

    item_name: str
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class TaxBenefitsResult(BaseModel):
    """Tax benefit calculation result for a period."""

    tax_system: str
    tax_rate: Decimal
    taxable_income: Decimal
    deductible_expenses: Decimal
    net_taxable_income: Decimal
    estimated_tax: Decimal
    tax_savings: Decimal
    deductible_items: List[DeductibleItem]

    model_config = ConfigDict(from_attributes=True)
