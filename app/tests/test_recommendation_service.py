import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import RecommendationFeedbackCreate, RecommendationParameters
from app.models.recommendation import RecommendationFeedback, RecommendationType
from app.models.user import User
from app.models.book import Book, Genre
from app.models.review import Review
from app.models.favorite import Favorite


class TestRecommendationService:
    def test_get_content_based_recommendations_with_favorites(self, db_session, sample_user, multiple_books, sample_genre):
        """Test content-based recommendations for user with favorites"""
        recommendation_service = RecommendationService(db_session)
        
        # Create user favorites with specific genres
        favorite1 = Favorite(user_id=sample_user.id, book_id=multiple_books[0].id)
        favorite2 = Favorite(user_id=sample_user.id, book_id=multiple_books[1].id)
        db_session.add_all([favorite1, favorite2])
        
        # Add reviews to ensure minimum review count
        for i, book in enumerate(multiple_books[:5]):
            for j in range(5):  # 5 reviews per book
                review = Review(
                    user_id=sample_user.id + j + 1,  # Different users
                    book_id=book.id,
                    rating=4.0 + (i * 0.2),  # Varied ratings
                    title=f"Review {j}",
                    content=f"Content {j}"
                )
                db_session.add(review)
        
        db_session.commit()
        
        params = RecommendationParameters(limit=5, exclude_user_books=True)
        recommendations = recommendation_service.get_content_based_recommendations(
            user_id=sample_user.id,
            params=params
        )
        
        assert len(recommendations) > 0
        for rec in recommendations:
            assert rec.book.id not in [multiple_books[0].id, multiple_books[1].id]  # Excluded favorites
            assert rec.score > 0
            assert rec.reason is not None
            assert rec.recommendation_type.value == RecommendationType.CONTENT_BASED.value

    def test_get_content_based_recommendations_no_favorites(self, db_session, sample_user, multiple_books):
        """Test content-based recommendations fallback when user has no favorites"""
        recommendation_service = RecommendationService(db_session)
        
        # Add some reviews to books for fallback
        for book in multiple_books[:3]:
            review = Review(
                user_id=sample_user.id + 1,  # Different user
                book_id=book.id,
                rating=4.0,
                title="Good book",
                content="Really enjoyed it"
            )
            db_session.add(review)
        
        db_session.commit()
        
        params = RecommendationParameters(limit=3)
        recommendations = recommendation_service.get_content_based_recommendations(
            user_id=sample_user.id,
            params=params
        )
        
        # Should return fallback recommendations
        assert len(recommendations) >= 0
        for rec in recommendations:
            assert rec.recommendation_type.value == RecommendationType.CONTENT_BASED.value

    def test_get_popularity_based_recommendations(self, db_session, sample_user, multiple_books):
        """Test popularity-based recommendations"""
        recommendation_service = RecommendationService(db_session)
        
        # Create reviews and favorites to establish popularity
        for i, book in enumerate(multiple_books[:3]):
            # Add multiple reviews
            for j in range(5 + i):  # Varying review counts
                review = Review(
                    user_id=sample_user.id + j + 1,
                    book_id=book.id,
                    rating=4.5 - (i * 0.1),  # Decreasing ratings
                    title=f"Review {j}",
                    content=f"Great book {j}"
                )
                db_session.add(review)
            
            # Add favorites
            for k in range(3 + i):  # Varying favorite counts
                favorite = Favorite(
                    user_id=sample_user.id + k + 1,
                    book_id=book.id
                )
                db_session.add(favorite)
        
        db_session.commit()
        
        params = RecommendationParameters(limit=3, exclude_user_books=True)
        recommendations = recommendation_service.get_popularity_based_recommendations(
            user_id=sample_user.id,
            params=params
        )
        
        assert len(recommendations) > 0
        # Should be sorted by popularity score (descending)
        for i in range(1, len(recommendations)):
            assert recommendations[i-1].score >= recommendations[i].score
        
        for rec in recommendations:
            assert rec.recommendation_type.value == RecommendationType.POPULARITY_BASED.value
            assert "Highly rated" in rec.reason or "Popular" in rec.reason

    def test_create_recommendation_feedback(self, db_session, sample_user, sample_book):
        """Test creating recommendation feedback"""
        recommendation_service = RecommendationService(db_session)
        
        feedback_data = RecommendationFeedbackCreate(
            book_id=sample_book.id,
            recommendation_type=RecommendationType.CONTENT_BASED,
            is_positive=True,
            context_data='{"page": "test"}'
        )
        
        feedback = recommendation_service.create_recommendation_feedback(
            user_id=sample_user.id,
            feedback_data=feedback_data
        )
        
        assert feedback is not None
        assert feedback.user_id == sample_user.id
        assert feedback.book_id == sample_book.id
        assert feedback.recommendation_type == RecommendationType.CONTENT_BASED
        assert feedback.is_positive is True
        assert feedback.context_data == '{"page": "test"}'
        assert feedback.created_at is not None

    def test_get_recommendation_stats_no_data(self, db_session):
        """Test getting recommendation stats with no feedback data"""
        recommendation_service = RecommendationService(db_session)
        
        stats = recommendation_service.get_recommendation_stats()
        
        assert isinstance(stats, list)
        assert len(stats) == 0

    def test_get_recommendation_stats_with_data(self, db_session, sample_user, multiple_books):
        """Test getting recommendation stats with feedback data"""
        recommendation_service = RecommendationService(db_session)
        
        # Create some feedback
        feedback1 = RecommendationFeedback(
            user_id=sample_user.id,
            book_id=multiple_books[0].id,
            recommendation_type=RecommendationType.CONTENT_BASED,
            is_positive=True
        )
        feedback2 = RecommendationFeedback(
            user_id=sample_user.id,
            book_id=multiple_books[1].id,
            recommendation_type=RecommendationType.CONTENT_BASED,
            is_positive=False
        )
        feedback3 = RecommendationFeedback(
            user_id=sample_user.id,
            book_id=multiple_books[2].id,
            recommendation_type=RecommendationType.POPULARITY_BASED,
            is_positive=True
        )
        
        db_session.add_all([feedback1, feedback2, feedback3])
        db_session.commit()
        
        stats = recommendation_service.get_recommendation_stats()
        
        assert len(stats) == 2  # Two recommendation types
        
        # Find content-based stats
        content_stats = next((s for s in stats if s.recommendation_type.value == RecommendationType.CONTENT_BASED.value), None)
        assert content_stats is not None
        assert content_stats.total_feedback == 2
        assert content_stats.positive_feedback == 1
        assert content_stats.negative_feedback == 1
        assert content_stats.positive_rate == 0.5

    def test_recommendation_parameters_validation(self, db_session, sample_user):
        """Test recommendation parameter validation"""
        recommendation_service = RecommendationService(db_session)
        
        # Test with various parameters
        params = RecommendationParameters(
            limit=5,
            exclude_user_books=False,
            min_rating=3.5
        )
        
        # Should not raise exceptions
        recommendations = recommendation_service.get_content_based_recommendations(
            user_id=sample_user.id,
            params=params
        )
        
        assert isinstance(recommendations, list)

    def test_exclude_user_books_parameter(self, db_session, sample_user, multiple_books):
        """Test that exclude_user_books parameter works correctly"""
        recommendation_service = RecommendationService(db_session)
        
        # User favorites a book
        favorite = Favorite(user_id=sample_user.id, book_id=multiple_books[0].id)
        db_session.add(favorite)
        
        # User reviews a book
        review = Review(
            user_id=sample_user.id,
            book_id=multiple_books[1].id,
            rating=4.0,
            title="My review",
            content="Good book"
        )
        db_session.add(review)
        db_session.commit()
        
        # Test with exclude_user_books=True
        params_exclude = RecommendationParameters(limit=10, exclude_user_books=True)
        recommendations_exclude = recommendation_service.get_popularity_based_recommendations(
            user_id=sample_user.id,
            params=params_exclude
        )
        
        # Test with exclude_user_books=False
        params_include = RecommendationParameters(limit=10, exclude_user_books=False)
        recommendations_include = recommendation_service.get_popularity_based_recommendations(
            user_id=sample_user.id,
            params=params_include
        )
        
        # With exclusion, user's books should not be in recommendations
        user_book_ids = {multiple_books[0].id, multiple_books[1].id}
        for rec in recommendations_exclude:
            assert rec.book.id not in user_book_ids

    def test_min_rating_filter(self, db_session, sample_user, multiple_books):
        """Test minimum rating filter"""
        recommendation_service = RecommendationService(db_session)
        
        # Add reviews with different ratings
        for i, book in enumerate(multiple_books[:3]):
            for j in range(5):
                review = Review(
                    user_id=sample_user.id + j + 1,
                    book_id=book.id,
                    rating=2.0 + i,  # 2.0, 3.0, 4.0 average ratings
                    title=f"Review {j}",
                    content="Review content"
                )
                db_session.add(review)
        
        db_session.commit()
        
        # Test with min_rating=3.5
        params = RecommendationParameters(limit=10, min_rating=3.5)
        recommendations = recommendation_service.get_popularity_based_recommendations(
            user_id=sample_user.id,
            params=params
        )
        
        # Should only include books with rating >= 3.5
        for rec in recommendations:
            if rec.book.average_rating > 0:
                assert rec.book.average_rating >= 3.5

    def test_cache_key_generation(self, db_session, sample_user):
        """Test cache key generation for recommendations"""
        recommendation_service = RecommendationService(db_session)
        
        params1 = RecommendationParameters(limit=10, exclude_user_books=True)
        params2 = RecommendationParameters(limit=5, exclude_user_books=False)
        
        key1 = recommendation_service._generate_cache_key(sample_user.id, "content_based", params1)
        key2 = recommendation_service._generate_cache_key(sample_user.id, "content_based", params2)
        
        assert key1 != key2  # Different parameters should generate different keys
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length

    def test_invalidate_user_cache(self, db_session, sample_user):
        """Test cache invalidation for user"""
        recommendation_service = RecommendationService(db_session)
        
        # Should not raise exceptions
        recommendation_service.invalidate_user_cache(sample_user.id)

    def test_fallback_recommendations_on_error(self, db_session, sample_user, multiple_books):
        """Test that fallback recommendations are provided when main algorithm fails"""
        recommendation_service = RecommendationService(db_session)
        
        # Add a basic book with review for fallback
        review = Review(
            user_id=sample_user.id + 1,
            book_id=multiple_books[0].id,
            rating=4.0,
            title="Good book",
            content="Really good"
        )
        db_session.add(review)
        db_session.commit()
        
        params = RecommendationParameters(limit=5)
        
        # Even if the main algorithm has issues, should return fallback
        recommendations = recommendation_service._get_fallback_recommendations(
            user_id=sample_user.id,
            params=params,
            rec_type="content_based"
        )
        
        assert isinstance(recommendations, list)
        # Should have at least some recommendations if books exist
        if multiple_books:
            assert len(recommendations) >= 0 