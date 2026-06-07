from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserSignupRequest(BaseModel):
    name: str = Field(..., description="User's full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=1, description="Account password")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (bearer)")


class UserResponse(BaseModel):
    id: UUID = Field(..., description="User's unique identifier")
    name: str = Field(..., description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    role: str = Field(..., description="User role (developer, admin, merchant)")
    is_active: bool = Field(..., description="Whether account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True
