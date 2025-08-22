# PlotTwist Backend

A FastAPI-based backend for the PlotTwist book review platform with JWT authentication, database models, and comprehensive testing.

## 🚀 Features Implemented

### ✅ Task 001: Project Setup and Infrastructure
- FastAPI application with CORS middleware
- Health check and documentation endpoints
- Docker configuration for development
- Testing framework with pytest
- Code quality tools (pytest configuration)

### ✅ Task 002: Database Models and Authentication
- **Database Models**: User, Book, Genre, Review, Favorite models with proper relationships
- **JWT Authentication**: Register, login, refresh, logout endpoints with secure token handling
- **Password Security**: bcrypt hashing with salting
- **Database Migrations**: Alembic setup for schema management
- **Data Seeding**: Comprehensive seeding script with sample data
- **Authentication Middleware**: Protected routes with role-based access
- **Test Coverage**: 73% coverage with comprehensive unit tests

## 🏗️ Architecture

### Database Schema
- **Users**: Authentication, profiles, soft deletes
- **Books**: Metadata, ratings, genre relationships
- **Genres**: Normalized many-to-many with books
- **Reviews**: User ratings and comments with unique constraints
- **Favorites**: User's favorite books tracking

### API Endpoints

#### Authentication (`/api/v1/auth`)
- `POST /register` - User registration with JWT tokens
- `POST /login` - User authentication
- `POST /refresh` - Refresh access tokens
- `POST /logout` - Invalidate refresh tokens
- `GET /me` - Get current user info
- `GET /verify-token` - Verify token validity

#### Users (`/api/v1/users`)
- `GET /` - List users (verified users only)
- `GET /{user_id}` - Get user by ID
- `PUT /{user_id}` - Update user (self only)
- `DELETE /{user_id}` - Delete user (self only)
- `POST /{user_id}/verify` - Verify user email
- `POST /{user_id}/activate` - Activate user account

## 🧪 Testing

Run the test suite with coverage:

```bash
python -m pytest app/tests/ -v --cov=app --cov-report=term-missing
```

Current test coverage: **73%**

Test categories:
- **Models**: Database model validation, relationships, constraints
- **Authentication**: JWT tokens, password hashing, security functions
- **API Endpoints**: Authentication flow, user management
- **Services**: Business logic testing

## 🔧 Setup & Development

### Prerequisites
- Python 3.10+
- PostgreSQL 12+

### Local Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables (create `.env`):
   ```env
   DATABASE_URL=postgresql://plottwist:plottwist@localhost/plottwist
   SECRET_KEY=your-secret-key-here
   DEBUG=true
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Seed the database (optional):
   ```bash
   python seed_database.py
   ```

5. Start the development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Development
Use the provided Docker Compose configuration for full-stack development:

```bash
# From the workspace root
docker-compose up -d
```

## 🔐 Authentication

### JWT Token Flow
1. **Registration/Login**: Receive access token (1h) + refresh token (30d)
2. **API Requests**: Include `Authorization: Bearer <access_token>`
3. **Token Refresh**: Use refresh token to get new access token
4. **Logout**: Invalidate refresh token

### Security Features
- bcrypt password hashing with salt
- JWT tokens with expiration
- Refresh token rotation
- Protected routes with middleware
- User role verification (active/verified)

## 📊 Database Models

### User Model
```python
class User(Base):
    id: int (PK)
    email: str (unique, indexed)
    hashed_password: str
    name: str
    is_active: bool (default: True)
    is_verified: bool (default: False)
    refresh_token: str (nullable)
    created_at: datetime
    updated_at: datetime
```

### Book Model
```python
class Book(Base):
    id: int (PK)
    title: str (indexed)
    author: str (indexed)
    description: text
    published_year: int (indexed)
    isbn: str (unique, indexed)
    cover_url: str
    average_rating: float (default: 0.0)
    total_reviews: int (default: 0)
    created_at: datetime
    updated_at: datetime
```

### Genre Model
```python
class Genre(Base):
    id: int (PK)
    name: str (unique, indexed)
    description: text
    created_at: datetime
```

### Review Model
```python
class Review(Base):
    id: int (PK)
    user_id: int (FK, indexed)
    book_id: int (FK, indexed)
    rating: float (1.0-5.0)
    title: str
    content: text
    created_at: datetime
    updated_at: datetime
    # Constraint: unique(user_id, book_id)
```

### Favorite Model
```python
class Favorite(Base):
    id: int (PK)
    user_id: int (FK, indexed)
    book_id: int (FK, indexed)
    created_at: datetime
    # Constraint: unique(user_id, book_id)
```

## 📈 Next Steps (Upcoming Tasks)
- **Task 003**: Book Data Population and Basic APIs
- **Task 004**: Frontend Authentication and Routing
- **Task 005**: Book Browsing and Search Frontend
- **Task 006**: Review and Rating System Backend
- **Task 007**: Review and Rating System Frontend
- **Task 008**: User Profile and Favorites System
- **Task 009**: Traditional Recommendation System
- **Task 010**: AI-Powered Recommendations
- **Task 011**: Deployment Infrastructure
- **Task 012**: Final Integration and Testing

## 🔗 Related Files
- **Frontend Repository**: `../plottwist-frontend/`
- **Full-Stack Setup**: `../docker-compose.yml`
- **Database Initialization**: `./init-db.sql`
- **Development Setup Guide**: `./DEVELOPMENT_SETUP.md`
- **Troubleshooting Guide**: `./TROUBLESHOOTING.md`

## 🐛 Common Issues & Fixes

### "relation 'users' does not exist" Error
If you see this error when trying to register users, it means the database tables weren't created. This is now fixed automatically:
- **Latest Fix**: The application now creates database tables automatically on startup
- **Manual Fix**: If still having issues, restart the Docker containers: `docker-compose down && docker-compose up --build`

### Missing pytest-cov for Coverage Calculation
- **Fixed**: `pytest-cov==4.2.1` is now included in `requirements.txt`
- **Usage**: Run `pytest --cov=app --cov-report=term-missing` to calculate test coverage

## 📝 API Documentation

Once the server is running, access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc 