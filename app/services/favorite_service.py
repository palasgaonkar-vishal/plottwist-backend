from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from typing import Optional, List, Tuple
from math import ceil

from ..models.favorite import Favorite
from ..models.book import Book
from ..models.user import User
from ..schemas.favorite import FavoriteCreate


class FavoriteService:
    def __init__(self, db: Session):
        self.db = db

    def add_favorite(self, user_id: int, favorite_data: FavoriteCreate) -> Optional[Favorite]:
        """Add a book to user's favorites"""
        # Check if already favorited
        existing = self.db.query(Favorite).filter(
            and_(
                Favorite.user_id == user_id,
                Favorite.book_id == favorite_data.book_id
            )
        ).first()
        
        if existing:
            return existing  # Already favorited
        
        # Verify book exists
        book = self.db.query(Book).filter(Book.id == favorite_data.book_id).first()
        if not book:
            return None
        
        # Create new favorite
        favorite = Favorite(
            user_id=user_id,
            book_id=favorite_data.book_id
        )
        
        self.db.add(favorite)
        self.db.commit()
        self.db.refresh(favorite)
        return favorite

    def remove_favorite(self, user_id: int, book_id: int) -> bool:
        """Remove a book from user's favorites"""
        favorite = self.db.query(Favorite).filter(
            and_(
                Favorite.user_id == user_id,
                Favorite.book_id == book_id
            )
        ).first()
        
        if not favorite:
            return False
        
        self.db.delete(favorite)
        self.db.commit()
        return True

    def toggle_favorite(self, user_id: int, book_id: int) -> Tuple[bool, str]:
        """Toggle favorite status of a book for a user"""
        favorite = self.db.query(Favorite).filter(
            and_(
                Favorite.user_id == user_id,
                Favorite.book_id == book_id
            )
        ).first()
        
        if favorite:
            # Remove from favorites
            self.db.delete(favorite)
            self.db.commit()
            return False, "Removed from favorites"
        else:
            # Add to favorites
            # Verify book exists first
            book = self.db.query(Book).filter(Book.id == book_id).first()
            if not book:
                return False, "Book not found"
            
            favorite = Favorite(user_id=user_id, book_id=book_id)
            self.db.add(favorite)
            self.db.commit()
            return True, "Added to favorites"

    def is_favorite(self, user_id: int, book_id: int) -> bool:
        """Check if a book is favorited by a user"""
        favorite = self.db.query(Favorite).filter(
            and_(
                Favorite.user_id == user_id,
                Favorite.book_id == book_id
            )
        ).first()
        
        return favorite is not None

    def get_user_favorites(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 10
    ) -> Tuple[List[Favorite], int, int]:
        """Get paginated list of user's favorite books"""
        # Get total count
        total = self.db.query(func.count(Favorite.id)).filter(
            Favorite.user_id == user_id
        ).scalar() or 0
        
        # Calculate pagination
        total_pages = ceil(total / per_page) if total > 0 else 1
        offset = (page - 1) * per_page
        
        # Get favorites with book details
        favorites = (
            self.db.query(Favorite)
            .options(joinedload(Favorite.book).joinedload(Book.genres))
            .filter(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )
        
        return favorites, total, total_pages

    def get_favorite_by_id(self, favorite_id: int, user_id: int) -> Optional[Favorite]:
        """Get a specific favorite by ID (user must own it)"""
        return (
            self.db.query(Favorite)
            .options(joinedload(Favorite.book).joinedload(Book.genres))
            .filter(
                and_(
                    Favorite.id == favorite_id,
                    Favorite.user_id == user_id
                )
            )
            .first()
        )

    def get_user_favorites_count(self, user_id: int) -> int:
        """Get total count of user's favorites"""
        return self.db.query(func.count(Favorite.id)).filter(
            Favorite.user_id == user_id
        ).scalar() or 0

    def get_book_favorites_count(self, book_id: int) -> int:
        """Get total count of users who favorited a book"""
        return self.db.query(func.count(Favorite.id)).filter(
            Favorite.book_id == book_id
        ).scalar() or 0

    def get_popular_books(self, limit: int = 10) -> List[Tuple[Book, int]]:
        """Get most favorited books with their favorite counts"""
        results = (
            self.db.query(Book, func.count(Favorite.id).label('favorite_count'))
            .join(Favorite, Book.id == Favorite.book_id)
            .group_by(Book.id)
            .order_by(func.count(Favorite.id).desc())
            .limit(limit)
            .all()
        )
        
        return [(book, count) for book, count in results] 