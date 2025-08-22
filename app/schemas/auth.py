from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., min_length=8, max_length=100, description="Password (min 8 characters)"
    )
    name: str = Field(
        ..., min_length=1, max_length=255, description="User's display name"
    )


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class TokenData(BaseModel):
    """Schema for token data."""

    subject: Optional[str] = None
    token_type: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str = Field(..., description="JWT refresh token")


class UserResponse(BaseModel):
    """Schema for user response (excluding sensitive data)."""

    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's display name")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_verified: bool = Field(..., description="Whether the user's email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Schema for authentication response."""

    user: UserResponse = Field(..., description="User information")
    tokens: Token = Field(..., description="Authentication tokens")
