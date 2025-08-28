# PlotTwist Backend API

A comprehensive FastAPI-based backend for the PlotTwist book review platform with AI-powered recommendations.

## 🚀 Features Implemented

### ✅ **Core Features**
- **User Authentication**: JWT-based authentication with registration, login, and token refresh
- **Book Management**: Complete CRUD operations with search, filtering, and pagination
- **Review System**: User reviews with ratings, CRUD operations, and statistics
- **User Profiles**: Extended user profiles with bio, location, website, and statistics
- **Favorites System**: Book favoriting with toggle functionality and popular books tracking
- **Recommendation Engine**: AI-powered content-based and popularity-based recommendations
- **Recommendation Feedback**: Thumbs up/down feedback system for recommendation improvement

### 🔧 **Technical Features**
- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **PostgreSQL Database**: Robust relational database with SQLAlchemy ORM
- **Pydantic Validation**: Data validation and serialization
- **JWT Authentication**: Secure token-based authentication
- **Database Migrations**: Alembic for database schema management
- **Comprehensive Testing**: 80%+ test coverage with pytest
- **OpenAPI Documentation**: Auto-generated API documentation at `/docs`

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh

### Users
- `GET /api/v1/users/me/` - Get current user info
- `PUT /api/v1/users/me/` - Update current user profile
- `GET /api/v1/users/me/profile/` - Get current user profile with statistics
- `GET /api/v1/users/me/reviews/` - Get current user's reviews with sorting
- `GET /api/v1/users/{id}/profile/` - Get public user profile

### Books
- `GET /api/v1/books/` - List books with pagination and filters
- `GET /api/v1/books/search` - Advanced book search
- `GET /api/v1/books/{id}` - Get specific book details
- `POST /api/v1/books/` - Create new book (authenticated)
- `PUT /api/v1/books/{id}` - Update book (authenticated)
- `DELETE /api/v1/books/{id}` - Delete book (authenticated)
- `GET /api/v1/books/genres/` - List all genres

### Reviews
- `POST /api/v1/reviews/` - Create review
- `GET /api/v1/reviews/{id}/` - Get specific review
- `PUT /api/v1/reviews/{id}/` - Update review (owner only)
- `DELETE /api/v1/reviews/{id}/` - Delete review (owner only)
- `GET /api/v1/reviews/book/{book_id}/` - Get book reviews with pagination
- `GET /api/v1/reviews/book/{book_id}/stats/` - Get book rating statistics

### Favorites
- `POST /api/v1/favorites/` - Add book to favorites
- `DELETE /api/v1/favorites/{book_id}/` - Remove from favorites
- `POST /api/v1/favorites/toggle/{book_id}/` - Toggle favorite status
- `GET /api/v1/favorites/check/{book_id}/` - Check favorite status
- `GET /api/v1/favorites/me/` - Get user's favorites with pagination
- `GET /api/v1/favorites/popular/` - Get most favorited books

### Recommendations
- `GET /api/v1/recommendations/content-based/` - Get content-based recommendations
- `GET /api/v1/recommendations/popularity-based/` - Get popularity-based recommendations
- `GET /api/v1/recommendations/all/` - Get all recommendation types
- `POST /api/v1/recommendations/feedback/` - Submit recommendation feedback
- `GET /api/v1/recommendations/stats/` - Get recommendation statistics

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- pip or poetry

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/palasgaonkar-vishal/plottwist-backend.git
   cd plottwist-backend
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

5. **Set up PostgreSQL database**
   ```bash
   # Create database and user
   psql -c "CREATE USER plottwist WITH PASSWORD 'your_password';"
   psql -c "CREATE DATABASE plottwist OWNER plottwist;"
   
   # Or run the initialization script
   psql -U postgres -f init-db.sql
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Seed the database (optional)**
   ```bash
   python seed_database.py
   ```

8. **Start the development server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py

# Run with verbose output
pytest -v
```

### Test Coverage
Current test coverage: **80%+**

