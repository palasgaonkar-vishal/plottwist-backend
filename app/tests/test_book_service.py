"""
Unit tests for book service operations.
Tests BookService and GenreService functionality including CRUD operations, search, and pagination.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.services.book_service import BookService, GenreService
from app.models.book import Book, Genre
from app.models.user import User
from app.schemas.book import BookCreate, BookUpdate, BookSearchQuery


class TestBookService:
    """Tests for BookService class."""

    def test_get_book_by_id_success(self, db_session: Session, sample_book: Book):
        """Test successfully getting a book by ID."""
        service = BookService(db_session)
        
        result = service.get_book_by_id(sample_book.id)
        
        assert result is not None
        assert result.id == sample_book.id
        assert result.title == sample_book.title

    def test_get_book_by_id_not_found(self, db_session: Session):
        """Test getting a book by non-existent ID."""
        service = BookService(db_session)
        
        result = service.get_book_by_id(999)
        
        assert result is None

    def test_get_book_by_isbn_success(self, db_session: Session, sample_book: Book):
        """Test successfully getting a book by ISBN."""
        service = BookService(db_session)
        
        result = service.get_book_by_isbn(sample_book.isbn)
        
        assert result is not None
        assert result.isbn == sample_book.isbn
        assert result.title == sample_book.title

    def test_get_book_by_isbn_not_found(self, db_session: Session):
        """Test getting a book by non-existent ISBN."""
        service = BookService(db_session)
        
        result = service.get_book_by_isbn("9999999999999")
        
        assert result is None

    def test_get_books_pagination(self, db_session: Session, multiple_books: list[Book]):
        """Test book listing with pagination."""
        service = BookService(db_session)
        
        # Test first page
        books, total = service.get_books(page=1, per_page=2)
        
        assert len(books) == 2
        assert total == len(multiple_books)
        
        # Test second page
        books, total = service.get_books(page=2, per_page=2)
        
        assert len(books) <= 2
        assert total == len(multiple_books)

    def test_get_books_with_genre_filter(self, db_session: Session, multiple_books: list[Book], sample_genre: Genre):
        """Test book listing with genre filter."""
        service = BookService(db_session)
        
        # Assign genre to first book
        multiple_books[0].genres.append(sample_genre)
        db_session.commit()
        
        books, total = service.get_books(genre_id=sample_genre.id)
        
        assert len(books) >= 1
        assert all(sample_genre in book.genres for book in books)

    def test_get_books_with_rating_filter(self, db_session: Session, multiple_books: list[Book]):
        """Test book listing with minimum rating filter."""
        service = BookService(db_session)
        
        # Set different ratings
        multiple_books[0].average_rating = 4.5
        multiple_books[1].average_rating = 3.0
        db_session.commit()
        
        books, total = service.get_books(min_rating=4.0)
        
        assert all(book.average_rating >= 4.0 for book in books)

    def test_search_books_by_title(self, db_session: Session, multiple_books: list[Book]):
        """Test searching books by title."""
        service = BookService(db_session)
        
        search_params = BookSearchQuery(
            query=multiple_books[0].title[:5],  # Partial title search
            page=1,
            per_page=10
        )
        
        books, total = service.search_books(search_params)
        
        assert len(books) >= 1
        assert any(multiple_books[0].title.lower() in book.title.lower() for book in books)

    def test_search_books_by_author(self, db_session: Session, multiple_books: list[Book]):
        """Test searching books by author."""
        service = BookService(db_session)
        
        search_params = BookSearchQuery(
            query=multiple_books[0].author[:5],  # Partial author search
            page=1,
            per_page=10
        )
        
        books, total = service.search_books(search_params)
        
        assert len(books) >= 1
        assert any(multiple_books[0].author.lower() in book.author.lower() for book in books)

    def test_search_books_with_year_filter(self, db_session: Session, multiple_books: list[Book]):
        """Test searching books with publication year filter."""
        service = BookService(db_session)
        
        # Set publication years
        multiple_books[0].published_year = 2020
        multiple_books[1].published_year = 2018
        db_session.commit()
        
        search_params = BookSearchQuery(
            published_year_start=2019,
            published_year_end=2021,
            page=1,
            per_page=10
        )
        
        books, total = service.search_books(search_params)
        
        for book in books:
            if book.published_year:
                assert 2019 <= book.published_year <= 2021

    def test_create_book_success(self, db_session: Session, sample_genre: Genre):
        """Test successfully creating a book."""
        service = BookService(db_session)
        
        book_data = BookCreate(
            title="Test Book",
            author="Test Author",
            description="A test book description",
            published_year=2023,
            isbn="9781234567890",
            cover_url="https://example.com/cover.jpg",
            genre_ids=[sample_genre.id]
        )
        
        book = service.create_book(book_data)
        
        assert book.id is not None
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert book.average_rating == 0.0
        assert book.total_reviews == 0
        assert len(book.genres) == 1
        assert book.genres[0].id == sample_genre.id

    def test_create_book_without_genres(self, db_session: Session):
        """Test creating a book without genres."""
        service = BookService(db_session)
        
        book_data = BookCreate(
            title="Test Book Without Genres",
            author="Test Author",
            description="A test book description",
            published_year=2023,
            isbn="9781234567891"
        )
        
        book = service.create_book(book_data)
        
        assert book.id is not None
        assert book.title == "Test Book Without Genres"
        assert len(book.genres) == 0

    def test_update_book_success(self, db_session: Session, sample_book: Book, sample_genre: Genre):
        """Test successfully updating a book."""
        service = BookService(db_session)
        
        update_data = BookUpdate(
            title="Updated Title",
            description="Updated description",
            genre_ids=[sample_genre.id]
        )
        
        updated_book = service.update_book(sample_book.id, update_data)
        
        assert updated_book is not None
        assert updated_book.title == "Updated Title"
        assert updated_book.description == "Updated description"
        assert len(updated_book.genres) == 1
        assert updated_book.genres[0].id == sample_genre.id

    def test_update_book_not_found(self, db_session: Session):
        """Test updating a non-existent book."""
        service = BookService(db_session)
        
        update_data = BookUpdate(title="Updated Title")
        
        result = service.update_book(999, update_data)
        
        assert result is None

    def test_delete_book_success(self, db_session: Session, sample_book: Book):
        """Test successfully deleting a book."""
        service = BookService(db_session)
        book_id = sample_book.id
        
        result = service.delete_book(book_id)
        
        assert result is True
        
        # Verify book is deleted
        deleted_book = service.get_book_by_id(book_id)
        assert deleted_book is None

    def test_delete_book_not_found(self, db_session: Session):
        """Test deleting a non-existent book."""
        service = BookService(db_session)
        
        result = service.delete_book(999)
        
        assert result is False

    def test_update_book_statistics(self, db_session: Session, sample_book: Book, sample_user: User):
        """Test updating book statistics."""
        from app.models.review import Review
        
        service = BookService(db_session)
        
        # Create some reviews for the book
        reviews = [
            Review(user_id=sample_user.id, book_id=sample_book.id, rating=5, title="Great", content="Loved it"),
            Review(user_id=sample_user.id, book_id=sample_book.id, rating=4, title="Good", content="Nice book"),
        ]
        
        # Since we have a unique constraint, we need to use different user IDs
        # Let's create additional users
        user2 = User(
            email="user2@example.com",
            name="User Two",
            hashed_password="hashedpass",
            is_active=True,
            is_verified=True
        )
        db_session.add(user2)
        db_session.flush()
        
        reviews[1].user_id = user2.id  # Use different user for second review
        
        for review in reviews:
            db_session.add(review)
        db_session.commit()
        
        updated_book = service.update_book_statistics(sample_book.id)
        
        assert updated_book is not None
        assert updated_book.total_reviews == 2
        assert updated_book.average_rating == 4.5  # (5 + 4) / 2


class TestGenreService:
    """Tests for GenreService class."""

    def test_get_all_genres(self, db_session: Session, multiple_genres: list[Genre]):
        """Test getting all genres."""
        service = GenreService(db_session)
        
        genres = service.get_all_genres()
        
        assert len(genres) == len(multiple_genres)
        assert all(isinstance(genre, Genre) for genre in genres)

    def test_get_genre_by_id_success(self, db_session: Session, sample_genre: Genre):
        """Test successfully getting a genre by ID."""
        service = GenreService(db_session)
        
        result = service.get_genre_by_id(sample_genre.id)
        
        assert result is not None
        assert result.id == sample_genre.id
        assert result.name == sample_genre.name

    def test_get_genre_by_id_not_found(self, db_session: Session):
        """Test getting a genre by non-existent ID."""
        service = GenreService(db_session)
        
        result = service.get_genre_by_id(999)
        
        assert result is None

    def test_get_genre_by_name_success(self, db_session: Session, sample_genre: Genre):
        """Test successfully getting a genre by name."""
        service = GenreService(db_session)
        
        result = service.get_genre_by_name(sample_genre.name)
        
        assert result is not None
        assert result.name == sample_genre.name

    def test_get_genre_by_name_not_found(self, db_session: Session):
        """Test getting a genre by non-existent name."""
        service = GenreService(db_session)
        
        result = service.get_genre_by_name("NonExistentGenre")
        
        assert result is None

    def test_create_genre_success(self, db_session: Session):
        """Test successfully creating a genre."""
        service = GenreService(db_session)
        
        genre = service.create_genre(
            name="Test Genre",
            description="A test genre description"
        )
        
        assert genre.id is not None
        assert genre.name == "Test Genre"
        assert genre.description == "A test genre description"

    def test_create_genre_without_description(self, db_session: Session):
        """Test creating a genre without description."""
        service = GenreService(db_session)
        
        genre = service.create_genre(name="Test Genre No Desc")
        
        assert genre.id is not None
        assert genre.name == "Test Genre No Desc"
        assert genre.description is None

    def test_update_genre_success(self, db_session: Session, sample_genre: Genre):
        """Test successfully updating a genre."""
        service = GenreService(db_session)
        
        updated_genre = service.update_genre(
            sample_genre.id,
            name="Updated Genre",
            description="Updated description"
        )
        
        assert updated_genre is not None
        assert updated_genre.name == "Updated Genre"
        assert updated_genre.description == "Updated description"

    def test_update_genre_partial(self, db_session: Session, sample_genre: Genre):
        """Test partially updating a genre."""
        service = GenreService(db_session)
        original_description = sample_genre.description
        
        updated_genre = service.update_genre(
            sample_genre.id,
            name="Partially Updated Genre"
        )
        
        assert updated_genre is not None
        assert updated_genre.name == "Partially Updated Genre"
        assert updated_genre.description == original_description

    def test_update_genre_not_found(self, db_session: Session):
        """Test updating a non-existent genre."""
        service = GenreService(db_session)
        
        result = service.update_genre(999, name="Updated Genre")
        
        assert result is None

    def test_delete_genre_success(self, db_session: Session, sample_genre: Genre):
        """Test successfully deleting a genre."""
        service = GenreService(db_session)
        genre_id = sample_genre.id
        
        result = service.delete_genre(genre_id)
        
        assert result is True
        
        # Verify genre is deleted
        deleted_genre = service.get_genre_by_id(genre_id)
        assert deleted_genre is None

    def test_delete_genre_not_found(self, db_session: Session):
        """Test deleting a non-existent genre."""
        service = GenreService(db_session)
        
        result = service.delete_genre(999)
        
        assert result is False 