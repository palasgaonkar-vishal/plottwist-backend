import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.book import Book, Genre
from app.core.security import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a test database session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_inactive_user(db_session: Session) -> User:
    """Create a sample inactive user for testing."""
    user = User(
        email="inactive@example.com",
        name="Inactive User",
        hashed_password=get_password_hash("password123"),
        is_active=False,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_genre(db_session: Session) -> Genre:
    """Create a sample genre for testing."""
    genre = Genre(
        name="Fiction",
        description="Imaginative or invented stories",
    )
    db_session.add(genre)
    db_session.commit()
    db_session.refresh(genre)
    return genre


@pytest.fixture
def sample_book(db_session: Session, sample_genre: Genre) -> Book:
    """Create a sample book for testing."""
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
    book.genres.append(sample_genre)
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


@pytest.fixture
def multiple_users(db_session: Session) -> list[User]:
    """Create multiple sample users for testing."""
    users = []
    for i in range(3):
        user = User(
            email=f"user{i}@example.com",
            name=f"User {i}",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=i % 2 == 0,  # Alternate verified status
        )
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    
    # Refresh all users
    for user in users:
        db_session.refresh(user)
    
    return users


@pytest.fixture
def multiple_genres(db_session: Session) -> list[Genre]:
    """Create multiple sample genres for testing."""
    genre_data = [
        {"name": "Fiction", "description": "Imaginative stories"},
        {"name": "Mystery", "description": "Puzzles and crimes"},
        {"name": "Romance", "description": "Love stories"},
    ]
    
    genres = []
    for data in genre_data:
        genre = Genre(**data)
        db_session.add(genre)
        genres.append(genre)
    
    db_session.commit()
    
    # Refresh all genres
    for genre in genres:
        db_session.refresh(genre)
    
    return genres


@pytest.fixture
def multiple_books(db_session: Session, multiple_genres: list[Genre]) -> list[Book]:
    """Create multiple sample books for testing."""
    book_data = [
        {
            "title": "The Great Test",
            "author": "Test Author 1",
            "description": "A great test book",
            "published_year": 2023,
            "isbn": "9781111111111",
            "genres": [multiple_genres[0], multiple_genres[1]],
        },
        {
            "title": "Mystery of Testing",
            "author": "Test Author 2",
            "description": "A mysterious test book",
            "published_year": 2022,
            "isbn": "9782222222222",
            "genres": [multiple_genres[1]],
        },
        {
            "title": "Love in Testing",
            "author": "Test Author 3",
            "description": "A romantic test book",
            "published_year": 2021,
            "isbn": "9783333333333",
            "genres": [multiple_genres[2]],
        },
    ]
    
    books = []
    for data in book_data:
        book = Book(
            title=data["title"],
            author=data["author"],
            description=data["description"],
            published_year=data["published_year"],
            isbn=data["isbn"],
            average_rating=0.0,
            total_reviews=0,
        )
        book.genres.extend(data["genres"])
        db_session.add(book)
        books.append(book)
    
    db_session.commit()
    
    # Refresh all books
    for book in books:
        db_session.refresh(book)
    
    return books


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Create authentication headers for a test user."""
    # Register a user
    user_data = {
        "email": "auth@example.com",
        "password": "password123",
        "name": "Auth User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    tokens = response.json()["tokens"]
    access_token = tokens["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def verified_user_headers(client: TestClient, db_session: Session) -> dict:
    """Create authentication headers for a verified test user."""
    # Create a verified user directly in database
    user = User(
        email="verified@example.com",
        name="Verified User",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Login to get tokens
    login_data = {
        "email": "verified@example.com",
        "password": "password123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    tokens = response.json()["tokens"]
    access_token = tokens["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"} 