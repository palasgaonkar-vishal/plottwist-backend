from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(
        ..., min_length=1, max_length=255, description="User's display name"
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        ..., min_length=8, max_length=100, description="Password (min 8 characters)"
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    email: Optional[EmailStr] = Field(None, description="User's email address")
    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="User's display name"
    )
    password: Optional[str] = Field(
        None, min_length=8, max_length=100, description="New password"
    )
    is_active: Optional[bool] = Field(
        None, description="Whether the user account is active"
    )
    is_verified: Optional[bool] = Field(
        None, description="Whether the user's email is verified"
    )


class UserInDB(UserBase):
    """Schema for user data stored in database."""

    id: int = Field(..., description="User ID")
    hashed_password: str = Field(..., description="Hashed password")
    is_active: bool = Field(
        default=True, description="Whether the user account is active"
    )
    is_verified: bool = Field(
        default=False, description="Whether the user's email is verified"
    )
    refresh_token: Optional[str] = Field(None, description="Current refresh token")

    model_config = {"from_attributes": True}
