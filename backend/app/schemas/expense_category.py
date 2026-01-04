from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ExpenseCategoryBase(BaseModel):
    """Base schema for ExpenseCategory."""

    category_name: str = Field(..., max_length=255)
    parent_category_id: UUID | None = None
    icon: str | None = Field(None, max_length=50)
    sort_order: int = 0


class ExpenseCategoryCreate(ExpenseCategoryBase):
    """Schema for creating an ExpenseCategory."""
    pass


class ExpenseCategoryUpdate(BaseModel):
    """Schema for updating an ExpenseCategory."""
    
    category_name: str | None = Field(None, max_length=255)
    parent_category_id: UUID | None = None
    icon: str | None = Field(None, max_length=50)
    sort_order: int | None = None
    is_active: bool | None = None


class ExpenseCategoryResponse(ExpenseCategoryBase):
    """Schema for ExpenseCategory response."""
    
    id: UUID
    user_id: UUID
    is_system_category: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
