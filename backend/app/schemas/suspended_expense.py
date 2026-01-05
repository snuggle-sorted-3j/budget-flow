from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class SuspendedExpenseBase(BaseModel):
    item_name: str
    amount: Decimal = Field(..., gt=0)
    currency_id: UUID
    transaction_type: str  # LOAN_OUT, PURCHASE_RETURN, OTHER
    notes: Optional[str] = None

class SuspendedExpenseCreate(SuspendedExpenseBase):
    pass

class SuspendedExpenseUpdate(BaseModel):
    item_name: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    settled_period_id: Optional[UUID] = None

class SuspendedExpenseResponse(SuspendedExpenseBase):
    id: UUID
    user_id: UUID
    status: str
    created_period_id: UUID
    settled_period_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    # Metadata for UI
    currency_ticker: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
