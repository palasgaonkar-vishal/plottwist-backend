import pytest
from math import ceil
from sqlalchemy.orm import Session

from app.services.favorite_service import FavoriteService
from app.schemas.favorite import FavoriteCreate
from app.models.favorite import Favorite
from app.models.book import Book
from app.models.user import User


class TestFavoriteService:
    def test_add_favorite_success(self, db_session, sample_user, sample_book):
        """Test successfully adding a book to favorites"""
        favorite_service = FavoriteService(db_session)
        
        favorite_data = FavoriteCreate(book_id=sample_book.id)
        favorite = favorite_service.add_favorite(sample_user.id, favorite_data)
        
        assert favorite is not None
        assert favorite.user_id == sample_user.id
        assert favorite.book_id == sample_book.id
        assert favorite.created_at is not None

    def test_add_favorite_duplicate(self, db_session, sample_user, sample_book):
        """Test adding duplicate favorite returns existing favorite"""
        favorite_service = FavoriteService(db_session)
        
        # Create first favorite
        favorite_data = FavoriteCreate(book_id=sample_book.id)
        favorite1 = favorite_service.add_favorite(sample_user.id, favorite_data)
        
        # Try to add same favorite again
        favorite2 = favorite_service.add_favorite(sample_user.id, favorite_data)
        
        assert favorite1.id == favorite2.id
        
        # Verify only one favorite exists
        favorites_count = db_session.query(Favorite).filter(
            Favorite.user_id == sample_user.id,
            Favorite.book_id == sample_book.id
        ).count()
        assert favorites_count == 1

    def test_add_favorite_book_not_found(self, db_session, sample_user):
        """Test adding favorite for non-existent book"""
        favorite_service = FavoriteService(db_session)
        
        favorite_data = FavoriteCreate(book_id=99999)
        favorite = favorite_service.add_favorite(sample_user.id, favorite_data)
        
        assert favorite is None

    def test_remove_favorite_success(self, db_session, sample_user, sample_book):
        """Test successfully removing a favorite"""
        favorite_service = FavoriteService(db_session)
        
        # First add a favorite
        favorite = Favorite(user_id=sample_user.id, book_id=sample_book.id)
        db_session.add(favorite)
        db_session.commit()
        
        # Remove it
        success = favorite_service.remove_favorite(sample_user.id, sample_book.id)
        
        assert success is True
        
        # Verify it's gone
        remaining_favorite = db_session.query(Favorite).filter(
            Favorite.user_id == sample_user.id,
            Favorite.book_id == sample_book.id
        ).first()
        assert remaining_favorite is None

    def test_remove_favorite_not_found(self, db_session, sample_user, sample_book):
        """Test removing non-existent favorite"""
        favorite_service = FavoriteService(db_session)
        
        success = favorite_service.remove_favorite(sample_user.id, sample_book.id)
        
        assert success is False

    def test_toggle_favorite_add(self, db_session, sample_user, sample_book):
        """Test toggling favorite (adding)"""
        favorite_service = FavoriteService(db_session)
        
        is_favorite, message = favorite_service.toggle_favorite(sample_user.id, sample_book.id)
        
        assert is_favorite is True
        assert message == "Added to favorites"
        
        # Verify favorite was created
        favorite = db_session.query(Favorite).filter(
            Favorite.user_id == sample_user.id,
            Favorite.book_id == sample_book.id
        ).first()
        assert favorite is not None

    def test_toggle_favorite_remove(self, db_session, sample_user, sample_book):
        """Test toggling favorite (removing)"""
        favorite_service = FavoriteService(db_session)
        
        # First add a favorite
        favorite = Favorite(user_id=sample_user.id, book_id=sample_book.id)
        db_session.add(favorite)
        db_session.commit()
        
        is_favorite, message = favorite_service.toggle_favorite(sample_user.id, sample_book.id)
        
        assert is_favorite is False
        assert message == "Removed from favorites"
        
        # Verify favorite was removed
        remaining_favorite = db_session.query(Favorite).filter(
            Favorite.user_id == sample_user.id,
            Favorite.book_id == sample_book.id
        ).first()
        assert remaining_favorite is None

    def test_toggle_favorite_book_not_found(self, db_session, sample_user):
        """Test toggling favorite for non-existent book"""
        favorite_service = FavoriteService(db_session)
        
        is_favorite, message = favorite_service.toggle_favorite(sample_user.id, 99999)
        
        assert is_favorite is False
        assert message == "Book not found"

    def test_is_favorite_true(self, db_session, sample_user, sample_book):
        """Test checking if book is favorited (true case)"""
        favorite_service = FavoriteService(db_session)
        
        # Add a favorite
        favorite = Favorite(user_id=sample_user.id, book_id=sample_book.id)
        db_session.add(favorite)
        db_session.commit()
        
        is_favorite = favorite_service.is_favorite(sample_user.id, sample_book.id)
        
        assert is_favorite is True

    def test_is_favorite_false(self, db_session, sample_user, sample_book):
        """Test checking if book is favorited (false case)"""
        favorite_service = FavoriteService(db_session)
        
        is_favorite = favorite_service.is_favorite(sample_user.id, sample_book.id)
        
        assert is_favorite is False

    def test_get_user_favorites_with_data(self, db_session, sample_user, multiple_books):
        """Test getting user's favorites with pagination"""
        favorite_service = FavoriteService(db_session)
        
        # Add multiple favorites
        for i, book in enumerate(multiple_books[:3]):
            favorite = Favorite(user_id=sample_user.id, book_id=book.id)
            db_session.add(favorite)
        db_session.commit()
        
        # Get favorites
        favorites, total, total_pages = favorite_service.get_user_favorites(
            user_id=sample_user.id,
            page=1,
            per_page=10
        )
        
        assert len(favorites) == 3
        assert total == 3
        assert total_pages == 1
        
        # Verify favorites have book details loaded
        for favorite in favorites:
            assert favorite.book is not None
            assert favorite.book.title is not None

    def test_get_user_favorites_pagination(self, db_session, sample_user, multiple_books):
        """Test favorites pagination"""
        favorite_service = FavoriteService(db_session)
        
        # Add 5 favorites
        for book in multiple_books[:5]:
            favorite = Favorite(user_id=sample_user.id, book_id=book.id)
            db_session.add(favorite)
        db_session.commit()
        
        # Get first page (2 per page)
        favorites, total, total_pages = favorite_service.get_user_favorites(
            user_id=sample_user.id,
            page=1,
            per_page=2
        )
        
        assert len(favorites) == 2
        assert total == 5
        assert total_pages == 3
        
        # Get second page
        favorites_page2, _, _ = favorite_service.get_user_favorites(
            user_id=sample_user.id,
            page=2,
            per_page=2
        )
        
        assert len(favorites_page2) == 2
        # Verify different favorites on different pages
        assert favorites[0].id != favorites_page2[0].id

    def test_get_user_favorites_empty(self, db_session, sample_user):
        """Test getting favorites for user with no favorites"""
        favorite_service = FavoriteService(db_session)
        
        favorites, total, total_pages = favorite_service.get_user_favorites(
            user_id=sample_user.id,
            page=1,
            per_page=10
        )
        
        assert len(favorites) == 0
        assert total == 0
        assert total_pages == 1

    def test_get_user_favorites_count(self, db_session, sample_user, multiple_books):
        """Test getting count of user's favorites"""
        favorite_service = FavoriteService(db_session)
        
        # Initially no favorites
        count = favorite_service.get_user_favorites_count(sample_user.id)
        assert count == 0
        
        # Add favorites
        for book in multiple_books[:3]:
            favorite = Favorite(user_id=sample_user.id, book_id=book.id)
            db_session.add(favorite)
        db_session.commit()
        
        count = favorite_service.get_user_favorites_count(sample_user.id)
        assert count == 3

    def test_get_book_favorites_count(self, db_session, multiple_users, sample_book):
        """Test getting count of users who favorited a book"""
        favorite_service = FavoriteService(db_session)
        
        # Initially no favorites
        count = favorite_service.get_book_favorites_count(sample_book.id)
        assert count == 0
        
        # Add favorites from multiple users
        for user in multiple_users[:2]:
            favorite = Favorite(user_id=user.id, book_id=sample_book.id)
            db_session.add(favorite)
        db_session.commit()
        
        count = favorite_service.get_book_favorites_count(sample_book.id)
        assert count == 2

    def test_get_popular_books(self, db_session, multiple_users, multiple_books):
        """Test getting most favorited books"""
        favorite_service = FavoriteService(db_session)
        
        # Book 1: 3 favorites
        for user in multiple_users[:3]:
            favorite = Favorite(user_id=user.id, book_id=multiple_books[0].id)
            db_session.add(favorite)
        
        # Book 2: 2 favorites
        for user in multiple_users[:2]:
            favorite = Favorite(user_id=user.id, book_id=multiple_books[1].id)
            db_session.add(favorite)
        
        # Book 3: 1 favorite
        favorite = Favorite(user_id=multiple_users[0].id, book_id=multiple_books[2].id)
        db_session.add(favorite)
        
        db_session.commit()
        
        popular_books = favorite_service.get_popular_books(limit=5)
        
        assert len(popular_books) == 3
        
        # Verify order (most popular first)
        book1, count1 = popular_books[0]
        book2, count2 = popular_books[1]
        book3, count3 = popular_books[2]
        
        assert count1 == 3
        assert count2 == 2
        assert count3 == 1
        assert book1.id == multiple_books[0].id
        assert book2.id == multiple_books[1].id
        assert book3.id == multiple_books[2].id

    def test_get_popular_books_limit(self, db_session, multiple_users, multiple_books):
        """Test popular books with limit"""
        favorite_service = FavoriteService(db_session)
        
        # Add favorites for 3 books
        for i, book in enumerate(multiple_books[:3]):
            for user in multiple_users[:i+1]:  # Different amounts of favorites
                favorite = Favorite(user_id=user.id, book_id=book.id)
                db_session.add(favorite)
        db_session.commit()
        
        popular_books = favorite_service.get_popular_books(limit=2)
        
        assert len(popular_books) == 2  # Limited to 2 results 