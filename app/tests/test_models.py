import pytest

# datetime used in model creation tests
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.book import Book, Genre
from app.models.review import Review
from app.models.favorite import Favorite
from app.core.security import get_password_hash


class TestUserModel:
    """Test cases for User model."""

    def test_create_user(self, db_session: Session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            name="Test User",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=False,
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.refresh_token is None

    def test_user_email_unique_constraint(self, db_session: Session):
        """Test that user email must be unique."""
        user1 = User(
            email="test@example.com",
            name="Test User 1",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            email="test@example.com",
            name="Test User 2",
            hashed_password=get_password_hash("password456"),
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_repr(self, db_session: Session):
        """Test user string representation."""
        user = User(
            email="test@example.com",
            name="Test User",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        expected = f"<User(id={user.id}, email='test@example.com', name='Test User')>"
        assert repr(user) == expected

    def test_user_relationships(self, db_session: Session):
        """Test user relationships with reviews and favorites."""
        user = User(
            email="test@example.com",
            name="Test User",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()

        # Initially no relationships
        assert len(user.reviews) == 0
        assert len(user.favorites) == 0


class TestGenreModel:
    """Test cases for Genre model."""

    def test_create_genre(self, db_session: Session):
        """Test creating a genre."""
        genre = Genre(
            name="Fiction",
            description="Imaginative or invented stories",
        )
        db_session.add(genre)
        db_session.commit()

        assert genre.id is not None
        assert genre.name == "Fiction"
        assert genre.description == "Imaginative or invented stories"
        assert genre.created_at is not None

    def test_genre_name_unique_constraint(self, db_session: Session):
        """Test that genre name must be unique."""
        genre1 = Genre(name="Fiction", description="First description")
        db_session.add(genre1)
        db_session.commit()

        genre2 = Genre(name="Fiction", description="Second description")
        db_session.add(genre2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_genre_repr(self, db_session: Session):
        """Test genre string representation."""
        genre = Genre(name="Fiction", description="Test description")
        db_session.add(genre)
        db_session.commit()

        expected = f"<Genre(id={genre.id}, name='Fiction')>"
        assert repr(genre) == expected


class TestBookModel:
    """Test cases for Book model."""

    def test_create_book(self, db_session: Session):
        """Test creating a book."""
        book = Book(
            title="Test Book",
            author="Test Author",
            description="A test book description",
            published_year=2023,
            isbn="9781234567890",
            cover_url="https://example.com/cover.jpg",
            average_rating=0.0,
            total_reviews=0,
        )
        db_session.add(book)
        db_session.commit()

        assert book.id is not None
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert book.description == "A test book description"
        assert book.published_year == 2023
        assert book.isbn == "9781234567890"
        assert book.cover_url == "https://example.com/cover.jpg"
        assert book.average_rating == 0.0
        assert book.total_reviews == 0
        assert book.created_at is not None
        assert book.updated_at is not None

    def test_book_isbn_unique_constraint(self, db_session: Session):
        """Test that book ISBN must be unique."""
        book1 = Book(
            title="Book 1",
            author="Author 1",
            isbn="9781234567890",
        )
        db_session.add(book1)
        db_session.commit()

        book2 = Book(
            title="Book 2",
            author="Author 2",
            isbn="9781234567890",
        )
        db_session.add(book2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_book_genre_relationship(self, db_session: Session):
        """Test book-genre many-to-many relationship."""
        # Create genres
        fiction = Genre(name="Fiction")
        mystery = Genre(name="Mystery")
        db_session.add_all([fiction, mystery])
        db_session.commit()

        # Create book
        book = Book(
            title="Test Book",
            author="Test Author",
        )
        book.genres.extend([fiction, mystery])
        db_session.add(book)
        db_session.commit()

        # Test relationship
        assert len(book.genres) == 2
        assert fiction in book.genres
        assert mystery in book.genres
        assert book in fiction.books
        assert book in mystery.books

    def test_book_repr(self, db_session: Session):
        """Test book string representation."""
        book = Book(
            title="Test Book",
            author="Test Author",
        )
        db_session.add(book)
        db_session.commit()

        expected = f"<Book(id={book.id}, title='Test Book', author='Test Author')>"
        assert repr(book) == expected


class TestReviewModel:
    """Test cases for Review model."""

    def test_create_review(self, db_session: Session, sample_user, sample_book):
        """Test creating a review."""
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.5,
            title="Great book!",
            content="This book was really amazing.",
        )
        db_session.add(review)
        db_session.commit()

        assert review.id is not None
        assert review.user_id == sample_user.id
        assert review.book_id == sample_book.id
        assert review.rating == 4.5
        assert review.title == "Great book!"
        assert review.content == "This book was really amazing."
        assert review.created_at is not None
        assert review.updated_at is not None

    def test_review_unique_constraint(
        self, db_session: Session, sample_user, sample_book
    ):
        """Test that user can only review a book once."""
        review1 = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.5,
        )
        db_session.add(review1)
        db_session.commit()

        review2 = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=3.0,
        )
        db_session.add(review2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_review_rating_validation_property(
        self, db_session: Session, sample_user, sample_book
    ):
        """Test review rating validation property."""
        # Valid rating
        review1 = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=3.5,
        )
        assert review1.is_valid_rating is True

        # Invalid ratings
        review2 = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=0.5,
        )
        assert review2.is_valid_rating is False

        review3 = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=5.5,
        )
        assert review3.is_valid_rating is False

    def test_review_relationships(self, db_session: Session, sample_user, sample_book):
        """Test review relationships with user and book."""
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.5,
        )
        db_session.add(review)
        db_session.commit()

        # Test relationships
        assert review.user == sample_user
        assert review.book == sample_book
        assert review in sample_user.reviews
        assert review in sample_book.reviews

    def test_review_repr(self, db_session: Session, sample_user, sample_book):
        """Test review string representation."""
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4.5,
        )
        db_session.add(review)
        db_session.commit()

        expected = f"<Review(id={review.id}, user_id={sample_user.id}, book_id={sample_book.id}, rating=4.5)>"
        assert repr(review) == expected


