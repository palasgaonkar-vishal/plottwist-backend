import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.models.user import User
from app.models.favorite import Favorite
from app.models.review import Review


class TestUsersAPI:
    def test_get_current_user_info(self, client: TestClient, auth_headers):
        """Test getting current user's basic information"""
        response = client.get("/api/v1/users/me/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "is_active" in data
        assert "is_verified" in data

    def test_get_current_user_info_unauthorized(self, client: TestClient):
        """Test getting current user info without authentication"""
        response = client.get("/api/v1/users/me/")
        
        assert response.status_code == 403

    def test_get_current_user_profile(self, client: TestClient, auth_headers):
        """Test getting current user's full profile with statistics"""
        response = client.get("/api/v1/users/me/profile/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "stats" in data
        
        # Verify stats structure
        stats = data["stats"]
        assert "total_reviews" in stats
        assert "average_rating_given" in stats
        assert "total_favorites" in stats
        assert "books_reviewed" in stats
        assert "reviews_this_month" in stats

    def test_update_current_user_profile(self, client: TestClient, auth_headers):
        """Test updating current user's profile"""
        update_data = {
            "name": "Updated Name",
            "bio": "Updated bio",
            "location": "New City",
            "website": "https://example.com"
        }
        
        response = client.put("/api/v1/users/me/", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_profile_with_existing_email(self, client: TestClient, auth_headers, sample_user, db_session):
        """Test updating profile with email that already exists"""
        # Create another user in the database
        another_user = User(
            email="another@example.com",
            name="Another User",
            hashed_password="hashedpassword"
        )
        db_session.add(another_user)
        db_session.commit()
        
        update_data = {
            "email": "another@example.com"  # This email should already exist
        }
        
        response = client.put("/api/v1/users/me/", json=update_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_update_profile_validation_errors(self, client: TestClient, auth_headers):
        """Test profile update with validation errors"""
        update_data = {
            "name": "A",  # Too short
            "bio": "x" * 501,  # Too long
            "location": "x" * 101,  # Too long
            "website": "x" * 201  # Too long
        }
        
        response = client.put("/api/v1/users/me/", json=update_data, headers=auth_headers)
        
        assert response.status_code == 422

    def test_get_current_user_reviews(self, client: TestClient, auth_headers):
        """Test getting current user's reviews with pagination"""
        response = client.get("/api/v1/users/me/reviews/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "reviews" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data

    def test_get_current_user_reviews_with_params(self, client: TestClient, auth_headers):
        """Test getting user reviews with pagination parameters"""
        params = {
            "page": 1,
            "per_page": 5,
            "sort_by": "rating",
            "sort_order": "desc"
        }
        
        response = client.get("/api/v1/users/me/reviews/", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5

    def test_get_current_user_stats(self, client: TestClient, auth_headers):
        """Test getting current user's profile statistics"""
        response = client.get("/api/v1/users/me/stats/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_reviews" in data
        assert "average_rating_given" in data
        assert "total_favorites" in data
        assert "books_reviewed" in data
        assert "reviews_this_month" in data

    def test_get_user_by_id_public(self, client: TestClient, sample_user):
        """Test getting user by ID (public information)"""
        response = client.get(f"/api/v1/users/{sample_user.id}/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["name"] == sample_user.name
        assert data["email"] == sample_user.email

    def test_get_user_by_id_not_found(self, client: TestClient):
        """Test getting non-existent user by ID"""
        response = client.get("/api/v1/users/99999/")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_user_profile_by_id_public(self, client: TestClient, sample_user):
        """Test getting user's public profile by ID"""
        response = client.get(f"/api/v1/users/{sample_user.id}/profile/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert "stats" in data


class TestFavoritesAPI:
    def test_add_favorite(self, client: TestClient, auth_headers, sample_book):
        """Test adding a book to favorites"""
        favorite_data = {"book_id": sample_book.id}
        
        response = client.post("/api/v1/favorites/", json=favorite_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == sample_book.id
        assert "id" in data
        assert "created_at" in data

    def test_add_favorite_book_not_found(self, client: TestClient, auth_headers):
        """Test adding favorite for non-existent book"""
        favorite_data = {"book_id": 99999}
        
        response = client.post("/api/v1/favorites/", json=favorite_data, headers=auth_headers)
        
        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

    def test_add_favorite_unauthorized(self, client: TestClient, sample_book):
        """Test adding favorite without authentication"""
        favorite_data = {"book_id": sample_book.id}
        
        response = client.post("/api/v1/favorites/", json=favorite_data)
        
        assert response.status_code == 403

    def test_remove_favorite(self, client: TestClient, auth_headers, sample_book, sample_user, db_session):
        """Test removing a book from favorites"""
        # First add a favorite
        favorite = Favorite(user_id=sample_user.id, book_id=sample_book.id)
        db_session.add(favorite)
        db_session.commit()
        
        response = client.delete(f"/api/v1/favorites/{sample_book.id}/", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Favorite removed successfully" in response.json()["message"]

    def test_remove_favorite_not_found(self, client: TestClient, auth_headers, sample_book):
        """Test removing non-existent favorite"""
        response = client.delete(f"/api/v1/favorites/{sample_book.id}/", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Favorite not found" in response.json()["detail"]

    def test_toggle_favorite_add(self, client: TestClient, auth_headers, sample_book):
        """Test toggling favorite (adding)"""
        response = client.post(f"/api/v1/favorites/toggle/{sample_book.id}/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] is True
        assert "Added to favorites" in data["message"]

    def test_toggle_favorite_remove(self, client: TestClient, auth_headers, sample_book, sample_user, db_session):
        """Test toggling favorite (removing)"""
        # First add a favorite
        favorite = Favorite(user_id=sample_user.id, book_id=sample_book.id)
        db_session.add(favorite)
        db_session.commit()
        
        response = client.post(f"/api/v1/favorites/toggle/{sample_book.id}/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] is False
        assert "Removed from favorites" in data["message"]

    def test_check_favorite_status_true(self, client: TestClient, auth_headers, sample_book, sample_user, db_session):
        """Test checking favorite status (favorited)"""
        # Add a favorite
        favorite = Favorite(user_id=sample_user.id, book_id=sample_book.id)
        db_session.add(favorite)
        db_session.commit()
        
        response = client.get(f"/api/v1/favorites/check/{sample_book.id}/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] is True

    def test_check_favorite_status_false(self, client: TestClient, auth_headers, sample_book):
        """Test checking favorite status (not favorited)"""
        response = client.get(f"/api/v1/favorites/check/{sample_book.id}/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] is False

    def test_get_my_favorites(self, client: TestClient, auth_headers, sample_user, multiple_books, db_session):
        """Test getting current user's favorites"""
        # Add some favorites
        for book in multiple_books[:3]:
            favorite = Favorite(user_id=sample_user.id, book_id=book.id)
            db_session.add(favorite)
        db_session.commit()
        
        response = client.get("/api/v1/favorites/me/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["favorites"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_get_my_favorites_with_pagination(self, client: TestClient, auth_headers):
        """Test getting favorites with pagination parameters"""
        params = {"page": 1, "per_page": 5}
        
        response = client.get("/api/v1/favorites/me/", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5

    def test_get_my_favorites_count(self, client: TestClient, auth_headers, sample_user, multiple_books, db_session):
        """Test getting count of user's favorites"""
        # Add some favorites
        for book in multiple_books[:2]:
            favorite = Favorite(user_id=sample_user.id, book_id=book.id)
            db_session.add(favorite)
        db_session.commit()
        
        response = client.get("/api/v1/favorites/count/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_get_book_favorites_count(self, client: TestClient, sample_book, multiple_users, db_session):
        """Test getting count of users who favorited a book"""
        # Add favorites from multiple users
        for user in multiple_users[:2]:
            favorite = Favorite(user_id=user.id, book_id=sample_book.id)
            db_session.add(favorite)
        db_session.commit()
        
        response = client.get(f"/api/v1/favorites/book/{sample_book.id}/count/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_get_popular_books(self, client: TestClient, multiple_books, multiple_users, db_session):
        """Test getting most favorited books"""
        # Add favorites for different books
        for i, book in enumerate(multiple_books[:2]):
            for j in range(i + 1):  # Different amounts of favorites
                favorite = Favorite(user_id=multiple_users[j].id, book_id=book.id)
                db_session.add(favorite)
        db_session.commit()
        
        response = client.get("/api/v1/favorites/popular/")
        
        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert len(data["books"]) >= 1
        
        # Verify structure
        if data["books"]:
            first_book = data["books"][0]
            assert "book" in first_book
            assert "favorite_count" in first_book

    def test_get_popular_books_with_limit(self, client: TestClient):
        """Test getting popular books with limit parameter"""
        params = {"limit": 5}
        
        response = client.get("/api/v1/favorites/popular/", params=params)
        
        assert response.status_code == 200 