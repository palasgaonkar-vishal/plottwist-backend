"""
Pydantic schemas for book-related API operations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class GenreBase(BaseModel):
    """Base schema for genre information."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GenreResponse(GenreBase):
    """Schema for genre response."""
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class BookBase(BaseModel):
    """Base schema for book information."""
    title: str = Field(..., max_length=255)
    author: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    published_year: Optional[int] = Field(None, ge=1000, le=2030)
    isbn: Optional[str] = Field(None, max_length=20)
    cover_url: Optional[str] = Field(None, max_length=500)


class BookCreate(BookBase):
    """Schema for creating a new book."""
    genre_ids: List[int] = Field(default_factory=list, description="List of genre IDs to associate with the book")


class BookUpdate(BaseModel):
    """Schema for updating a book."""
    title: Optional[str] = Field(None, max_length=255)
    author: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    published_year: Optional[int] = Field(None, ge=1000, le=2030)
    isbn: Optional[str] = Field(None, max_length=20)
    cover_url: Optional[str] = Field(None, max_length=500)
    genre_ids: Optional[List[int]] = Field(None, description="List of genre IDs to associate with the book")


class BookResponse(BookBase):
    """Schema for book response with ratings and genres."""
    id: int
    average_rating: float = Field(..., ge=0.0, le=5.0)
    total_reviews: int = Field(..., ge=0)
    genres: List[GenreResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    """Schema for paginated book listing."""
    books: List[BookResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class BookSearchQuery(BaseModel):
    """Schema for book search parameters."""
    query: Optional[str] = Field(None, description="Search query for title or author")
    genre_id: Optional[int] = Field(None, description="Filter by genre ID")
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Minimum average rating")
    published_year_start: Optional[int] = Field(None, ge=1000, description="Earliest publication year")
    published_year_end: Optional[int] = Field(None, le=2030, description="Latest publication year")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")


class BookSearchResponse(BookListResponse):
    """Schema for book search results."""
    query: Optional[str] = None
    filters_applied: dict = Field(default_factory=dict) 