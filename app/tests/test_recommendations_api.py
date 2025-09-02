import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.models.user import User
from app.models.book import Book
from app.models.review import Review
from app.models.favorite import Favorite
from app.models.recommendation import RecommendationFeedback, RecommendationType
from app.database import get_db


class TestRecommendationsAPI:
    def test_get_content_based_recommendations(self, client: TestClient, auth_headers, sample_user, multiple_books, db_session):
        """Test getting content-based recommendations"""
        # Add some data for recommendations
        favorite = Favorite(user_id=sample_user.id, book_id=multiple_books[0].id)
        db_session.add(favorite)
        db_session.commit()
        
        response = client.get("/api/v1/recommendations/content-based/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "recommendations" in data
        assert "recommendation_type" in data
        assert "total_count" in data
        assert "generated_at" in data
        assert data["recommendation_type"] == "content_based"

    def test_get_content_based_recommendations_with_params(self, client: TestClient, auth_headers):
        """Test content-based recommendations with query parameters"""
        params = {
            "limit": 5,
            "exclude_user_books": True,
            "min_rating": 4.0
        }
        
        response = client.get("/api/v1/recommendations/content-based/", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) <= 5

    def test_get_content_based_recommendations_unauthorized(self, client: TestClient):
        """Test content-based recommendations without authentication"""
        response = client.get("/api/v1/recommendations/content-based/")
        
        assert response.status_code == 403

    def test_get_popularity_based_recommendations(self, client: TestClient, auth_headers, multiple_books, multiple_users, db_session):
        """Test getting popularity-based recommendations"""
        # Add reviews to establish popularity
        for i, book in enumerate(multiple_books[:2]):
            for user in multiple_users[:3]:
                review = Review(
                    user_id=user.id,
                    book_id=book.id,
                    rating=4.0 + i * 0.5,
                    title=f"Review by user {user.id}",
                    content="Great book"
                )
                db_session.add(review)
        db_session.commit()
        
        response = client.get("/api/v1/recommendations/popularity-based/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "recommendations" in data
        assert data["recommendation_type"] == "popularity_based"

    def test_get_popularity_based_recommendations_with_genre_filter(self, client: TestClient, auth_headers):
        """Test popularity-based recommendations with genre filter"""
        params = {
            "limit": 10,
            "genres": [1, 2, 3]
        }
        
        response = client.get("/api/v1/recommendations/popularity-based/", params=params, headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_all_recommendations(self, client: TestClient, auth_headers):
        """Test getting both content-based and popularity-based recommendations"""
        response = client.get("/api/v1/recommendations/all/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "content_based" in data
        assert "popularity_based" in data
        assert "generated_at" in data
        assert isinstance(data["content_based"], list)
        assert isinstance(data["popularity_based"], list)

    def test_get_all_recommendations_with_params(self, client: TestClient, auth_headers):
        """Test getting all recommendations with parameters"""
        params = {
            "limit": 8,
            "exclude_user_books": False,
            "min_rating": 3.5
        }
        
        response = client.get("/api/v1/recommendations/all/", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["content_based"]) <= 8
        assert len(data["popularity_based"]) <= 8

    def test_create_recommendation_feedback(self, client: TestClient, auth_headers, sample_book):
        """Test creating recommendation feedback"""
        feedback_data = {
            "book_id": sample_book.id,
            "recommendation_type": "content_based",
            "is_positive": True,
            "context_data": '{"page": "recommendations"}'
        }
        
        response = client.post("/api/v1/recommendations/feedback/", json=feedback_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == sample_book.id
        assert data["recommendation_type"] == "content_based"
        assert data["is_positive"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_recommendation_feedback_negative(self, client: TestClient, auth_headers, sample_book):
        """Test creating negative recommendation feedback"""
        feedback_data = {
            "book_id": sample_book.id,
            "recommendation_type": "popularity_based",
            "is_positive": False
        }
        
        response = client.post("/api/v1/recommendations/feedback/", json=feedback_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_positive"] is False

    def test_create_recommendation_feedback_unauthorized(self, client: TestClient, sample_book):
        """Test creating recommendation feedback without authentication"""
        feedback_data = {
            "book_id": sample_book.id,
            "recommendation_type": "content_based",
            "is_positive": True
        }
        
        response = client.post("/api/v1/recommendations/feedback/", json=feedback_data)
        
        assert response.status_code == 403

    def test_create_recommendation_feedback_invalid_data(self, client: TestClient, auth_headers):
        """Test creating recommendation feedback with invalid data"""
        feedback_data = {
            "book_id": 99999,  # Non-existent book
            "recommendation_type": "invalid_type",
            "is_positive": "not_boolean"
        }
        
        response = client.post("/api/v1/recommendations/feedback/", json=feedback_data, headers=auth_headers)
        
        assert response.status_code == 422

    def test_get_recommendation_stats(self, client: TestClient, auth_headers, sample_user, multiple_books, db_session):
        """Test getting recommendation statistics"""
        # Create some feedback data
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
        db_session.add_all([feedback1, feedback2])
        db_session.commit()
        
        response = client.get("/api/v1/recommendations/stats/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check if we have content-based stats
        content_stats = next((s for s in data if s["recommendation_type"] == "content_based"), None)
        if content_stats:
            assert "total_feedback" in content_stats
            assert "positive_feedback" in content_stats
            assert "negative_feedback" in content_stats
            assert "feedback_rate" in content_stats
            assert "positive_rate" in content_stats

    def test_get_recommendation_stats_filtered(self, client: TestClient, auth_headers):
        """Test getting recommendation statistics filtered by type"""
        params = {
            "recommendation_type": "popularity_based"
        }
        
        response = client.get("/api/v1/recommendations/stats/", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_invalidate_cache(self, client: TestClient, auth_headers):
        """Test invalidating user recommendations cache"""
        response = client.post("/api/v1/recommendations/invalidate-cache/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_invalidate_cache_unauthorized(self, client: TestClient):
        """Test invalidating cache without authentication"""
        response = client.post("/api/v1/recommendations/invalidate-cache/")
        
        assert response.status_code == 403

    def test_recommendation_parameters_validation(self, client: TestClient, auth_headers):
        """Test recommendation parameter validation"""
        # Test invalid limit
        params = {"limit": 100}  # Over maximum
        response = client.get("/api/v1/recommendations/content-based/", params=params, headers=auth_headers)
        assert response.status_code == 422
        
        # Test invalid rating
        params = {"min_rating": 6.0}  # Over maximum
        response = client.get("/api/v1/recommendations/content-based/", params=params, headers=auth_headers)
        assert response.status_code == 422
        
        # Test negative limit
        params = {"limit": -1}
        response = client.get("/api/v1/recommendations/content-based/", params=params, headers=auth_headers)
        assert response.status_code == 422

    def test_recommendation_response_structure(self, client: TestClient, auth_headers):
        """Test that recommendation responses have correct structure"""
        response = client.get("/api/v1/recommendations/content-based/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["user_id", "recommendations", "recommendation_type", "total_count", "generated_at"]
        for field in required_fields:
            assert field in data
        
        # Check recommendation items structure
        for rec in data["recommendations"]:
            assert "book" in rec
            assert "score" in rec
            assert "reason" in rec
            assert "recommendation_type" in rec
            
            # Check book structure
            book = rec["book"]
            assert "id" in book
            assert "title" in book
            assert "author" in book

    def test_error_handling_in_recommendations(self, client: TestClient, auth_headers):
        """Test error handling in recommendation endpoints"""
        with patch('app.services.recommendation_service.RecommendationService.get_content_based_recommendations') as mock_recommendations:
            mock_recommendations.side_effect = Exception("Test error")
            
            response = client.get("/api/v1/recommendations/content-based/", headers=auth_headers)
            
            assert response.status_code == 500
            assert "Failed to generate content-based recommendations" in response.json()["detail"] 