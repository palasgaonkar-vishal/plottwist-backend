import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base, get_db

# app imported for reference but not used directly in tests anymore
from app.models.user import User
from app.models.book import Book, Genre
from app.core.security import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.routers import auth_router, users_router, books_router, reviews_router
    from app.core.config import settings

    # Create a test app without startup events
    test_app = FastAPI(
        title="PlotTwist API Test",
        description="Test version of PlotTwist API",
        version="1.0.0",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    test_app.include_router(auth_router, prefix=settings.API_V1_STR)
    test_app.include_router(users_router, prefix=settings.API_V1_STR)
    test_app.include_router(books_router, prefix=settings.API_V1_STR)
    test_app.include_router(reviews_router, prefix=settings.API_V1_STR)

    # Add basic routes
    @test_app.get("/", tags=["Root"])
    async def root():
        return {"message": "Test PlotTwist API"}

    @test_app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "test": True}

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    # Clear dependency overrides
    test_app.dependency_overrides.clear()


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
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_genre(db_session: Session) -> Genre:
    """Create a sample genre for testing."""
    genre = Genre(name="Test Fiction", description="A test fiction genre")
    db_session.add(genre)
    db_session.commit()
    db_session.refresh(genre)
    return genre


@pytest.fixture
def sample_book(db_session: Session) -> Book:
    """Create a sample book for testing."""
    from app.models.book import Book
    
    book = Book(
        title="The Great Gatsby",
        author="F. Scott Fitzgerald",
        isbn="9780743273565",
        published_year=1925,
        description="A classic American novel set in the Jazz Age."
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


@pytest.fixture
def multiple_users(db_session: Session) -> list[User]:
    """Create multiple users for testing."""
    users = [
        User(
            email="user1@example.com",
            name="User One",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
        ),
        User(
            email="user2@example.com",
            name="User Two",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=False,
        ),
        User(
            email="user3@example.com",
            name="User Three",
            hashed_password=get_password_hash("password123"),
            is_active=False,
            is_verified=True,
        ),
        User(
            email="user4@example.com",
            name="User Four",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
        ),
        User(
            email="user5@example.com",
            name="User Five",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
        ),
    ]

    for user in users:
        db_session.add(user)

    db_session.commit()

    for user in users:
        db_session.refresh(user)

    return users


@pytest.fixture
def multiple_genres(db_session: Session) -> list[Genre]:
    """Create multiple genres for testing."""
    genres = [
        Genre(name="Fiction", description="Fictional stories"),
        Genre(name="Science Fiction", description="Science fiction stories"),
        Genre(name="Mystery", description="Mystery and detective stories"),
        Genre(name="Romance", description="Romance stories"),
        Genre(name="Non-Fiction", description="Non-fictional content"),
    ]

    for genre in genres:
        db_session.add(genre)

    db_session.commit()

    for genre in genres:
        db_session.refresh(genre)

    return genres


@pytest.fixture
def multiple_books(db_session: Session, multiple_genres: list[Genre]) -> list[Book]:
    """Create multiple books for testing."""
    books = [
        Book(
            title="Test Book One",
            author="Author One",
            description="First test book",
            published_year=2022,
            isbn="9781111111111",
            cover_url="https://example.com/cover1.jpg",
            average_rating=4.5,
            total_reviews=10,
        ),
        Book(
            title="Test Book Two",
            author="Author Two",
            description="Second test book",
            published_year=2021,
            isbn="9782222222222",
            cover_url="https://example.com/cover2.jpg",
            average_rating=3.8,
            total_reviews=7,
        ),
        Book(
            title="Test Book Three",
            author="Author Three",
            description="Third test book",
            published_year=2023,
            isbn="9783333333333",
            cover_url="https://example.com/cover3.jpg",
            average_rating=4.2,
            total_reviews=12,
        ),
        Book(
            title="Test Book Four",
            author="Author Four",
            description="Fourth test book",
            published_year=2020,
            isbn="9784444444444",
            cover_url="https://example.com/cover4.jpg",
            average_rating=3.5,
            total_reviews=8,
        ),
        Book(
            title="Test Book Five",
            author="Author Five",
            description="Fifth test book",
            published_year=2024,
            isbn="9785555555555",
            cover_url="https://example.com/cover5.jpg",
            average_rating=4.8,
            total_reviews=15,
        ),
    ]

    for i, book in enumerate(books):
        db_session.add(book)
        db_session.flush()  # Get the book ID

        # Add genre associations (different genres for variety)
        book.genres.append(multiple_genres[i % len(multiple_genres)])
        if i % 2 == 0 and len(multiple_genres) > 1:
            book.genres.append(multiple_genres[(i + 1) % len(multiple_genres)])

    db_session.commit()

    for book in books:
        db_session.refresh(book)

    return books


@pytest.fixture
def auth_headers(sample_user: User) -> dict:
    """Create authentication headers for API testing."""
    from app.core.security import create_access_token
    
    token = create_access_token(subject=str(sample_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def verified_user_headers(client: TestClient, db_session: Session) -> dict:
    """Get authentication headers for a verified user."""
    # Create a verified user for authentication
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
    login_data = {"email": "verified@example.com", "password": "password123"}

    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200

    tokens = response.json()["tokens"]
    access_token = tokens["access_token"]

    return {"Authorization": f"Bearer {access_token}"}
