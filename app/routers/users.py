from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..core.dependencies import get_current_user
from ..models.user import User
from ..schemas.user import UserResponse, UserUpdate, UserProfileResponse, UserProfileStats
from ..schemas.review import ReviewListResponse, ReviewResponse
from ..services.user_service import UserService
from ..services.review_service import ReviewService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's basic information"""
    return current_user


@router.get("/me/profile/", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's full profile with statistics"""
    user_service = UserService(db)
    
    # Get user profile statistics
    stats = user_service.get_user_profile_stats(current_user.id)
    
    # Create profile response
    profile_data = {
        **current_user.__dict__,
        "stats": stats
    }
    
    return profile_data


@router.put("/me/", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    user_service = UserService(db)
    
    # Check if email is being updated and if it already exists
    if user_update.email and user_update.email != current_user.email:
        existing_user = user_service.get_user_by_email(user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    updated_user = user_service.update_user(current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.get("/me/reviews/", response_model=ReviewListResponse)
async def get_current_user_reviews(
    page: int = 1,
    per_page: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's reviews with pagination"""
    if per_page > 100:
        per_page = 100
    
    review_service = ReviewService(db)
    
    try:
        reviews, total, total_pages = review_service.get_reviews_by_user(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Build response with user and book details
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
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user reviews"
        )


@router.get("/me/stats/", response_model=UserProfileStats)
async def get_current_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile statistics"""
    user_service = UserService(db)
    return user_service.get_user_profile_stats(current_user.id)


@router.get("/{user_id}/", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user by ID (public information only)"""
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/{user_id}/profile/", response_model=UserProfileResponse)
async def get_user_profile_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's public profile with statistics"""
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user profile statistics
    stats = user_service.get_user_profile_stats(user_id)
    
    # Create profile response (only public information)
    profile_data = {
        **user.__dict__,
        "stats": stats
    }
    
    return profile_data
