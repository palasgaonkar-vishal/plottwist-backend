from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..core.dependencies import get_current_user
from ..models.user import User
from ..models.recommendation import RecommendationType
from ..schemas.recommendation import (
    RecommendationFeedbackCreate,
    RecommendationFeedbackResponse,
    RecommendationResponse,
    RecommendationListResponse,
    RecommendationParameters,
    RecommendationStats,
    RecommendationItem
)
from ..services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/content-based/", response_model=RecommendationResponse)
async def get_content_based_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    exclude_user_books: bool = Query(True, description="Exclude books user has already interacted with"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum average rating filter"),
    genres: Optional[List[int]] = Query(None, description="Filter by specific genre IDs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content-based recommendations for the current user"""
    recommendation_service = RecommendationService(db)
    
    params = RecommendationParameters(
        limit=limit,
        exclude_user_books=exclude_user_books,
        min_rating=min_rating,
        genres=genres
    )
    
    try:
        recommendations = recommendation_service.get_content_based_recommendations(
            user_id=current_user.id,
            params=params
        )
        
        return RecommendationResponse(
            user_id=current_user.id,
            recommendations=recommendations,
            recommendation_type=RecommendationType.CONTENT_BASED,
            total_count=len(recommendations),
            generated_at=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content-based recommendations: {str(e)}"
        )


@router.get("/popularity-based/", response_model=RecommendationResponse)
async def get_popularity_based_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    exclude_user_books: bool = Query(True, description="Exclude books user has already interacted with"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum average rating filter"),
    genres: Optional[List[int]] = Query(None, description="Filter by specific genre IDs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get popularity-based recommendations for the current user"""
    recommendation_service = RecommendationService(db)
    
    params = RecommendationParameters(
        limit=limit,
        exclude_user_books=exclude_user_books,
        min_rating=min_rating,
        genres=genres
    )
    
    try:
        recommendations = recommendation_service.get_popularity_based_recommendations(
            user_id=current_user.id,
            params=params
        )
        
        return RecommendationResponse(
            user_id=current_user.id,
            recommendations=recommendations,
            recommendation_type=RecommendationType.POPULARITY_BASED,
            total_count=len(recommendations),
            generated_at=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate popularity-based recommendations: {str(e)}"
        )


@router.get("/all/", response_model=RecommendationListResponse)
async def get_all_recommendations(
    limit: int = Query(10, ge=1, le=25, description="Number of recommendations per type"),
    exclude_user_books: bool = Query(True, description="Exclude books user has already interacted with"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum average rating filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get both content-based and popularity-based recommendations"""
    recommendation_service = RecommendationService(db)
    
    params = RecommendationParameters(
        limit=limit,
        exclude_user_books=exclude_user_books,
        min_rating=min_rating
    )
    
    try:
        # Generate both types of recommendations in parallel
        content_based = recommendation_service.get_content_based_recommendations(
            user_id=current_user.id,
            params=params
        )
        
        popularity_based = recommendation_service.get_popularity_based_recommendations(
            user_id=current_user.id,
            params=params
        )
        
        return RecommendationListResponse(
            user_id=current_user.id,
            content_based=content_based,
            popularity_based=popularity_based,
            generated_at=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.post("/feedback/", response_model=RecommendationFeedbackResponse)
async def create_recommendation_feedback(
    feedback_data: RecommendationFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback on a recommendation for analytics"""
    recommendation_service = RecommendationService(db)
    
    try:
        feedback = recommendation_service.create_recommendation_feedback(
            user_id=current_user.id,
            feedback_data=feedback_data
        )
        
        return feedback
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save recommendation feedback: {str(e)}"
        )


@router.get("/stats/", response_model=List[RecommendationStats])
async def get_recommendation_stats(
    recommendation_type: Optional[RecommendationType] = Query(None, description="Filter by recommendation type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recommendation system statistics (for analytics)"""
    # Note: In a real system, this might be restricted to admin users
    recommendation_service = RecommendationService(db)
    
    try:
        stats = recommendation_service.get_recommendation_stats(recommendation_type)
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation statistics: {str(e)}"
        )


@router.post("/invalidate-cache/")
async def invalidate_user_recommendations_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invalidate cached recommendations for current user"""
    recommendation_service = RecommendationService(db)
    
    try:
        recommendation_service.invalidate_user_cache(current_user.id)
        return {"message": "Cache invalidated successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}"
        ) 