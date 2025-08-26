from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..core.dependencies import get_current_user
from ..models.user import User
from ..schemas.favorite import (
    FavoriteCreate, 
    FavoriteResponse, 
    FavoriteToggleResponse, 
    UserFavoritesResponse
)
from ..services.favorite_service import FavoriteService

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/", response_model=FavoriteResponse)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a book to user's favorites"""
    favorite_service = FavoriteService(db)
    
    favorite = favorite_service.add_favorite(current_user.id, favorite_data)
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return favorite


@router.delete("/{book_id}/")
async def remove_favorite(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a book from user's favorites"""
    favorite_service = FavoriteService(db)
    
    success = favorite_service.remove_favorite(current_user.id, book_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    return {"message": "Favorite removed successfully"}


@router.post("/toggle/{book_id}/", response_model=FavoriteToggleResponse)
async def toggle_favorite(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle favorite status of a book"""
    favorite_service = FavoriteService(db)
    
    is_favorite, message = favorite_service.toggle_favorite(current_user.id, book_id)
    
    return FavoriteToggleResponse(
        is_favorite=is_favorite,
        message=message
    )


@router.get("/check/{book_id}/")
async def check_favorite_status(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a book is favorited by the current user"""
    favorite_service = FavoriteService(db)
    
    is_favorite = favorite_service.is_favorite(current_user.id, book_id)
    
    return {"is_favorite": is_favorite}


@router.get("/me/", response_model=UserFavoritesResponse)
async def get_my_favorites(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's favorite books with pagination"""
    favorite_service = FavoriteService(db)
    
    favorites, total, total_pages = favorite_service.get_user_favorites(
        user_id=current_user.id,
        page=page,
        per_page=per_page
    )
    
    return UserFavoritesResponse(
        favorites=favorites,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/count/")
async def get_my_favorites_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of current user's favorites"""
    favorite_service = FavoriteService(db)
    
    count = favorite_service.get_user_favorites_count(current_user.id)
    
    return {"count": count}


@router.get("/book/{book_id}/count/")
async def get_book_favorites_count(
    book_id: int,
    db: Session = Depends(get_db)
):
    """Get count of users who favorited a specific book"""
    favorite_service = FavoriteService(db)
    
    count = favorite_service.get_book_favorites_count(book_id)
    
    return {"count": count}


@router.get("/popular/")
async def get_popular_books(
    limit: int = Query(10, ge=1, le=50, description="Number of books to return"),
    db: Session = Depends(get_db)
):
    """Get most favorited books"""
    favorite_service = FavoriteService(db)
    
    popular_books = favorite_service.get_popular_books(limit)
    
    return {
        "books": [
            {
                "book": book,
                "favorite_count": count
            }
            for book, count in popular_books
        ]
    } 