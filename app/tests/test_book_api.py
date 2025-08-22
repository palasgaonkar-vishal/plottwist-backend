"""
Unit tests for book API endpoints.
Tests all book-related API operations including listing, searching, CRUD operations, and genre endpoints.
"""

# pytest used for fixtures and test functions
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.book import Book, Genre

# User model used in auth headers fixtures


class TestBookAPI:
    """Tests for book API endpoints."""

    def test_list_books_success(self, client: TestClient, multiple_books: list[Book]):
        """Test successful book listing."""
        response = client.get("/api/v1/books/")

        assert response.status_code == 200
        data = response.json()

        assert "books" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data

        assert len(data["books"]) <= 10  # Default per_page
        assert data["total"] >= len(multiple_books)
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_list_books_pagination(
        self, client: TestClient, multiple_books: list[Book]
    ):
        """Test book listing with pagination."""
        response = client.get("/api/v1/books/?page=1&per_page=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data["books"]) <= 2
        assert data["page"] == 1
        assert data["per_page"] == 2

    def test_list_books_invalid_pagination(self, client: TestClient):
        """Test book listing with invalid pagination parameters."""
        # Test page < 1
        response = client.get("/api/v1/books/?page=0")
        assert response.status_code == 422

        # Test per_page > 100
        response = client.get("/api/v1/books/?per_page=101")
        assert response.status_code == 422

    def test_list_books_with_genre_filter(
        self,
        client: TestClient,
        sample_book: Book,
        sample_genre: Genre,
        db_session: Session,
    ):
        """Test book listing with genre filter."""
        # Assign genre to book
        sample_book.genres.append(sample_genre)
        db_session.commit()

        response = client.get(f"/api/v1/books/?genre_id={sample_genre.id}")

        assert response.status_code == 200
        data = response.json()

        # All returned books should have the specified genre
        for book in data["books"]:
            genre_ids = [genre["id"] for genre in book["genres"]]
            assert sample_genre.id in genre_ids

    def test_list_books_with_rating_filter(
        self, client: TestClient, multiple_books: list[Book], db_session: Session
    ):
        """Test book listing with minimum rating filter."""
        # Set different ratings for books
        multiple_books[0].average_rating = 4.5
        multiple_books[1].average_rating = 3.0
        db_session.commit()

        response = client.get("/api/v1/books/?min_rating=4.0")

        assert response.status_code == 200
        data = response.json()

        # All returned books should have rating >= 4.0
        for book in data["books"]:
            assert book["average_rating"] >= 4.0

    def test_search_books_by_query(self, client: TestClient, sample_book: Book):
        """Test searching books by title/author query."""
        search_term = sample_book.title[:5]
        response = client.get(f"/api/v1/books/search?query={search_term}")

        assert response.status_code == 200
        data = response.json()

        assert "books" in data
        assert "query" in data
        assert "filters_applied" in data
        assert data["query"] == search_term

        # At least one book should match
        assert len(data["books"]) >= 1

    def test_search_books_with_multiple_filters(
        self,
        client: TestClient,
        sample_book: Book,
        sample_genre: Genre,
        db_session: Session,
    ):
        """Test searching books with multiple filters."""
        # Setup book with specific attributes
        sample_book.published_year = 2020
        sample_book.average_rating = 4.0
        sample_book.genres.append(sample_genre)
        db_session.commit()

        response = client.get(
            f"/api/v1/books/search?"
            f"genre_id={sample_genre.id}&"
            f"min_rating=3.5&"
            f"published_year_start=2019&"
            f"published_year_end=2021"
        )

        assert response.status_code == 200
        data = response.json()

        filters_applied = data["filters_applied"]
        assert "genre_id" in filters_applied
        assert "min_rating" in filters_applied
        assert "published_year_start" in filters_applied
        assert "published_year_end" in filters_applied

    def test_search_books_no_results(self, client: TestClient):
        """Test searching books with no matching results."""
        response = client.get("/api/v1/books/search?query=nonexistentbooktitle12345")

        assert response.status_code == 200
        data = response.json()

        assert len(data["books"]) == 0
        assert data["total"] == 0

    def test_get_book_success(self, client: TestClient, sample_book: Book):
        """Test successfully getting a specific book."""
        response = client.get(f"/api/v1/books/{sample_book.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_book.id
        assert data["title"] == sample_book.title
        assert data["author"] == sample_book.author
        assert "genres" in data
        assert "average_rating" in data
        assert "total_reviews" in data

    def test_get_book_not_found(self, client: TestClient):
        """Test getting a non-existent book."""
        response = client.get("/api/v1/books/999")

        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

    def test_create_book_success(
        self, client: TestClient, auth_headers: dict, sample_genre: Genre
    ):
        """Test successfully creating a book."""
        book_data = {
            "title": "New Test Book",
            "author": "Test Author",
            "description": "A new test book",
            "published_year": 2023,
            "isbn": "9781234567890",
            "cover_url": "https://example.com/cover.jpg",
            "genre_ids": [sample_genre.id],
        }

        response = client.post("/api/v1/books/", json=book_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == book_data["title"]
        assert data["author"] == book_data["author"]
        assert data["isbn"] == book_data["isbn"]
        assert len(data["genres"]) == 1
        assert data["genres"][0]["id"] == sample_genre.id

    def test_create_book_unauthorized(self, client: TestClient, sample_genre: Genre):
        """Test creating a book without authentication."""
        book_data = {
            "title": "Unauthorized Book",
            "author": "Test Author",
            "genre_ids": [sample_genre.id],
        }

        response = client.post("/api/v1/books/", json=book_data)

        assert response.status_code == 403

    def test_create_book_duplicate_isbn(
        self, client: TestClient, auth_headers: dict, sample_book: Book
    ):
        """Test creating a book with duplicate ISBN."""
        book_data = {
            "title": "Duplicate ISBN Book",
            "author": "Test Author",
            "isbn": sample_book.isbn,  # Duplicate ISBN
            "genre_ids": [],
        }

        response = client.post("/api/v1/books/", json=book_data, headers=auth_headers)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_book_invalid_data(self, client: TestClient, auth_headers: dict):
        """Test creating a book with invalid data."""
        book_data = {
            "title": "",  # Empty title
            "author": "Test Author",
            "published_year": 3000,  # Invalid year
            "genre_ids": [],
        }

        response = client.post("/api/v1/books/", json=book_data, headers=auth_headers)

        assert response.status_code == 422

    def test_update_book_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_book: Book,
        sample_genre: Genre,
    ):
        """Test successfully updating a book."""
        update_data = {
            "title": "Updated Book Title",
            "description": "Updated description",
            "genre_ids": [sample_genre.id],
        }

        response = client.put(
            f"/api/v1/books/{sample_book.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Updated Book Title"
        assert data["description"] == "Updated description"
        assert len(data["genres"]) == 1
        assert data["genres"][0]["id"] == sample_genre.id

    def test_update_book_unauthorized(self, client: TestClient, sample_book: Book):
        """Test updating a book without authentication."""
        update_data = {"title": "Unauthorized Update"}

        response = client.put(f"/api/v1/books/{sample_book.id}", json=update_data)

        assert response.status_code == 403

    def test_update_book_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating a non-existent book."""
        update_data = {"title": "Updated Title"}

        response = client.put(
            "/api/v1/books/999", json=update_data, headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_book_success(
        self, client: TestClient, auth_headers: dict, sample_book: Book
    ):
        """Test successfully deleting a book."""
        book_id = sample_book.id

        response = client.delete(f"/api/v1/books/{book_id}", headers=auth_headers)

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify book is deleted
        get_response = client.get(f"/api/v1/books/{book_id}")
        assert get_response.status_code == 404

    def test_delete_book_unauthorized(self, client: TestClient, sample_book: Book):
        """Test deleting a book without authentication."""
        response = client.delete(f"/api/v1/books/{sample_book.id}")

        assert response.status_code == 403

    def test_delete_book_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting a non-existent book."""
        response = client.delete("/api/v1/books/999", headers=auth_headers)

        assert response.status_code == 404


class TestGenreAPI:
    """Tests for genre API endpoints."""

    def test_list_genres_success(
        self, client: TestClient, multiple_genres: list[Genre]
    ):
        """Test successfully listing all genres."""
        response = client.get("/api/v1/books/genres/")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == len(multiple_genres)

        # Check genre structure
        for genre in data:
            assert "id" in genre
            assert "name" in genre
            assert "description" in genre
            assert "created_at" in genre

    def test_get_genre_success(self, client: TestClient, sample_genre: Genre):
        """Test successfully getting a specific genre."""
        response = client.get(f"/api/v1/books/genres/{sample_genre.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_genre.id
        assert data["name"] == sample_genre.name
        assert data["description"] == sample_genre.description

    def test_get_genre_not_found(self, client: TestClient):
        """Test getting a non-existent genre."""
        response = client.get("/api/v1/books/genres/999")

        assert response.status_code == 404
        assert "Genre not found" in response.json()["detail"]

    def test_list_genres_empty(self, client: TestClient, db_session: Session):
        """Test listing genres when no genres exist."""
        # Clear all genres
        db_session.query(Genre).delete()
        db_session.commit()

        response = client.get("/api/v1/books/genres/")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0
