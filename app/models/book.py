from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


# Association table for many-to-many relationship between books and genres
book_genre_association = Table(
    "book_genres",
    Base.metadata,
    Column(
        "book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "genre_id",
        Integer,
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Genre(Base):
    """
    Genre model for categorizing books.

    Attributes:
        id: Primary key
        name: Genre name (e.g., "Fiction", "Mystery", "Romance")
        description: Optional description of the genre
        created_at: Genre creation timestamp
    """

    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    books = relationship(
        "Book", secondary=book_genre_association, back_populates="genres"
    )

    def __repr__(self):
        return f"<Genre(id={self.id}, name='{self.name}')>"


class Book(Base):
    """
    Book model for storing book information.

    Attributes:
        id: Primary key
        title: Book title
        author: Book author(s)
        description: Book description/summary
        published_year: Year the book was published
        isbn: International Standard Book Number (optional)
        cover_url: URL to book cover image
        average_rating: Calculated average rating from reviews
        total_reviews: Total number of reviews
        created_at: Book creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    published_year = Column(Integer, nullable=True, index=True)
    isbn = Column(String(13), nullable=True, unique=True, index=True)
    cover_url = Column(String(500), nullable=True)
    average_rating = Column(Float, default=0.0, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    genres = relationship(
        "Genre", secondary=book_genre_association, back_populates="books"
    )
    reviews = relationship(
        "Review", back_populates="book", cascade="all, delete-orphan"
    )
    favorites = relationship(
        "Favorite", back_populates="book", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"


# For backward compatibility and explicit relationship reference
class BookGenre(Base):
    """
    Explicit BookGenre model for any additional attributes on the relationship.
    Currently just maps to the association table.
    """

    __tablename__ = "book_genres_explicit"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(
        Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False
    )
    genre_id = Column(
        Integer, ForeignKey("genres.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<BookGenre(book_id={self.book_id}, genre_id={self.genre_id})>"
