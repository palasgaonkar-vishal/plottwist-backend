import logging
from typing import List
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
            {"name": "Mystery", "description": "Stories involving puzzles or crimes to solve"},
            {"name": "Romance", "description": "Stories focused on love relationships"},
            {"name": "Science Fiction", "description": "Stories set in the future or involving science and technology"},
            {"name": "Fantasy", "description": "Stories involving magical or supernatural elements"},
            {"name": "Thriller", "description": "Fast-paced stories designed to keep readers in suspense"},
            {"name": "Horror", "description": "Stories intended to frighten, unsettle, or create suspense"},
            {"name": "Biography", "description": "Life stories of real people"},
            {"name": "History", "description": "Books about past events and civilizations"},
            {"name": "Self-Help", "description": "Books designed to help readers improve their lives"},
            {"name": "Comedy", "description": "Humorous and entertaining stories"},
            {"name": "Drama", "description": "Serious stories dealing with emotional themes"},
            {"name": "Adventure", "description": "Stories with exciting journeys or quests"},
            {"name": "Young Adult", "description": "Books targeted at teenage readers"},
        ]
        
        genres = []
        for data in genre_data:
            # Check if genre already exists
            existing_genre = self.db.query(Genre).filter(Genre.name == data["name"]).first()
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
                "password": "reading123",
                "is_verified": False,
            },
        ]
        
        users = []
        for data in user_data:
            # Check if user already exists
            existing_user = self.db.query(User).filter(User.email == data["email"]).first()
            if not existing_user:
                user = User(
                    email=data["email"],
                    name=data["name"],
                    hashed_password=get_password_hash(data["password"]),
                    is_active=True,
                    is_verified=data["is_verified"],
                )
                self.db.add(user)
                users.append(user)
            else:
                users.append(existing_user)
        
        self.db.commit()
        logger.info(f"Seeded {len([u for u in users if u.id is None])} new users")
        return users

    def seed_books(self) -> List[Book]:
        """Seed sample books."""
        logger.info("Seeding sample books...")
        
        book_data = [
            {
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "description": "A classic American novel set in the Jazz Age",
                "published_year": 1925,
                "isbn": "9780743273565",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780743273565-L.jpg",
                "genres": ["Fiction", "Drama"],
            },
            {
                "title": "To Kill a Mockingbird",
                "author": "Harper Lee",
                "description": "A novel about racial injustice and childhood in the American South",
                "published_year": 1960,
                "isbn": "9780061120084",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780061120084-L.jpg",
                "genres": ["Fiction", "Drama"],
            },
            {
                "title": "1984",
                "author": "George Orwell",
                "description": "A dystopian social science fiction novel and cautionary tale",
                "published_year": 1949,
                "isbn": "9780451524935",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780451524935-L.jpg",
                "genres": ["Science Fiction", "Fiction"],
            },
            {
                "title": "Pride and Prejudice",
                "author": "Jane Austen",
                "description": "A romantic novel of manners",
                "published_year": 1813,
                "isbn": "9780141439518",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780141439518-L.jpg",
                "genres": ["Romance", "Fiction"],
            },
            {
                "title": "The Catcher in the Rye",
                "author": "J.D. Salinger",
                "description": "A controversial novel about teenage rebellion and alienation",
                "published_year": 1951,
                "isbn": "9780316769174",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780316769174-L.jpg",
                "genres": ["Fiction", "Young Adult"],
            },
            {
                "title": "Harry Potter and the Philosopher's Stone",
                "author": "J.K. Rowling",
                "description": "The first book in the Harry Potter series",
                "published_year": 1997,
                "isbn": "9780747532699",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780747532699-L.jpg",
                "genres": ["Fantasy", "Young Adult", "Adventure"],
            },
            {
                "title": "The Lord of the Rings",
                "author": "J.R.R. Tolkien",
                "description": "An epic high fantasy novel",
                "published_year": 1954,
                "isbn": "9780544003415",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780544003415-L.jpg",
                "genres": ["Fantasy", "Adventure", "Fiction"],
            },
            {
                "title": "The Da Vinci Code",
                "author": "Dan Brown",
                "description": "A mystery thriller novel",
                "published_year": 2003,
                "isbn": "9780307474278",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780307474278-L.jpg",
                "genres": ["Mystery", "Thriller", "Adventure"],
            },
            {
                "title": "The Hunger Games",
                "author": "Suzanne Collins",
                "description": "A dystopian young adult novel",
                "published_year": 2008,
                "isbn": "9780439023528",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780439023528-L.jpg",
                "genres": ["Science Fiction", "Young Adult", "Adventure"],
            },
            {
                "title": "The Girl with the Dragon Tattoo",
                "author": "Stieg Larsson",
                "description": "A psychological thriller novel",
                "published_year": 2005,
                "isbn": "9780307269751",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780307269751-L.jpg",
                "genres": ["Mystery", "Thriller", "Fiction"],
            },
        ]
        
        books = []
        for data in book_data:
            # Check if book already exists
            existing_book = self.db.query(Book).filter(Book.isbn == data["isbn"]).first()
            if not existing_book:
                book = Book(
                    title=data["title"],
                    author=data["author"],
                    description=data["description"],
                    published_year=data["published_year"],
                    isbn=data["isbn"],
                    cover_url=data["cover_url"],
                    average_rating=0.0,
                    total_reviews=0,
                )
                
                # Add genres
                for genre_name in data["genres"]:
                    genre = self.db.query(Genre).filter(Genre.name == genre_name).first()
                    if genre:
                        book.genres.append(genre)
                
                self.db.add(book)
                books.append(book)
            else:
                books.append(existing_book)
        
        self.db.commit()
        logger.info(f"Seeded {len([b for b in books if b.id is None])} new books")
        return books

    def seed_reviews(self) -> List[Review]:
        """Seed sample reviews."""
        logger.info("Seeding sample reviews...")
        
        # Get users and books
        users = self.db.query(User).all()
        books = self.db.query(Book).all()
        
        if not users or not books:
            logger.warning("No users or books found, skipping review seeding")
            return []
        
        reviews = []
        review_data = [
            {"user_idx": 0, "book_idx": 0, "rating": 4.5, "title": "A timeless classic", "content": "Beautiful prose and compelling characters."},
            {"user_idx": 1, "book_idx": 1, "rating": 5.0, "title": "Powerful and moving", "content": "This book changed my perspective on many things."},
            {"user_idx": 2, "book_idx": 2, "rating": 4.0, "title": "Thought-provoking", "content": "Orwell's vision feels more relevant than ever."},
            {"user_idx": 3, "book_idx": 3, "rating": 4.5, "title": "Witty and romantic", "content": "Austen's wit and social commentary are brilliant."},
            {"user_idx": 0, "book_idx": 4, "rating": 3.5, "title": "Interesting but dated", "content": "Good insight into teenage psychology of the era."},
            {"user_idx": 1, "book_idx": 5, "rating": 5.0, "title": "Magical beginning", "content": "Started an amazing series that captivated millions."},
            {"user_idx": 2, "book_idx": 6, "rating": 4.8, "title": "Epic fantasy masterpiece", "content": "Tolkien created an entire world with incredible detail."},
            {"user_idx": 3, "book_idx": 7, "rating": 4.2, "title": "Page-turner", "content": "Couldn't put it down, great mystery and pacing."},
            {"user_idx": 0, "book_idx": 8, "rating": 4.3, "title": "Gripping dystopia", "content": "Collins created a compelling and brutal world."},
            {"user_idx": 1, "book_idx": 9, "rating": 4.1, "title": "Dark and compelling", "content": "Great thriller with complex characters."},
            {"user_idx": 2, "book_idx": 0, "rating": 4.0, "title": "Literary excellence", "content": "Fitzgerald's prose is simply beautiful."},
            {"user_idx": 3, "book_idx": 1, "rating": 4.7, "title": "Important read", "content": "Every person should read this book."},
            {"user_idx": 4, "book_idx": 2, "rating": 4.2, "title": "Chilling prediction", "content": "Scary how accurate Orwell's predictions were."},
            {"user_idx": 4, "book_idx": 5, "rating": 4.9, "title": "Perfect for all ages", "content": "A book that adults and children can both enjoy."},
            {"user_idx": 4, "book_idx": 6, "rating": 5.0, "title": "The ultimate fantasy", "content": "Set the standard for all fantasy literature."},
        ]
        
        for data in review_data:
            if data["user_idx"] < len(users) and data["book_idx"] < len(books):
                user = users[data["user_idx"]]
                book = books[data["book_idx"]]
                
                # Check if review already exists
                existing_review = self.db.query(Review).filter(
                    Review.user_id == user.id,
                    Review.book_id == book.id
                ).first()
                
                if not existing_review:
                    review = Review(
                        user_id=user.id,
                        book_id=book.id,
                        rating=data["rating"],
                        title=data["title"],
                        content=data["content"],
                    )
                    self.db.add(review)
                    reviews.append(review)
        
        self.db.commit()
        
        # Update book statistics
        self._update_book_statistics()
        
        logger.info(f"Seeded {len(reviews)} new reviews")
        return reviews

    def seed_favorites(self) -> List[Favorite]:
        """Seed sample favorites."""
        logger.info("Seeding sample favorites...")
        
        # Get users and books
        users = self.db.query(User).all()
        books = self.db.query(Book).all()
        
        if not users or not books:
            logger.warning("No users or books found, skipping favorites seeding")
            return []
        
        favorites = []
        favorite_data = [
            {"user_idx": 0, "book_idx": 0},
            {"user_idx": 0, "book_idx": 5},
            {"user_idx": 1, "book_idx": 1},
            {"user_idx": 1, "book_idx": 6},
            {"user_idx": 2, "book_idx": 2},
            {"user_idx": 2, "book_idx": 7},
            {"user_idx": 3, "book_idx": 3},
            {"user_idx": 3, "book_idx": 8},
            {"user_idx": 4, "book_idx": 5},
            {"user_idx": 4, "book_idx": 6},
        ]
        
        for data in favorite_data:
            if data["user_idx"] < len(users) and data["book_idx"] < len(books):
                user = users[data["user_idx"]]
                book = books[data["book_idx"]]
                
                # Check if favorite already exists
                existing_favorite = self.db.query(Favorite).filter(
                    Favorite.user_id == user.id,
                    Favorite.book_id == book.id
                ).first()
                
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
                book.average_rating = sum(review.rating for review in reviews) / len(reviews)
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