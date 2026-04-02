from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TemplateBase(BaseModel):
    template_name: str = Field(..., max_length=255)
    template_type: str = Field(..., pattern="^(EXPENSE_CATEGORIES|INCOME_SOURCES|FULL)$")
    is_default: bool = False


class TemplateCreate(TemplateBase):
    source_period_id: uuid.UUID


class TemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    is_default: Optional[bool] = None


class TemplateApply(BaseModel):
    target_period_id: uuid.UUID


class TemplateResponse(TemplateBase):
    id: uuid.UUID
    user_id: uuid.UUID
    template_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
