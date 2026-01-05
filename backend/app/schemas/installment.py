from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# --- Payment Schemas ---

class InstallmentPaymentBase(BaseModel):
    payment_amount: Decimal = Field(..., gt=0)
    payment_date: date
    notes: Optional[str] = None

class InstallmentPaymentCreate(InstallmentPaymentBase):
    pass

class InstallmentPaymentResponse(InstallmentPaymentBase):
    id: UUID
    installment_item_id: UUID
    calculation_period_id: UUID
    created_at: datetime
    
    # helper for UI?
    period_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Item Schemas ---

class InstallmentItemBase(BaseModel):
    item_name: str = Field(..., max_length=255)
    total_price: Decimal = Field(..., gt=0)
    currency_id: UUID
    monthly_payment_amount: Optional[Decimal] = Field(None, gt=0)
    months_to_pay: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None

class InstallmentItemCreate(InstallmentItemBase):
    initial_period_id: UUID

class InstallmentItemResponse(InstallmentItemBase):
    id: UUID
    user_id: UUID
    initial_period_id: UUID
    remaining_balance: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Relationships/Computed
    currency_ticker: Optional[str] = None
    
    # We might want to embed payments sometimes? 
    # For now, let's keep it separate or include last payment info?
    # Simple response is fine.

    model_config = ConfigDict(from_attributes=True)
