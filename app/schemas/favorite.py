from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from .book import BookResponse


class FavoriteBase(BaseModel):
    """Base schema for favorites"""
    book_id: int

    class Config:
        from_attributes = True


class FavoriteCreate(FavoriteBase):
    """Schema for creating a favorite"""
    pass


class FavoriteResponse(BaseModel):
    """Schema for favorite response with book details"""
    id: int
    book_id: int
    user_id: int
    created_at: datetime
    book: BookResponse
    
    class Config:
        from_attributes = True


class FavoriteToggleResponse(BaseModel):
    """Schema for favorite toggle response"""
    is_favorite: bool
    message: str
    
    class Config:
        from_attributes = True


class UserFavoritesResponse(BaseModel):
    """Schema for user's favorites list with pagination"""
    favorites: List[FavoriteResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    
    class Config:
        from_attributes = True 