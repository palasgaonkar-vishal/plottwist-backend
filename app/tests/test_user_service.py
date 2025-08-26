import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserProfileStats
from app.models.user import User
from app.models.review import Review
from app.models.favorite import Favorite


class TestUserService:
    def test_get_user_profile_stats(self, db_session, sample_user, sample_book):
        """Test getting comprehensive user profile statistics"""
        user_service = UserService(db_session)
        
        # Create test reviews for this month and previous month
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month = current_month - timedelta(days=31)
        
        # Create reviews for different months
        review1 = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.5,
            title="Great book",
            content="Really enjoyed it",
            created_at=current_month + timedelta(days=5)
        )
        review2 = Review(
            user_id=sample_user.id, 
            book_id=sample_book.id + 1,  # Different book
            rating=3.5,
            title="Good read",
            content="Pretty good",
            created_at=previous_month
        )
        
        # Create favorites
        favorite1 = Favorite(user_id=sample_user.id, book_id=sample_book.id)
        favorite2 = Favorite(user_id=sample_user.id, book_id=sample_book.id + 1)
        
        db_session.add_all([review1, review2, favorite1, favorite2])
        db_session.commit()
        
        # Get stats
        stats = user_service.get_user_profile_stats(sample_user.id)
        
        assert isinstance(stats, UserProfileStats)
        assert stats.total_reviews == 2
        assert stats.average_rating_given == 4.0  # (4.5 + 3.5) / 2
        assert stats.total_favorites == 2
        assert stats.books_reviewed == 2  # Two different books
        assert stats.reviews_this_month == 1  # Only one review this month

    def test_get_user_profile_stats_no_data(self, db_session, sample_user):
        """Test getting profile stats for user with no reviews or favorites"""
        user_service = UserService(db_session)
        
        stats = user_service.get_user_profile_stats(sample_user.id)
        
        assert stats.total_reviews == 0
        assert stats.average_rating_given is None
        assert stats.total_favorites == 0
        assert stats.books_reviewed == 0
        assert stats.reviews_this_month == 0

    def test_update_user_profile(self, db_session, sample_user):
        """Test updating user profile information"""
        user_service = UserService(db_session)
        
        update_data = UserUpdate(
            name="Updated Name",
            bio="Updated bio",
            location="New City",
            website="https://example.com"
        )
        
        updated_user = user_service.update_user(sample_user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.name == "Updated Name"
        assert updated_user.bio == "Updated bio"
        assert updated_user.location == "New City"
        assert updated_user.website == "https://example.com"
        assert updated_user.email == sample_user.email  # Email unchanged

    def test_update_user_partial(self, db_session, sample_user):
        """Test partial user profile update"""
        user_service = UserService(db_session)
        
        update_data = UserUpdate(bio="New bio only")
        
        updated_user = user_service.update_user(sample_user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.bio == "New bio only"
        assert updated_user.name == sample_user.name  # Unchanged
        assert updated_user.email == sample_user.email  # Unchanged

    def test_update_user_not_found(self, db_session):
        """Test updating non-existent user"""
        user_service = UserService(db_session)
        
        update_data = UserUpdate(name="Test")
        updated_user = user_service.update_user(99999, update_data)
        
        assert updated_user is None

    def test_authenticate_user_success(self, db_session, sample_user):
        """Test successful user authentication"""
        user_service = UserService(db_session)
        
        # The sample_user fixture should have password "testpassword"
        authenticated_user = user_service.authenticate_user(sample_user.email, "testpassword")
        
        assert authenticated_user is not None
        assert authenticated_user.id == sample_user.id
        assert authenticated_user.email == sample_user.email

    def test_authenticate_user_wrong_password(self, db_session, sample_user):
        """Test authentication with wrong password"""
        user_service = UserService(db_session)
        
        authenticated_user = user_service.authenticate_user(sample_user.email, "wrongpassword")
        
        assert authenticated_user is None

    def test_authenticate_user_not_found(self, db_session):
        """Test authentication with non-existent email"""
        user_service = UserService(db_session)
        
        authenticated_user = user_service.authenticate_user("nonexistent@example.com", "password")
        
        assert authenticated_user is None

    def test_verify_user(self, db_session, sample_user):
        """Test user email verification"""
        user_service = UserService(db_session)
        
        # User should start unverified
        assert not sample_user.is_verified
        
        success = user_service.verify_user(sample_user.id)
        
        assert success is True
        db_session.refresh(sample_user)
        assert sample_user.is_verified is True

    def test_verify_user_not_found(self, db_session):
        """Test verifying non-existent user"""
        user_service = UserService(db_session)
        
        success = user_service.verify_user(99999)
        
        assert success is False

    def test_deactivate_user(self, db_session, sample_user):
        """Test user deactivation"""
        user_service = UserService(db_session)
        
        # User should start active
        assert sample_user.is_active is True
        
        success = user_service.deactivate_user(sample_user.id)
        
        assert success is True
        db_session.refresh(sample_user)
        assert sample_user.is_active is False

    def test_reactivate_user(self, db_session, sample_user):
        """Test user reactivation"""
        user_service = UserService(db_session)
        
        # First deactivate
        sample_user.is_active = False
        db_session.commit()
        
        success = user_service.reactivate_user(sample_user.id)
        
        assert success is True
        db_session.refresh(sample_user)
        assert sample_user.is_active is True

    def test_update_password(self, db_session, sample_user):
        """Test password update"""
        user_service = UserService(db_session)
        
        old_password_hash = sample_user.hashed_password
        
        success = user_service.update_password(sample_user.id, "newpassword123")
        
        assert success is True
        db_session.refresh(sample_user)
        assert sample_user.hashed_password != old_password_hash
        
        # Verify new password works
        authenticated_user = user_service.authenticate_user(sample_user.email, "newpassword123")
        assert authenticated_user is not None 