Key test areas:
- Authentication and authorization
- Book CRUD operations and search
- Review system with rating calculations  
- User profile and favorites functionality
- Recommendation algorithms
- API endpoint validation
- Database models and relationships

## 🚀 Production Deployment

### AWS EC2 Deployment
The backend is configured for production deployment on AWS EC2 using our infrastructure automation:

1. **Infrastructure Setup**
   ```bash
   cd ../infrastructure/terraform/
   terraform init
   terraform apply
   ```

2. **CI/CD Pipeline**
   - GitHub Actions automatically deploy on push to `main`
   - Includes testing, security scanning, and health checks
   - See `.github/workflows/` for pipeline configuration

3. **Manual Deployment**
   ```bash
   # SSH to production server
   ssh ubuntu@your-ec2-instance
   
   # Run deployment script
   sudo -u ubuntu /opt/plottwist/deploy.sh
   ```

### Docker Deployment
```bash
# Build Docker image
docker build -t plottwist-backend .

# Run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Configuration

#### Production Environment Variables
```bash
DATABASE_URL=postgresql://plottwist:password@localhost:5432/plottwist
JWT_SECRET_KEY=your-secure-jwt-secret-key
ENVIRONMENT=production
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com
```

## 📊 Performance & Monitoring

### Health Checks
- **Endpoint**: `GET /api/v1/health`
- **Response**: `{"status": "healthy", "timestamp": "..."}`
- **Monitoring**: Automated health checks every 30 seconds

### Database Performance
- Connection pooling with SQLAlchemy
- Database query optimization
- Indexed columns for fast lookups
- Pagination for large datasets

### API Performance
- Async/await for concurrent operations
- Response caching for static data
- Rate limiting for API protection
- Comprehensive error handling

## 🔒 Security Features

### Authentication & Authorization
- JWT tokens with expiration
- Password hashing with bcrypt
- Role-based access control
- Token refresh mechanism

### Data Protection
- Input validation with Pydantic
- SQL injection prevention
- XSS protection
- CORS configuration

### API Security
- Rate limiting
- Request size limits
- Security headers
- Environment-based configuration

## 🧩 Architecture

### Project Structure
```
app/
├── main.py              # FastAPI application entry point
├── core/                # Core configurations and dependencies
│   ├── config.py        # Settings and configuration
│   ├── security.py      # Authentication utilities
│   └── dependencies.py  # Dependency injection
├── models/              # SQLAlchemy database models
├── schemas/             # Pydantic request/response models
├── routers/             # API route handlers
├── services/            # Business logic layer
├── tests/               # Test suites
└── utils/               # Utility functions
```

### Database Schema
- **Users**: User accounts with profiles
- **Books**: Book information with genres
- **Reviews**: User reviews and ratings
- **Favorites**: User favorite books
- **Recommendation Feedback**: AI recommendation feedback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR

## 📝 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Authentication
Most endpoints require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Error Responses
All endpoints return consistent error responses:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## 🎯 Current Status

**Task Implementation Status:**
- ✅ **Task 001**: Project Setup and Infrastructure
- ✅ **Task 002**: Database Models and Authentication  
- ✅ **Task 003**: Book Data Population and Basic APIs
- ✅ **Task 006**: Review and Rating System Backend
- ✅ **Task 008**: User Profile and Favorites System
- ✅ **Task 009**: Traditional Recommendation System
- ✅ **Task 010**: AI-Powered Recommendations  
- ✅ **Task 011**: Deployment Infrastructure

**Features Ready for Production:**
- Complete user authentication system
- Full book management with Open Library integration
- Comprehensive review and rating system
- User profiles with statistics and favorites
- AI-powered recommendation engine
- Production-ready deployment infrastructure
- Comprehensive test suite (80%+ coverage)

## 📞 Support

For issues or questions:
1. Check the [API documentation](http://localhost:8000/docs)
2. Review the [troubleshooting guide](../infrastructure/README.md#troubleshooting)
3. Submit an issue on GitHub

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**PlotTwist Backend - Ready for Production** 🚀
