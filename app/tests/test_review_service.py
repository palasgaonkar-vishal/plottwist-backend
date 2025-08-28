"""
Tests for ReviewService functionality.
Comprehensive testing of review CRUD operations, rating calculations, and business logic.
"""

import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.review_service import ReviewService
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.models.review import Review
from app.models.book import Book
from app.models.user import User


class TestReviewService:
    """Test class for ReviewService functionality."""
    
    def test_create_review_success(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test successful review creation."""
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            book_id=sample_book.id,
            rating=4.5,
            title="Great book!",
            content="Really enjoyed this book. Highly recommended."
        )
        
        review = review_service.create_review(review_data, sample_user.id)
        
        assert review.id is not None
        assert review.book_id == sample_book.id
        assert review.user_id == sample_user.id
        assert review.rating == 4.5
        assert review.title == "Great book!"
        assert review.content == "Really enjoyed this book. Highly recommended."
        assert review.created_at is not None
        assert review.updated_at is not None
    
    def test_create_review_book_not_found(self, db_session: Session, sample_user: User):
        """Test review creation with non-existent book."""
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            book_id=99999,  # Non-existent book ID
            rating=4.5,
            title="Great book!",
            content="Really enjoyed this book."
        )
        
        with pytest.raises(HTTPException) as exc_info:
            review_service.create_review(review_data, sample_user.id)
        
        assert exc_info.value.status_code == 404
        assert "Book not found" in str(exc_info.value.detail)
    
    def test_create_review_duplicate(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test creation of duplicate review by same user for same book."""
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            book_id=sample_book.id,
            rating=4.5,
            title="Great book!",
            content="Really enjoyed this book."
        )
        
        # Create first review
        review_service.create_review(review_data, sample_user.id)
        
        # Try to create duplicate review
        with pytest.raises(HTTPException) as exc_info:
            review_service.create_review(review_data, sample_user.id)
        
        assert exc_info.value.status_code == 400
        assert "already reviewed this book" in str(exc_info.value.detail)
    
    def test_get_review_success(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test successful review retrieval."""
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            book_id=sample_book.id,
            rating=4.5,
            title="Great book!",
            content="Really enjoyed this book."
        )
        
        created_review = review_service.create_review(review_data, sample_user.id)
        retrieved_review = review_service.get_review(created_review.id)
        
        assert retrieved_review is not None
        assert retrieved_review.id == created_review.id
        assert retrieved_review.rating == 4.5
    
    def test_get_review_not_found(self, db_session: Session):
        """Test review retrieval with non-existent ID."""
        review_service = ReviewService(db_session)
        
        review = review_service.get_review(99999)
        assert review is None
    
    def test_get_reviews_by_book(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test getting reviews for a specific book."""
        review_service = ReviewService(db_session)
        
        # Create multiple reviews
        for i in range(5):
            review_data = ReviewCreate(
                book_id=sample_book.id,
                rating=float(i + 1),
                title=f"Review {i + 1}",
                content=f"Content {i + 1}"
            )
            
            # Create additional users for multiple reviews
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
                hashed_password="hashedpassword"
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            review_service.create_review(review_data, user.id)
        
        # Test pagination
        reviews, total = review_service.get_reviews_by_book(sample_book.id, page=1, per_page=3)
        
        assert len(reviews) == 3
        assert total == 5
        
        # Test sorting by rating
        reviews, _ = review_service.get_reviews_by_book(
            sample_book.id, page=1, per_page=10, sort_by="rating", sort_order="asc"
        )
        
        assert len(reviews) == 5
        assert reviews[0].rating <= reviews[1].rating
    
    def test_get_reviews_by_user(self, db_session: Session, sample_user: User):
        """Test getting reviews by a specific user."""
        review_service = ReviewService(db_session)
        
        # Create multiple books and reviews
        for i in range(3):
            book = Book(
                title=f"Book {i + 1}",
                author=f"Author {i + 1}",
                isbn=f"978000000000{i}",
                published_year=2020 + i,
                description=f"Description {i + 1}"
            )
            db_session.add(book)
            db_session.commit()
            db_session.refresh(book)
            
            review_data = ReviewCreate(
                book_id=book.id,
                rating=float(i + 2),
                title=f"Review {i + 1}",
                content=f"Content {i + 1}"
            )
            review_service.create_review(review_data, sample_user.id)
        
        reviews, total, _ = review_service.get_reviews_by_user(sample_user.id, page=1, per_page=10)
        
        assert len(reviews) == 3
        assert total == 3
    
    def test_update_review_success(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test successful review update."""
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            book_id=sample_book.id,
            rating=4.0,
            title="Good book",
            content="It was okay."
        )
        
        review = review_service.create_review(review_data, sample_user.id)
        
        update_data = ReviewUpdate(
            rating=5.0,
            title="Amazing book!",
            content="Actually, this book was incredible!"
        )
        
        updated_review = review_service.update_review(review.id, update_data, sample_user.id)
        
        assert updated_review.rating == 5.0
        assert updated_review.title == "Amazing book!"
        assert updated_review.content == "Actually, this book was incredible!"
        assert updated_review.updated_at >= updated_review.created_at
    
    def test_update_review_not_found(self, db_session: Session, sample_user: User):
        """Test updating non-existent review."""
        review_service = ReviewService(db_session)
        update_data = ReviewUpdate(rating=5.0)
        
        with pytest.raises(HTTPException) as exc_info:
            review_service.update_review(99999, update_data, sample_user.id)
        
        assert exc_info.value.status_code == 404
        assert "Review not found" in str(exc_info.value.detail)
    
    def test_update_review_unauthorized(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test updating review by non-owner."""
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            book_id=sample_book.id,
            rating=4.0,
            title="Good book",
            content="It was okay."
        )
        
        review = review_service.create_review(review_data, sample_user.id)
        
        # Create another user
        other_user = User(
            email="other@example.com",
            name="Other User",
            hashed_password="hashedpassword"
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        update_data = ReviewUpdate(rating=5.0)
        
        with pytest.raises(HTTPException) as exc_info:
            review_service.update_review(review.id, update_data, other_user.id)
        
        assert exc_info.value.status_code == 403
        assert "only update your own reviews" in str(exc_info.value.detail)
    
    def test_delete_review_success(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test successful review deletion."""
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            book_id=sample_book.id,
            rating=4.0,
            title="Good book",
            content="It was okay."
        )
        
        review = review_service.create_review(review_data, sample_user.id)
        review_id = review.id
        
        result = review_service.delete_review(review_id, sample_user.id)
        
        assert result is True
        
        # Verify review is deleted
        deleted_review = review_service.get_review(review_id)
        assert deleted_review is None
    
    def test_delete_review_not_found(self, db_session: Session, sample_user: User):
        """Test deleting non-existent review."""
        review_service = ReviewService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            review_service.delete_review(99999, sample_user.id)
        
        assert exc_info.value.status_code == 404
        assert "Review not found" in str(exc_info.value.detail)
    
    def test_delete_review_unauthorized(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test deleting review by non-owner."""
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            book_id=sample_book.id,
            rating=4.0,
            title="Good book",
            content="It was okay."
        )
        
        review = review_service.create_review(review_data, sample_user.id)
        
        # Create another user
        other_user = User(
            email="other@example.com",
            name="Other User",
            hashed_password="hashedpassword"
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        with pytest.raises(HTTPException) as exc_info:
            review_service.delete_review(review.id, other_user.id)
        
        assert exc_info.value.status_code == 403
        assert "only delete your own reviews" in str(exc_info.value.detail)
    
    def test_get_book_rating_stats(self, db_session: Session, sample_book: Book):
        """Test getting book rating statistics."""
        review_service = ReviewService(db_session)
        
        # Create users and reviews with different ratings
        ratings = [1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 5.0]
        for i, rating in enumerate(ratings):
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
                hashed_password="hashedpassword"
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            review_data = ReviewCreate(
                book_id=sample_book.id,
                rating=rating,
                title=f"Review {i + 1}",
                content=f"Content {i + 1}"
            )
            review_service.create_review(review_data, user.id)
        
        stats = review_service.get_book_rating_stats(sample_book.id)
        
        assert stats.book_id == sample_book.id
        assert stats.total_reviews == 7
        assert stats.average_rating is not None
        assert 3.0 <= stats.average_rating <= 4.0  # Should be around 3.4
        
        # Check rating distribution
        assert stats.rating_distribution["1"] == 1
        assert stats.rating_distribution["2"] == 1
        assert stats.rating_distribution["3"] == 1
        assert stats.rating_distribution["4"] == 2
        assert stats.rating_distribution["5"] == 2
    
    def test_get_user_review_stats(self, db_session: Session, sample_user: User):
        """Test getting user review statistics."""
        review_service = ReviewService(db_session)
        
        # Create books and reviews
        ratings = [3.0, 4.0, 5.0]
        for i, rating in enumerate(ratings):
            book = Book(
                title=f"Book {i + 1}",
                author=f"Author {i + 1}",
                isbn=f"978000000000{i}",
                published_year=2020 + i,
                description=f"Description {i + 1}"
            )
            db_session.add(book)
            db_session.commit()
            db_session.refresh(book)
            
            review_data = ReviewCreate(
                book_id=book.id,
                rating=rating,
                title=f"Review {i + 1}",
                content=f"Content {i + 1}"
            )
            review_service.create_review(review_data, sample_user.id)
        
        stats = review_service.get_user_review_stats(sample_user.id)
        
        assert stats.user_id == sample_user.id
        assert stats.total_reviews == 3
        assert stats.average_rating_given == 4.0  # (3+4+5)/3 = 4.0
    
    def test_get_user_review_for_book(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test getting user's review for a specific book."""
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            book_id=sample_book.id,
            rating=4.5,
            title="Great book!",
            content="Really enjoyed this book."
        )
        
        created_review = review_service.create_review(review_data, sample_user.id)
        retrieved_review = review_service.get_user_review_for_book(sample_user.id, sample_book.id)
        
        assert retrieved_review is not None
        assert retrieved_review.id == created_review.id
        assert retrieved_review.user_id == sample_user.id
        assert retrieved_review.book_id == sample_book.id
    
    def test_get_user_review_for_book_not_found(self, db_session: Session, sample_user: User, sample_book: Book):
        """Test getting non-existent user review for book."""
        review_service = ReviewService(db_session)
        
        review = review_service.get_user_review_for_book(sample_user.id, sample_book.id)
        assert review is None 