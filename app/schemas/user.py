from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True
    is_verified: bool = False

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Schema for updating user profile information"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip() if v else v
    
    @validator('bio')
    def validate_bio(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError('Bio cannot exceed 500 characters')
        return v
    
    @validator('location')
    def validate_location(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError('Location cannot exceed 100 characters')
        return v
    
    @validator('website')
    def validate_website(cls, v):
        if v is not None and len(v) > 200:
            raise ValueError('Website URL cannot exceed 200 characters')
        return v

    class Config:
        from_attributes = True


class UserProfileStats(BaseModel):
    """User profile statistics"""
    total_reviews: int
    average_rating_given: Optional[float]
    total_favorites: int
    books_reviewed: int
    reviews_this_month: int
    
    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    """Extended user response with profile information and statistics"""
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    stats: UserProfileStats
    
    class Config:
        from_attributes = True
