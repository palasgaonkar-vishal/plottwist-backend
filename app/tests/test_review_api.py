"""
Tests for Review API endpoints.
Comprehensive testing of review CRUD operations via HTTP API.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.book import Book
from app.models.review import Review


class TestReviewAPI:
    """Test class for Review API endpoints."""
    
    def test_create_review_success(self, client: TestClient, sample_user: User, sample_book: Book, auth_headers):
        """Test successful review creation via API."""
        review_data = {
            "book_id": sample_book.id,
            "rating": 4.5,
            "title": "Great book!",
            "content": "Really enjoyed this book. Highly recommended."
        }
        
        response = client.post("/api/v1/reviews/", json=review_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["book_id"] == sample_book.id
        assert data["user_id"] == sample_user.id
        assert data["rating"] == 4.5
        assert data["title"] == "Great book!"
        assert data["content"] == "Really enjoyed this book. Highly recommended."
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_review_unauthorized(self, client: TestClient, sample_book: Book):
        """Test review creation without authentication."""
        review_data = {
            "book_id": sample_book.id,
            "rating": 4.5,
            "title": "Great book!",
            "content": "Really enjoyed this book."
        }
        
        response = client.post("/api/v1/reviews/", json=review_data)
        assert response.status_code == 403
    
    def test_create_review_invalid_rating(self, client: TestClient, sample_book: Book, auth_headers):
        """Test review creation with invalid rating."""
        review_data = {
            "book_id": sample_book.id,
            "rating": 6.0,  # Invalid rating > 5.0
            "title": "Great book!",
            "content": "Really enjoyed this book."
        }
        
        response = client.post("/api/v1/reviews/", json=review_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_create_review_book_not_found(self, client: TestClient, auth_headers):
        """Test review creation for non-existent book."""
        review_data = {
            "book_id": 99999,
            "rating": 4.5,
            "title": "Great book!",
            "content": "Really enjoyed this book."
        }
        
        response = client.post("/api/v1/reviews/", json=review_data, headers=auth_headers)
        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]
    
    def test_get_review_success(self, client: TestClient, db_session: Session, sample_user: User, sample_book: Book):
        """Test successful review retrieval via API."""
        # Create review directly in database
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.5,
            title="Great book!",
            content="Really enjoyed this book."
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        
        response = client.get(f"/api/v1/reviews/{review.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review.id
        assert data["rating"] == 4.5
        assert data["title"] == "Great book!"
    
    def test_get_review_not_found(self, client: TestClient):
        """Test retrieval of non-existent review."""
        response = client.get("/api/v1/reviews/99999")
        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]
    
    def test_update_review_success(self, client: TestClient, db_session: Session, sample_user: User, sample_book: Book, auth_headers):
        """Test successful review update via API."""
        # Create review directly in database
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.0,
            title="Good book",
            content="It was okay."
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        
        update_data = {
            "rating": 5.0,
            "title": "Amazing book!",
            "content": "Actually, this book was incredible!"
        }
        
        response = client.put(f"/api/v1/reviews/{review.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5.0
        assert data["title"] == "Amazing book!"
        assert data["content"] == "Actually, this book was incredible!"
    
    def test_update_review_unauthorized(self, client: TestClient, db_session: Session, sample_user: User, sample_book: Book):
        """Test review update without authentication."""
        # Create review directly in database
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.0,
            title="Good book",
            content="It was okay."
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        
        update_data = {"rating": 5.0}
        
        response = client.put(f"/api/v1/reviews/{review.id}", json=update_data)
        assert response.status_code == 403
    
    def test_update_review_forbidden(self, client: TestClient, db_session: Session, sample_user: User, sample_book: Book):
        """Test review update by non-owner."""
        # Create review directly in database
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.0,
            title="Good book",
            content="It was okay."
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        
        # Create another user
        other_user = User(
            email="other@example.com",
            name="Other User",
            hashed_password="hashedpassword"
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        # Create auth headers for other user
        from app.core.security import create_access_token
        token = create_access_token(subject=str(other_user.id))
        other_auth_headers = {"Authorization": f"Bearer {token}"}
        
        update_data = {"rating": 5.0}
        
        response = client.put(f"/api/v1/reviews/{review.id}", json=update_data, headers=other_auth_headers)
        assert response.status_code == 403
        assert "only update your own reviews" in response.json()["detail"]
    
    def test_delete_review_success(self, client: TestClient, db_session: Session, sample_user: User, sample_book: Book, auth_headers):
        """Test successful review deletion via API."""
        # Create review directly in database
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.0,
            title="Good book",
            content="It was okay."
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        review_id = review.id
        
        response = client.delete(f"/api/v1/reviews/{review_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify review is deleted
        response = client.get(f"/api/v1/reviews/{review_id}")
        assert response.status_code == 404
    
    def test_delete_review_unauthorized(self, client: TestClient, db_session: Session, sample_user: User, sample_book: Book):
        """Test review deletion without authentication."""
        # Create review directly in database
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.0,
            title="Good book",
            content="It was okay."
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        
        response = client.delete(f"/api/v1/reviews/{review.id}")
        assert response.status_code == 403
    
    def test_get_book_reviews(self, client: TestClient, db_session: Session, sample_book: Book):
        """Test getting reviews for a specific book."""
        # Create users and reviews
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
                hashed_password="hashedpassword"
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            review = Review(
                user_id=user.id,
                book_id=sample_book.id,
                rating=float(i + 1),
                title=f"Review {i + 1}",
                content=f"Content {i + 1}"
            )
            db_session.add(review)
        
        db_session.commit()
        
        response = client.get(f"/api/v1/reviews/book/{sample_book.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 5
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 10
        assert data["total_pages"] == 1
    
    def test_get_book_reviews_pagination(self, client: TestClient, db_session: Session, sample_book: Book):
        """Test book reviews pagination."""
        # Create users and reviews
        for i in range(15):
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
                hashed_password="hashedpassword"
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            review = Review(
                user_id=user.id,
                book_id=sample_book.id,
                rating=float((i % 5) + 1),
                title=f"Review {i + 1}",
                content=f"Content {i + 1}"
            )
            db_session.add(review)
        
        db_session.commit()
        
        response = client.get(f"/api/v1/reviews/book/{sample_book.id}?page=2&per_page=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 5
        assert data["total"] == 15
        assert data["page"] == 2
        assert data["per_page"] == 5
        assert data["total_pages"] == 3
    
    def test_get_book_rating_stats(self, client: TestClient, db_session: Session, sample_book: Book):
        """Test getting book rating statistics."""
        # Create users and reviews with specific ratings
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
            
            review = Review(
                user_id=user.id,
                book_id=sample_book.id,
                rating=rating,
                title=f"Review {i + 1}",
                content=f"Content {i + 1}"
            )
            db_session.add(review)
        
        db_session.commit()
        
        response = client.get(f"/api/v1/reviews/book/{sample_book.id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == sample_book.id
        assert data["total_reviews"] == 7
        assert data["average_rating"] is not None
        assert "rating_distribution" in data
        assert data["rating_distribution"]["1"] == 1
        assert data["rating_distribution"]["5"] == 2
    
    def test_get_my_reviews(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """Test getting current user's reviews."""
        # Create books and reviews
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
            
            review = Review(
                user_id=sample_user.id,
                book_id=book.id,
                rating=float(i + 3),
                title=f"Review {i + 1}",
                content=f"Content {i + 1}"
            )
            db_session.add(review)
        
        db_session.commit()
        
        response = client.get("/api/v1/reviews/user/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 3
        assert data["total"] == 3
        assert all(review["user_id"] == sample_user.id for review in data["reviews"])
    
    def test_get_my_reviews_unauthorized(self, client: TestClient):
        """Test getting user reviews without authentication."""
        response = client.get("/api/v1/reviews/user/me")
        assert response.status_code == 403
    
    def test_get_my_review_stats(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """Test getting current user's review statistics."""
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
            
            review = Review(
                user_id=sample_user.id,
                book_id=book.id,
                rating=rating,
                title=f"Review {i + 1}",
                content=f"Content {i + 1}"
            )
            db_session.add(review)
        
        db_session.commit()
        
        response = client.get("/api/v1/reviews/user/me/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == sample_user.id
        assert data["total_reviews"] == 3
        assert data["average_rating_given"] == 4.0
    
    def test_get_my_review_for_book(self, client: TestClient, db_session: Session, sample_user: User, sample_book: Book, auth_headers):
        """Test getting current user's review for a specific book."""
        # Create review directly in database
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.5,
            title="Great book!",
            content="Really enjoyed this book."
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        
        response = client.get(f"/api/v1/reviews/user/me/book/{sample_book.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review.id
        assert data["user_id"] == sample_user.id
        assert data["book_id"] == sample_book.id
        assert data["rating"] == 4.5
    
    def test_get_my_review_for_book_not_found(self, client: TestClient, sample_book: Book, auth_headers):
        """Test getting non-existent user review for book."""
        response = client.get(f"/api/v1/reviews/user/me/book/{sample_book.id}", headers=auth_headers) 