"""
Pydantic schemas for review operations.
Defines request/response models for review CRUD operations with validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class ReviewBase(BaseModel):
    """Base review schema with common fields."""
    
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating on a scale of 1-5")
    title: Optional[str] = Field(None, max_length=255, description="Optional review title")
    content: Optional[str] = Field(None, description="Review text content")

    @validator('rating')
    def validate_rating(cls, v):
        """Ensure rating is within valid range."""
        if not 1.0 <= v <= 5.0:
            raise ValueError('Rating must be between 1.0 and 5.0')
        return round(v, 1)  # Round to 1 decimal place

    @validator('title')
    def validate_title(cls, v):
        """Validate review title."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            if len(v) > 255:
                raise ValueError('Title cannot exceed 255 characters')
        return v

    @validator('content')
    def validate_content(cls, v):
        """Validate review content."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""
    
    book_id: int = Field(..., gt=0, description="ID of the book being reviewed")

    class Config:
        schema_extra = {
            "example": {
                "book_id": 1,
                "rating": 4.5,
                "title": "Great read!",
                "content": "This book was absolutely fantastic. The characters were well-developed and the plot kept me engaged throughout."
            }
        }


class ReviewUpdate(ReviewBase):
    """Schema for updating an existing review."""
    
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Updated rating")
    title: Optional[str] = Field(None, max_length=255, description="Updated review title")
    content: Optional[str] = Field(None, description="Updated review content")

    class Config:
        schema_extra = {
            "example": {
                "rating": 5.0,
                "title": "Even better on second read!",
                "content": "After reading this again, I appreciate the subtle details even more."
            }
        }


class ReviewResponse(ReviewBase):
    """Schema for review response with additional metadata."""
    
    id: int = Field(..., description="Review ID")
    book_id: int = Field(..., description="ID of the reviewed book")
    user_id: int = Field(..., description="ID of the review author")
    created_at: datetime = Field(..., description="Review creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Optional user and book details
    user_name: Optional[str] = Field(None, description="Name of the review author")
    book_title: Optional[str] = Field(None, description="Title of the reviewed book")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "book_id": 1,
                "user_id": 1,
                "rating": 4.5,
                "title": "Great read!",
                "content": "This book was absolutely fantastic...",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "user_name": "John Doe",
                "book_title": "The Great Gatsby"
            }
        }


class ReviewListResponse(BaseModel):
    """Schema for paginated review list response."""
    
    reviews: List[ReviewResponse] = Field(..., description="List of reviews")
    total: int = Field(..., ge=0, description="Total number of reviews")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Number of reviews per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    class Config:
        schema_extra = {
            "example": {
                "reviews": [
                    {
                        "id": 1,
                        "book_id": 1,
                        "user_id": 1,
                        "rating": 4.5,
                        "title": "Great read!",
                        "content": "This book was fantastic...",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "user_name": "John Doe",
                        "book_title": "The Great Gatsby"
                    }
                ],
                "total": 50,
                "page": 1,
                "per_page": 10,
                "total_pages": 5
            }
        }


class BookRatingStats(BaseModel):
    """Schema for book rating statistics."""
    
    book_id: int = Field(..., description="Book ID")
    average_rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Average rating")
    total_reviews: int = Field(..., ge=0, description="Total number of reviews")
    rating_distribution: dict = Field(..., description="Rating distribution (1-5 stars)")

    class Config:
        schema_extra = {
            "example": {
                "book_id": 1,
                "average_rating": 4.2,
                "total_reviews": 25,
                "rating_distribution": {
                    "1": 1,
                    "2": 2,
                    "3": 5,
                    "4": 10,
                    "5": 7
                }
            }
        }


class UserReviewsResponse(BaseModel):
    """Schema for user's review history."""
    
    user_id: int = Field(..., description="User ID")
    reviews: List[ReviewResponse] = Field(..., description="User's reviews")
    total_reviews: int = Field(..., ge=0, description="Total reviews by user")
    average_rating_given: Optional[float] = Field(None, description="Average rating given by user")

    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "reviews": [],
                "total_reviews": 15,
                "average_rating_given": 4.1
            }
        } 