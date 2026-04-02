"""Authentication-related Pydantic schemas."""

from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str | None = Field(None, max_length=255)


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)."""

    id: UUID
    email: str
    full_name: str | None
    is_active: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class SetupStatusResponse(BaseModel):
    """Response indicating whether the user needs initial setup."""

    needs_setup: bool
    missing: List[str]
    currencies_count: int



