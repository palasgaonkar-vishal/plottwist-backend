"""
API routes for review operations.
Provides endpoints for review CRUD operations, rating statistics, and user review management.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    ReviewListResponse,
    BookRatingStats,
    UserReviewsResponse
)
from app.services.review_service import ReviewService
from app.core.dependencies import get_current_active_user, get_optional_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new review for a book."""
    try:
        review_service = ReviewService(db)
        review = review_service.create_review(review_data, current_user.id)
        
        # Fetch user and book details for response
        review_response = ReviewResponse.from_orm(review)
        review_response.user_name = current_user.name
        if review.book:
            review_response.book_title = review.book.title
            
        return review_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int = Path(..., gt=0, description="Review ID"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific review by ID."""
    try:
        review_service = ReviewService(db)
        review = review_service.get_review(review_id)
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Build response with user and book details
        review_response = ReviewResponse.from_orm(review)
        if review.user:
            review_response.user_name = review.user.name
        if review.book:
            review_response.book_title = review.book.title
            
        return review_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review {review_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_data: ReviewUpdate,
    review_id: int = Path(..., gt=0, description="Review ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing review (owner only)."""
    try:
        review_service = ReviewService(db)
        review = review_service.update_review(review_id, review_data, current_user.id)
        
        # Build response with user and book details
        review_response = ReviewResponse.from_orm(review)
        review_response.user_name = current_user.name
        if review.book:
            review_response.book_title = review.book.title
            
        return review_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating review {review_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int = Path(..., gt=0, description="Review ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a review (owner only)."""
    try:
        review_service = ReviewService(db)
        review_service.delete_review(review_id, current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting review {review_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/book/{book_id}", response_model=ReviewListResponse)
async def get_book_reviews(
    book_id: int = Path(..., gt=0, description="Book ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Reviews per page"),
    sort_by: str = Query("created_at", regex="^(created_at|rating|updated_at)$", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated reviews for a specific book."""
    try:
        review_service = ReviewService(db)
        reviews, total = review_service.get_reviews_by_book(
            book_id=book_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Build response with user and book details
        review_responses = []
        for review in reviews:
            review_response = ReviewResponse.from_orm(review)
            if review.user:
                review_response.user_name = review.user.name
            if review.book:
                review_response.book_title = review.book.title
            review_responses.append(review_response)
        
        total_pages = (total + per_page - 1) // per_page
        
        return ReviewListResponse(
            reviews=review_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reviews for book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/book/{book_id}/stats", response_model=BookRatingStats)
async def get_book_rating_stats(
    book_id: int = Path(..., gt=0, description="Book ID"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Get rating statistics for a specific book."""
    try:
        review_service = ReviewService(db)
        stats = review_service.get_book_rating_stats(book_id)
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching rating stats for book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/user/me", response_model=ReviewListResponse)
async def get_my_reviews(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Reviews per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the current user's reviews."""
    try:
        review_service = ReviewService(db)
        reviews, total, total_pages = review_service.get_reviews_by_user(
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )
        
        # Build response with book details
        review_responses = []
        for review in reviews:
            review_response = ReviewResponse.from_orm(review)
            review_response.user_name = current_user.name
            if review.book:
                review_response.book_title = review.book.title
            review_responses.append(review_response)
        
        return ReviewListResponse(
            reviews=review_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error fetching reviews for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/user/me/stats", response_model=UserReviewsResponse)
async def get_my_review_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get review statistics for the current user."""
    try:
        review_service = ReviewService(db)
        stats = review_service.get_user_review_stats(current_user.id)
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching review stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/user/me/book/{book_id}", response_model=ReviewResponse)
async def get_my_review_for_book(
    book_id: int = Path(..., gt=0, description="Book ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the current user's review for a specific book."""
    try:
        review_service = ReviewService(db)
        review = review_service.get_user_review_for_book(current_user.id, book_id)
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Build response with user and book details
        review_response = ReviewResponse.from_orm(review)
        review_response.user_name = current_user.name
        if review.book:
            review_response.book_title = review.book.title
            
        return review_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user review for book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 