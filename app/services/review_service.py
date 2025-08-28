"""
Business logic for review operations.
Handles CRUD operations, rating calculations, and review management.
"""

import logging
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status

from app.models.review import Review
from app.models.book import Book
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewUpdate, BookRatingStats, UserReviewsResponse
from app.services.book_service import BookService

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for managing book reviews and ratings."""
    
    def __init__(self, db: Session):
        self.db = db
        self.book_service = BookService(db)
    
    def create_review(self, review_data: ReviewCreate, user_id: int) -> Review:
        """
        Create a new review for a book.
        
        Args:
            review_data: Review creation data
            user_id: ID of the user creating the review
            
        Returns:
            Created review object
            
        Raises:
            HTTPException: If book doesn't exist or user already reviewed the book
        """
        # Verify book exists
        book = self.db.query(Book).filter(Book.id == review_data.book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Check if user already reviewed this book
        existing_review = self.db.query(Review).filter(
            and_(Review.user_id == user_id, Review.book_id == review_data.book_id)
        ).first()
        
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reviewed this book. Use update instead."
            )
        
        try:
            # Create new review
            review = Review(
                user_id=user_id,
                book_id=review_data.book_id,
                rating=review_data.rating,
                title=review_data.title,
                content=review_data.content
            )
            
            self.db.add(review)
            self.db.commit()
            self.db.refresh(review)
            
            # Update book rating statistics
            self.book_service.update_book_statistics(review_data.book_id)
            
            logger.info(f"Created review {review.id} for book {review_data.book_id} by user {user_id}")
            return review
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating review: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create review"
            )
    
    def get_review(self, review_id: int) -> Optional[Review]:
        """
        Get a review by ID.
        
        Args:
            review_id: Review ID
            
        Returns:
            Review object or None if not found
        """
        return self.db.query(Review).filter(Review.id == review_id).first()
    
    def get_reviews_by_book(
        self, 
        book_id: int, 
        page: int = 1, 
        per_page: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Review], int]:
        """
        Get paginated reviews for a specific book.
        
        Args:
            book_id: Book ID
            page: Page number (1-based)
            per_page: Number of reviews per page
            sort_by: Field to sort by (created_at, rating, updated_at)
            sort_order: Sort order (asc, desc)
            
        Returns:
            Tuple of (reviews list, total count)
        """
        query = self.db.query(Review).filter(Review.book_id == book_id)
        
        # Apply sorting
        if sort_by == "rating":
            sort_field = Review.rating
        elif sort_by == "updated_at":
            sort_field = Review.updated_at
        else:
            sort_field = Review.created_at
        
        if sort_order.lower() == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        reviews = query.offset(offset).limit(per_page).all()
        
        return reviews, total
    
    def get_reviews_by_user(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Review], int, int]:
        """
        Get paginated reviews by a specific user.
        
        Args:
            user_id: User ID
            page: Page number (1-based)
            per_page: Number of reviews per page
            sort_by: Field to sort by (created_at, rating, updated_at)
            sort_order: Sort order (asc, desc)
            
        Returns:
            Tuple of (reviews list, total count, total pages)
        """
        query = self.db.query(Review).filter(Review.user_id == user_id)
        
        # Apply sorting
        if sort_by == "rating":
            sort_field = Review.rating
        elif sort_by == "updated_at":
            sort_field = Review.updated_at
        else:
            sort_field = Review.created_at
        
        if sort_order.lower() == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
        
        # Get total count
        total = query.count()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        # Apply pagination
        offset = (page - 1) * per_page
        reviews = query.offset(offset).limit(per_page).all()
        
        return reviews, total, total_pages
    
    def update_review(self, review_id: int, review_data: ReviewUpdate, user_id: int) -> Review:
        """
        Update an existing review.
        
        Args:
            review_id: Review ID to update
            review_data: Updated review data
            user_id: ID of the user updating the review
            
        Returns:
            Updated review object
            
        Raises:
            HTTPException: If review not found or user not authorized
        """
        review = self.get_review(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Check ownership
        if review.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own reviews"
            )
        
        try:
            # Update fields if provided
            update_data = review_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(review, field, value)
            
            self.db.commit()
            self.db.refresh(review)
            
            # Update book rating statistics if rating changed
            if 'rating' in update_data:
                self.book_service.update_book_statistics(review.book_id)
            
            logger.info(f"Updated review {review_id} by user {user_id}")
            return review
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating review: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update review"
            )
    
    def delete_review(self, review_id: int, user_id: int) -> bool:
        """
        Delete a review.
        
        Args:
            review_id: Review ID to delete
            user_id: ID of the user deleting the review
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: If review not found or user not authorized
        """
        review = self.get_review(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Check ownership
        if review.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own reviews"
            )
        
        try:
            book_id = review.book_id
            self.db.delete(review)
            self.db.commit()
            
            # Update book rating statistics
            self.book_service.update_book_statistics(book_id)
            
            logger.info(f"Deleted review {review_id} by user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting review: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete review"
            )
    
    def get_book_rating_stats(self, book_id: int) -> BookRatingStats:
        """
        Get comprehensive rating statistics for a book.
        
        Args:
            book_id: Book ID
            
        Returns:
            Book rating statistics
        """
        # Get basic stats
        stats_query = self.db.query(
            func.count(Review.id).label("total_reviews"),
            func.avg(Review.rating).label("average_rating")
        ).filter(Review.book_id == book_id).first()
        
        total_reviews = stats_query.total_reviews or 0
        average_rating = round(stats_query.average_rating, 1) if stats_query.average_rating else None
        
        # Get rating distribution
        distribution_query = self.db.query(
            func.floor(Review.rating).label("rating"),
            func.count(Review.id).label("count")
        ).filter(Review.book_id == book_id).group_by(func.floor(Review.rating)).all()
        
        rating_distribution = {str(i): 0 for i in range(1, 6)}
        for row in distribution_query:
            rating_key = str(int(row.rating))
            if rating_key in rating_distribution:
                rating_distribution[rating_key] = row.count
        
        return BookRatingStats(
            book_id=book_id,
            average_rating=average_rating,
            total_reviews=total_reviews,
            rating_distribution=rating_distribution
        )
    
    def get_user_review_stats(self, user_id: int) -> UserReviewsResponse:
        """
        Get review statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            User review statistics
        """
        # Get user's reviews
        reviews, total_reviews, _ = self.get_reviews_by_user(user_id, page=1, per_page=1000)
        
        # Calculate average rating given by user
        if total_reviews > 0:
            avg_rating = self.db.query(func.avg(Review.rating)).filter(
                Review.user_id == user_id
            ).scalar()
            average_rating_given = round(avg_rating, 1) if avg_rating else None
        else:
            average_rating_given = None
        
        return UserReviewsResponse(
            user_id=user_id,
            reviews=[],  # Return empty list, can be populated separately if needed
            total_reviews=total_reviews,
            average_rating_given=average_rating_given
        )
    
    def get_user_review_for_book(self, user_id: int, book_id: int) -> Optional[Review]:
        """
        Get a user's review for a specific book.
        
        Args:
            user_id: User ID
            book_id: Book ID
            
        Returns:
            Review object or None if not found
        """
        return self.db.query(Review).filter(
            and_(Review.user_id == user_id, Review.book_id == book_id)
        ).first() 