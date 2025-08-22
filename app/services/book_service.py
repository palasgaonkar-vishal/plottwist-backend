"""
Service layer for book operations.
Handles CRUD operations, search, pagination, and genre management for books.
"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.book import Book, Genre
from app.schemas.book import BookCreate, BookUpdate, BookSearchQuery

logger = logging.getLogger(__name__)


class BookService:
    """Service class for book operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """Get a book by its ID with genres loaded."""
        return (
            self.db.query(Book)
            .options(joinedload(Book.genres))
            .filter(Book.id == book_id)
            .first()
        )

    def get_book_by_isbn(self, isbn: str) -> Optional[Book]:
        """Get a book by its ISBN."""
        return (
            self.db.query(Book)
            .options(joinedload(Book.genres))
            .filter(Book.isbn == isbn)
            .first()
        )

    def get_books(
        self,
        page: int = 1,
        per_page: int = 10,
        genre_id: Optional[int] = None,
        min_rating: Optional[float] = None,
    ) -> Tuple[List[Book], int]:
        """Get paginated list of books with optional filters."""
        query = self.db.query(Book).options(joinedload(Book.genres))

        # Apply filters
        filters = []
        if genre_id:
            query = query.join(Book.genres).filter(Genre.id == genre_id)

        if min_rating is not None:
            filters.append(Book.average_rating >= min_rating)

        if filters:
            query = query.filter(and_(*filters))

        # Order by average rating and total reviews
        query = query.order_by(Book.average_rating.desc(), Book.total_reviews.desc())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        books = query.offset(offset).limit(per_page).all()

        return books, total

    def search_books(self, search_params: BookSearchQuery) -> Tuple[List[Book], int]:
        """Search books with various filters and pagination."""
        query = self.db.query(Book).options(joinedload(Book.genres))

        filters = []

        # Text search in title and author
        if search_params.query:
            search_term = f"%{search_params.query}%"
            filters.append(
                or_(Book.title.ilike(search_term), Book.author.ilike(search_term))
            )

        # Genre filter
        if search_params.genre_id:
            query = query.join(Book.genres).filter(Genre.id == search_params.genre_id)

        # Rating filter
        if search_params.min_rating is not None:
            filters.append(Book.average_rating >= search_params.min_rating)

        # Publication year filters
        if search_params.published_year_start:
            filters.append(Book.published_year >= search_params.published_year_start)

        if search_params.published_year_end:
            filters.append(Book.published_year <= search_params.published_year_end)

        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))

        # Order by relevance (rating and reviews)
        query = query.order_by(Book.average_rating.desc(), Book.total_reviews.desc())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (search_params.page - 1) * search_params.per_page
        books = query.offset(offset).limit(search_params.per_page).all()

        return books, total

    def create_book(self, book_data: BookCreate) -> Book:
        """Create a new book with genre associations."""
        # Create book without genres first
        book_dict = book_data.model_dump(exclude={"genre_ids"})
        book_dict.update(
            {
                "average_rating": 0.0,
                "total_reviews": 0,
            }
        )

        book = Book(**book_dict)
        self.db.add(book)
        self.db.flush()  # Get the book ID

        # Add genre associations
        if book_data.genre_ids:
            genres = (
                self.db.query(Genre).filter(Genre.id.in_(book_data.genre_ids)).all()
            )
            for genre in genres:
                book.genres.append(genre)

        self.db.commit()
        self.db.refresh(book)

        logger.info(f"Created book: {book.title} (ID: {book.id})")
        return book

    def update_book(self, book_id: int, book_data: BookUpdate) -> Optional[Book]:
        """Update an existing book."""
        book = self.get_book_by_id(book_id)
        if not book:
            return None

        # Update basic fields
        update_data = book_data.model_dump(exclude_unset=True, exclude={"genre_ids"})
        for field, value in update_data.items():
            setattr(book, field, value)

        # Update genre associations if provided
        if book_data.genre_ids is not None:
            # Clear existing associations
            book.genres.clear()

            # Add new associations
            if book_data.genre_ids:
                genres = (
                    self.db.query(Genre).filter(Genre.id.in_(book_data.genre_ids)).all()
                )
                for genre in genres:
                    book.genres.append(genre)

        self.db.commit()
        self.db.refresh(book)

        logger.info(f"Updated book: {book.title} (ID: {book.id})")
        return book

    def delete_book(self, book_id: int) -> bool:
        """Delete a book by ID."""
        book = self.get_book_by_id(book_id)
        if not book:
            return False

        self.db.delete(book)
        self.db.commit()

        logger.info(f"Deleted book: {book.title} (ID: {book.id})")
        return True

    def update_book_statistics(self, book_id: int) -> Optional[Book]:
        """Update book's average rating and review count."""
        from app.models.review import Review

        book = self.get_book_by_id(book_id)
        if not book:
            return None

        # Calculate statistics
        result = (
            self.db.query(
                func.count(Review.id).label("total_reviews"),
                func.avg(Review.rating).label("average_rating"),
            )
            .filter(Review.book_id == book_id)
            .first()
        )

        book.total_reviews = result.total_reviews or 0
        book.average_rating = float(result.average_rating or 0.0)

        self.db.commit()
        self.db.refresh(book)

        logger.info(
            f"Updated statistics for book: {book.title} - Rating: {book.average_rating}, Reviews: {book.total_reviews}"
        )
        return book


class GenreService:
    """Service class for genre operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_genres(self) -> List[Genre]:
        """Get all available genres."""
        return self.db.query(Genre).order_by(Genre.name).all()

    def get_genre_by_id(self, genre_id: int) -> Optional[Genre]:
        """Get a genre by its ID."""
        return self.db.query(Genre).filter(Genre.id == genre_id).first()

    def get_genre_by_name(self, name: str) -> Optional[Genre]:
        """Get a genre by its name."""
        return self.db.query(Genre).filter(Genre.name == name).first()

    def create_genre(self, name: str, description: Optional[str] = None) -> Genre:
        """Create a new genre."""
        genre = Genre(name=name, description=description)
        self.db.add(genre)
        self.db.commit()
        self.db.refresh(genre)

        logger.info(f"Created genre: {genre.name} (ID: {genre.id})")
        return genre

    def update_genre(
        self,
        genre_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Genre]:
        """Update a genre."""
        genre = self.get_genre_by_id(genre_id)
        if not genre:
            return None

        if name is not None:
            genre.name = name
        if description is not None:
            genre.description = description

        self.db.commit()
        self.db.refresh(genre)

        logger.info(f"Updated genre: {genre.name} (ID: {genre.id})")
        return genre

    def delete_genre(self, genre_id: int) -> bool:
        """Delete a genre."""
        genre = self.get_genre_by_id(genre_id)
        if not genre:
            return False

        self.db.delete(genre)
        self.db.commit()

        logger.info(f"Deleted genre: {genre.name} (ID: {genre.id})")
        return True