class TestFavoriteModel:
    """Test cases for Favorite model."""

    def test_create_favorite(self, db_session: Session, sample_user, sample_book):
        """Test creating a favorite."""
        favorite = Favorite(
            user_id=sample_user.id,
            book_id=sample_book.id,
        )
        db_session.add(favorite)
        db_session.commit()

        assert favorite.id is not None
        assert favorite.user_id == sample_user.id
        assert favorite.book_id == sample_book.id
        assert favorite.created_at is not None

    def test_favorite_unique_constraint(
        self, db_session: Session, sample_user, sample_book
    ):
        """Test that user can only favorite a book once."""
        favorite1 = Favorite(
            user_id=sample_user.id,
            book_id=sample_book.id,
        )
        db_session.add(favorite1)
        db_session.commit()

        favorite2 = Favorite(
            user_id=sample_user.id,
            book_id=sample_book.id,
        )
        db_session.add(favorite2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_favorite_relationships(
        self, db_session: Session, sample_user, sample_book
    ):
        """Test favorite relationships with user and book."""
        favorite = Favorite(
            user_id=sample_user.id,
            book_id=sample_book.id,
        )
        db_session.add(favorite)
        db_session.commit()

        # Test relationships
        assert favorite.user == sample_user
        assert favorite.book == sample_book
        assert favorite in sample_user.favorites
        assert favorite in sample_book.favorites

    def test_favorite_repr(self, db_session: Session, sample_user, sample_book):
        """Test favorite string representation."""
        favorite = Favorite(
            user_id=sample_user.id,
            book_id=sample_book.id,
        )
        db_session.add(favorite)
        db_session.commit()

        expected = f"<Favorite(id={favorite.id}, user_id={sample_user.id}, book_id={sample_book.id})>"
        assert repr(favorite) == expected

    def test_cascade_delete_user(self, db_session: Session, sample_user, sample_book):
        """Test that deleting user cascades to favorites."""
        favorite = Favorite(
            user_id=sample_user.id,
            book_id=sample_book.id,
        )
        db_session.add(favorite)
        db_session.commit()

        favorite_id = favorite.id

        # Delete user
        db_session.delete(sample_user)
        db_session.commit()

        # Favorite should be deleted
        deleted_favorite = (
            db_session.query(Favorite).filter(Favorite.id == favorite_id).first()
        )
        assert deleted_favorite is None

    def test_cascade_delete_book(self, db_session: Session, sample_user, sample_book):
        """Test that deleting book cascades to favorites."""
        favorite = Favorite(
            user_id=sample_user.id,
            book_id=sample_book.id,
        )
        db_session.add(favorite)
        db_session.commit()

        favorite_id = favorite.id

        # Delete book
        db_session.delete(sample_book)
        db_session.commit()

        # Favorite should be deleted
        deleted_favorite = (
            db_session.query(Favorite).filter(Favorite.id == favorite_id).first()
        )
        assert deleted_favorite is None
