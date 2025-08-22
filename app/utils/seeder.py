import logging
import requests
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.book import Book, Genre, book_genre_association
from app.models.review import Review
from app.models.favorite import Favorite
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Utility class for seeding the database with initial data."""

    def __init__(self, db: Session):
        self.db = db

    def seed_all(self) -> None:
        """Seed the database with all initial data."""
        logger.info("Starting database seeding...")

        self.seed_genres()
        self.seed_users()
        self.seed_books()
        self.seed_reviews()
        self.seed_favorites()

        logger.info("Database seeding completed!")

    def seed_genres(self) -> List[Genre]:
        """Seed standard book genres."""
        logger.info("Seeding genres...")

        genre_data = [
            {"name": "Fiction", "description": "Imaginative or invented stories"},
            {"name": "Non-Fiction", "description": "Factual and informative content"},
            {
                "name": "Mystery",
                "description": "Stories involving puzzles or crimes to solve",
            },
            {"name": "Romance", "description": "Stories focused on love relationships"},
            {
                "name": "Science Fiction",
                "description": "Stories set in the future or involving science and technology",
            },
            {
                "name": "Fantasy",
                "description": "Stories involving magical or supernatural elements",
            },
            {
                "name": "Thriller",
                "description": "Fast-paced stories designed to keep readers in suspense",
            },
            {
                "name": "Horror",
                "description": "Stories intended to frighten, unsettle, or create suspense",
            },
            {"name": "Biography", "description": "Life stories of real people"},
            {
                "name": "History",
                "description": "Books about past events and civilizations",
            },
            {
                "name": "Self-Help",
                "description": "Books designed to help readers improve their lives",
            },
            {"name": "Comedy", "description": "Humorous and entertaining stories"},
            {
                "name": "Drama",
                "description": "Serious stories dealing with emotional themes",
            },
            {
                "name": "Adventure",
                "description": "Stories with exciting journeys or quests",
            },
            {"name": "Young Adult", "description": "Books targeted at teenage readers"},
        ]

        genres = []
        for data in genre_data:
            # Check if genre already exists
            existing_genre = (
                self.db.query(Genre).filter(Genre.name == data["name"]).first()
            )
            if not existing_genre:
                genre = Genre(**data)
                self.db.add(genre)
                genres.append(genre)
            else:
                genres.append(existing_genre)

        self.db.commit()
        logger.info(f"Seeded {len([g for g in genres if g.id is None])} new genres")
        return genres

    def seed_users(self) -> List[User]:
        """Seed test users."""
        logger.info("Seeding test users...")

        user_data = [
            {
                "email": "admin@plottwist.com",
                "name": "Admin User",
                "password": "admin123456",
                "is_verified": True,
            },
            {
                "email": "john.doe@example.com",
                "name": "John Doe",
                "password": "password123",
                "is_verified": True,
            },
            {
                "email": "jane.smith@example.com",
                "name": "Jane Smith",
                "password": "password123",
                "is_verified": False,
            },
            {
                "email": "book.lover@example.com",
                "name": "Book Lover",
                "password": "ilovebooks123",
                "is_verified": True,
            },
            {
                "email": "reader.one@example.com",
                "name": "Reader One",
                "password": "readmore123",
                "is_verified": True,
            },
        ]

        users = []
        for data in user_data:
            # Check if user already exists
            existing_user = (
                self.db.query(User).filter(User.email == data["email"]).first()
            )
            if not existing_user:
                password = data.pop("password")
                hashed_password = get_password_hash(password)
                user = User(hashed_password=hashed_password, **data)
                self.db.add(user)
                users.append(user)
            else:
                users.append(existing_user)

        self.db.commit()
        logger.info(f"Seeded {len([u for u in users if u.id is None])} new users")
        return users

    def seed_books(self, target_count: int = 500) -> List[Book]:
        """Seed books from Open Library API."""
        logger.info(f"Seeding {target_count} books from Open Library...")

        # Check if we already have enough books
        existing_count = self.db.query(Book).count()
        if existing_count >= target_count:
            logger.info(
                f"Database already has {existing_count} books (target: {target_count})"
            )
            return self.db.query(Book).all()

        # Get all genres to assign to books
        genres = self.db.query(Genre).all()
        genre_map = {genre.name: genre for genre in genres}

        books = []
        seeded_count = 0

        # Popular subjects to search for diverse books
        subjects = [
            "fiction",
            "science_fiction",
            "fantasy",
            "mystery",
            "romance",
            "thriller",
            "biography",
            "history",
            "science",
            "philosophy",
            "adventure",
            "young_adult",
            "horror",
            "comedy",
            "drama",
            "self_help",
            "business",
            "psychology",
            "nature",
            "technology",
        ]

        for subject in subjects:
            if seeded_count >= target_count:
                break

            logger.info(f"Fetching books for subject: {subject}")
            subject_books = self._fetch_books_by_subject(subject, limit=30)

            for book_data in subject_books:
                if seeded_count >= target_count:
                    break

                # Check if book already exists
                if book_data.get("isbn"):
                    existing_book = (
                        self.db.query(Book)
                        .filter(Book.isbn == book_data["isbn"])
                        .first()
                    )
                    if existing_book:
                        continue

                # Create book
                try:
                    book_genres = book_data.pop("genres", [])
                    book = Book(**book_data)
                    self.db.add(book)
                    self.db.flush()  # Get the book ID

                    # Add genre associations
                    for genre_name in book_genres:
                        if genre_name in genre_map:
                            genre = genre_map[genre_name]
                            book.genres.append(genre)

                    books.append(book)
                    seeded_count += 1

                    if seeded_count % 50 == 0:
                        logger.info(f"Seeded {seeded_count} books so far...")

                except Exception as e:
                    logger.warning(f"Failed to create book: {e}")
                    continue

            # Be respectful to the API
            time.sleep(0.5)

        self.db.commit()
        logger.info(f"Successfully seeded {seeded_count} new books")
        return books

    def _fetch_books_by_subject(
        self, subject: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Fetch books from Open Library by subject."""
        try:
            # Search for books by subject
            search_url = "https://openlibrary.org/search.json"
            params = {
                "subject": subject,
                "limit": limit,
                "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,publisher",
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            books = []
            for doc in data.get("docs", []):
                book_data = self._parse_open_library_book(doc, subject)
                if book_data:
                    books.append(book_data)

            return books

        except Exception as e:
            logger.error(f"Failed to fetch books for subject {subject}: {e}")
            return []

    def _parse_open_library_book(
        self, doc: Dict[str, Any], primary_subject: str
    ) -> Optional[Dict[str, Any]]:
        """Parse Open Library book data into our format."""
        try:
            # Extract basic information
            title = doc.get("title", "").strip()
            if not title:
                return None

            # Get author (take first author if multiple)
            authors = doc.get("author_name", [])
            author = authors[0] if authors else "Unknown Author"

            # Get publication year
            published_year = doc.get("first_publish_year")
            if not published_year:
                return None

            # Get ISBN (prefer ISBN-13, fallback to ISBN-10)
            isbns = doc.get("isbn", [])
            isbn = None
            for isbn_candidate in isbns:
                if len(isbn_candidate) == 13:  # ISBN-13
                    isbn = isbn_candidate
                    break
            if not isbn and isbns:
                isbn = isbns[0]  # Take first available ISBN

            # Generate cover URL
            cover_url = None
            if doc.get("cover_i"):
                cover_url = (
                    f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
                )
            elif isbn:
                cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

            # Map subjects to our genres
            subjects = doc.get("subject", [])
            genres = self._map_subjects_to_genres(subjects, primary_subject)

            # Create description based on subjects and metadata
            description = self._generate_description(
                title, author, subjects, doc.get("publisher", [])
            )

            return {
                "title": title[:255],  # Ensure we don't exceed database limits
                "author": author[:255],
                "description": description[:1000] if description else None,
                "published_year": published_year,
                "isbn": isbn,
                "cover_url": cover_url,
                "genres": genres,
                "average_rating": 0.0,
                "total_reviews": 0,
            }

        except Exception as e:
            logger.warning(f"Failed to parse book data: {e}")
            return None

    def _map_subjects_to_genres(
        self, subjects: List[str], primary_subject: str
    ) -> List[str]:
        """Map Open Library subjects to our genre categories."""
        # Subject to genre mapping
        subject_mapping = {
            "fiction": "Fiction",
            "science_fiction": "Science Fiction",
            "fantasy": "Fantasy",
            "mystery": "Mystery",
            "romance": "Romance",
            "thriller": "Thriller",
            "horror": "Horror",
            "biography": "Biography",
            "history": "History",
            "adventure": "Adventure",
            "young_adult": "Young Adult",
            "comedy": "Comedy",
            "drama": "Drama",
            "self_help": "Self-Help",
            "business": "Non-Fiction",
            "psychology": "Non-Fiction",
            "science": "Non-Fiction",
            "philosophy": "Non-Fiction",
            "nature": "Non-Fiction",
            "technology": "Non-Fiction",
        }

        genres = []

        # Add primary genre based on search subject
        if primary_subject in subject_mapping:
            genres.append(subject_mapping[primary_subject])

        # Add additional genres based on book subjects
        for subject in subjects[:3]:  # Limit to avoid too many genres
            subject_lower = subject.lower()
            for key, genre in subject_mapping.items():
                if key in subject_lower and genre not in genres:
                    genres.append(genre)
                    break

        # Ensure we have at least one genre
        if not genres:
            if "non" in primary_subject.lower() or primary_subject in [
                "science",
                "history",
                "biography",
            ]:
                genres.append("Non-Fiction")
            else:
                genres.append("Fiction")

        return genres[:3]  # Limit to max 3 genres per book

    def _generate_description(
        self, title: str, author: str, subjects: List[str], publishers: List[str]
    ) -> str:
        """Generate a description for the book based on available metadata."""
        description_parts = []

        # Add subjects as description elements
        if subjects:
            subject_text = ", ".join(subjects[:3])
            description_parts.append(f"A work covering {subject_text}")

        # Add publisher info if available
        if publishers:
            publisher = publishers[0]
            description_parts.append(f"Published by {publisher}")

        # Generic description if no specific info
        if not description_parts:
            description_parts.append(f"A book by {author}")

        return ". ".join(description_parts) + "."

    def seed_reviews(self) -> List[Review]:
        """Seed sample reviews."""
        logger.info("Seeding sample reviews...")

        # Get sample users and books
        users = self.db.query(User).limit(5).all()
        books = self.db.query(Book).limit(15).all()

        if not users or not books:
            logger.warning("No users or books found, skipping review seeding")
            return []

        review_data = [
            {
                "rating": 5,
                "title": "Amazing book!",
                "content": "I couldn't put this book down. Highly recommended!",
            },
            {
                "rating": 4,
                "title": "Great read",
                "content": "Really enjoyed this one. Well written and engaging.",
            },
            {
                "rating": 3,
                "title": "Decent book",
                "content": "It was okay, but not my favorite. Worth reading once.",
            },
            {
                "rating": 5,
                "title": "Loved it",
                "content": "One of the best books I've read this year. Fantastic!",
            },
            {
                "rating": 2,
                "title": "Not for me",
                "content": "Couldn't get into this one. Maybe others will enjoy it more.",
            },
            {
                "rating": 4,
                "title": "Solid choice",
                "content": "Good story and character development. Recommend it.",
            },
            {
                "rating": 5,
                "title": "Masterpiece",
                "content": "This is why I love reading. Absolutely brilliant work.",
            },
            {
                "rating": 3,
                "title": "Average",
                "content": "Nothing special but not bad either. Middle of the road.",
            },
            {
                "rating": 4,
                "title": "Enjoyable",
                "content": "Had a good time reading this. Nice plot and pacing.",
            },
            {
                "rating": 1,
                "title": "Disappointing",
                "content": "Expected more based on the reviews. Didn't work for me.",
            },
            {
                "rating": 5,
                "title": "Fantastic",
                "content": "Everything about this book is perfect. Love the author's style.",
            },
            {
                "rating": 4,
                "title": "Recommended",
                "content": "Definitely worth your time. Good storytelling and characters.",
            },
            {
                "rating": 3,
                "title": "Mixed feelings",
                "content": "Some parts were great, others not so much. Overall decent.",
            },
            {
                "rating": 5,
                "title": "Perfect",
                "content": "Could not ask for a better book. This is pure excellence.",
            },
            {
                "rating": 2,
                "title": "Struggled",
                "content": "Had to force myself to finish it. Not my cup of tea.",
            },
        ]

        reviews = []
        review_index = 0

        # Create reviews ensuring each book gets at least one review
        for i, book in enumerate(books):
            user = users[i % len(users)]
            review_info = review_data[review_index % len(review_data)]

            # Check if review already exists
            existing_review = (
                self.db.query(Review)
                .filter(Review.user_id == user.id, Review.book_id == book.id)
                .first()
            )

            if not existing_review:
                review = Review(
                    user_id=user.id,
                    book_id=book.id,
                    rating=review_info["rating"],
                    title=review_info["title"],
                    content=review_info["content"],
                )
                self.db.add(review)
                reviews.append(review)

            review_index += 1

        self.db.commit()

        # Update book statistics
        self._update_book_statistics()

        logger.info(f"Seeded {len(reviews)} new reviews")
        return reviews

    def seed_favorites(self) -> List[Favorite]:
        """Seed sample favorites."""
        logger.info("Seeding sample favorites...")

        # Get sample users and books
        users = self.db.query(User).limit(5).all()
        books = self.db.query(Book).limit(10).all()

        if not users or not books:
            logger.warning("No users or books found, skipping favorites seeding")
            return []

        favorites = []

        # Each user gets 2-3 favorite books
        for user in users:
            user_books = books[:3] if user.id % 2 == 0 else books[2:5]

            for book in user_books:
                # Check if favorite already exists
                existing_favorite = (
                    self.db.query(Favorite)
                    .filter(Favorite.user_id == user.id, Favorite.book_id == book.id)
                    .first()
                )

                if not existing_favorite:
                    favorite = Favorite(
                        user_id=user.id,
                        book_id=book.id,
                    )
                    self.db.add(favorite)
                    favorites.append(favorite)

        self.db.commit()
        logger.info(f"Seeded {len(favorites)} new favorites")
        return favorites

    def _update_book_statistics(self) -> None:
        """Update book average ratings and review counts."""
        logger.info("Updating book statistics...")

        books = self.db.query(Book).all()
        for book in books:
            reviews = self.db.query(Review).filter(Review.book_id == book.id).all()

            if reviews:
                book.total_reviews = len(reviews)
                book.average_rating = sum(review.rating for review in reviews) / len(
                    reviews
                )
            else:
                book.total_reviews = 0
                book.average_rating = 0.0

        self.db.commit()
        logger.info("Book statistics updated")

    def clear_all_data(self) -> None:
        """Clear all data from the database (use with caution!)."""
        logger.warning("Clearing all database data...")

        # Delete in reverse order of dependencies
        self.db.query(Favorite).delete()
        self.db.query(Review).delete()
        self.db.execute(book_genre_association.delete())
        self.db.query(Book).delete()
        self.db.query(Genre).delete()
        self.db.query(User).delete()

        self.db.commit()
        logger.info("All database data cleared")
