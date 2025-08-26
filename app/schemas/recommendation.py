from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .book import BookResponse


class RecommendationType(str, Enum):
    """Recommendation type enumeration"""
    CONTENT_BASED = "content_based"
    POPULARITY_BASED = "popularity_based"


class RecommendationFeedbackCreate(BaseModel):
    """Schema for creating recommendation feedback"""
    book_id: int
    recommendation_type: RecommendationType
    is_positive: bool
    context_data: Optional[str] = None
    
    @validator('context_data')
    def validate_context_data(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError('Context data cannot exceed 500 characters')
        return v

    class Config:
        from_attributes = True


class RecommendationFeedbackResponse(BaseModel):
    """Schema for recommendation feedback response"""
    id: int
    user_id: int
    book_id: int
    recommendation_type: RecommendationType
    is_positive: bool
    context_data: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class RecommendationItem(BaseModel):
    """Schema for individual recommendation item"""
    book: BookResponse
    score: float
    reason: str
    recommendation_type: RecommendationType
    
    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Schema for recommendation response"""
    user_id: int
    recommendations: List[RecommendationItem]
    recommendation_type: RecommendationType
    total_count: int
    generated_at: datetime
    cache_expiry: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RecommendationListResponse(BaseModel):
    """Schema for multiple recommendation types response"""
    user_id: int
    content_based: List[RecommendationItem]
    popularity_based: List[RecommendationItem]
    generated_at: datetime
    
    class Config:
        from_attributes = True


class RecommendationParameters(BaseModel):
    """Schema for recommendation generation parameters"""
    limit: Optional[int] = 10
    exclude_user_books: Optional[bool] = True
    min_rating: Optional[float] = None
    genres: Optional[List[int]] = None
    
    @validator('limit')
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 50):
            raise ValueError('Limit must be between 1 and 50')
        return v
    
    @validator('min_rating')
    def validate_min_rating(cls, v):
        if v is not None and (v < 0.0 or v > 5.0):
            raise ValueError('Min rating must be between 0.0 and 5.0')
        return v

    class Config:
        from_attributes = True


class RecommendationStats(BaseModel):
    """Schema for recommendation analytics and statistics"""
    recommendation_type: RecommendationType
    total_generated: int
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    feedback_rate: float
    positive_rate: float
    avg_score: Optional[float]
    
    class Config:
        from_attributes = True 