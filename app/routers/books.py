"""
API routes for book operations.
Provides endpoints for book listing, searching, CRUD operations, and genre management.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.book import (
    BookResponse,
    BookListResponse,
    BookSearchQuery,
    BookSearchResponse,
    BookCreate,
    BookUpdate,
    GenreResponse,
)
from app.services.book_service import BookService, GenreService
from app.core.dependencies import get_current_active_user, get_optional_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=BookListResponse)
async def list_books(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    genre_id: Optional[int] = Query(None, description="Filter by genre ID"),
    min_rating: Optional[float] = Query(
        None, ge=0.0, le=5.0, description="Minimum average rating"
    ),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get paginated list of books with optional filters."""
    try:
        book_service = BookService(db)
        books, total = book_service.get_books(
            page=page, per_page=per_page, genre_id=genre_id, min_rating=min_rating
        )

        total_pages = (total + per_page - 1) // per_page

        return BookListResponse(
            books=[BookResponse.model_validate(book) for book in books],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(f"Error listing books: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search", response_model=BookSearchResponse)
async def search_books(
    query: Optional[str] = Query(None, description="Search query for title or author"),
    genre_id: Optional[int] = Query(None, description="Filter by genre ID"),
    min_rating: Optional[float] = Query(
        None, ge=0.0, le=5.0, description="Minimum average rating"
    ),
    published_year_start: Optional[int] = Query(
        None, ge=1000, description="Earliest publication year"
    ),
    published_year_end: Optional[int] = Query(
        None, le=2030, description="Latest publication year"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Search books with various filters and pagination."""
    try:
        search_params = BookSearchQuery(
            query=query,
            genre_id=genre_id,
            min_rating=min_rating,
            published_year_start=published_year_start,
            published_year_end=published_year_end,
            page=page,
            per_page=per_page,
        )

        book_service = BookService(db)
        books, total = book_service.search_books(search_params)

        total_pages = (total + per_page - 1) // per_page

        # Build filters applied info
        filters_applied = {}
        if query:
            filters_applied["query"] = query
        if genre_id:
            filters_applied["genre_id"] = genre_id
        if min_rating is not None:
            filters_applied["min_rating"] = min_rating
        if published_year_start:
            filters_applied["published_year_start"] = published_year_start
        if published_year_end:
            filters_applied["published_year_end"] = published_year_end

        return BookSearchResponse(
            books=[BookResponse.model_validate(book) for book in books],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            query=query,
            filters_applied=filters_applied,
        )

    except Exception as e:
        logger.error(f"Error searching books: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get a specific book by ID."""
    try:
        book_service = BookService(db)
        book = book_service.get_book_by_id(book_id)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return BookResponse.model_validate(book)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=BookResponse)
async def create_book(
    book_data: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new book (requires authentication)."""
    try:
        book_service = BookService(db)

        # Check if book with same ISBN already exists
        if book_data.isbn:
            existing_book = book_service.get_book_by_isbn(book_data.isbn)
            if existing_book:
                raise HTTPException(
                    status_code=400,
                    detail=f"Book with ISBN {book_data.isbn} already exists",
                )

        book = book_service.create_book(book_data)
        return BookResponse.model_validate(book)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating book: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_data: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing book (requires authentication)."""
    try:
        book_service = BookService(db)
        book = book_service.update_book(book_id, book_data)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return BookResponse.model_validate(book)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{book_id}")
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a book (requires authentication)."""
    try:
        book_service = BookService(db)
        success = book_service.delete_book(book_id)

        if not success:
            raise HTTPException(status_code=404, detail="Book not found")

        return {"message": "Book deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Genre endpoints
genre_router = APIRouter(prefix="/genres", tags=["genres"])


@genre_router.get("/", response_model=list[GenreResponse])
async def list_genres(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get all available genres."""
    try:
        genre_service = GenreService(db)
        genres = genre_service.get_all_genres()

        return [GenreResponse.model_validate(genre) for genre in genres]

    except Exception as e:
        logger.error(f"Error listing genres: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@genre_router.get("/{genre_id}", response_model=GenreResponse)
async def get_genre(
    genre_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get a specific genre by ID."""
    try:
        genre_service = GenreService(db)
        genre = genre_service.get_genre_by_id(genre_id)

        if not genre:
            raise HTTPException(status_code=404, detail="Genre not found")

        return GenreResponse.model_validate(genre)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting genre {genre_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Include genre router in the main books router
router.include_router(genre_router)
