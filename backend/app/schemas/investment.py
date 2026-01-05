from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# --- Investment Account Schemas ---
class InvestmentAccountBase(BaseModel):
    account_name: str = Field(..., max_length=255)
    account_type: str = Field(..., pattern="^(BROKERAGE|CRYPTO_EXCHANGE|PHYSICAL)$")
    notes: Optional[str] = None
    is_active: bool = True

class InvestmentAccountCreate(InvestmentAccountBase):
    pass

class InvestmentAccountUpdate(BaseModel):
    account_name: Optional[str] = Field(None, max_length=255)
    account_type: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class InvestmentAccountResponse(InvestmentAccountBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Investment (Category) Schemas ---
class InvestmentBase(BaseModel):
    category_name: str = Field(..., max_length=255)
    investment_account_id: Optional[UUID] = None
    opening_balance: Optional[Decimal] = None
    opening_balance_date: Optional[date] = None
    opening_balance_currency_id: Optional[UUID] = None

class InvestmentCreate(InvestmentBase):
    pass

class InvestmentResponse(InvestmentBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    # We might want to return details of the associated account/currency
    account_name: Optional[str] = None
    currency_ticker: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Investment Transfer Schemas ---
class InvestmentTransferBase(BaseModel):
    investment_id: UUID
    amount_transferred: Decimal = Field(..., gt=0)
    currency_id: UUID
    source_account_id: UUID
    transfer_date: date
    units_added: Optional[Decimal] = None
    notes: Optional[str] = None

class InvestmentTransferCreate(InvestmentTransferBase):
    pass

class InvestmentTransferResponse(InvestmentTransferBase):
    id: UUID
    calculation_period_id: UUID
    created_at: datetime
    
    # Metadata for display
    investment_category_name: Optional[str] = None
    source_account_name: Optional[str] = None
    currency_ticker: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
