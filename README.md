# PlotTwist Backend

A FastAPI-based backend for the PlotTwist book review platform with AI-powered recommendations.

## Features

- User authentication and authorization
- Book management and search
- Review and rating system
- User favorites management
- **AI-Powered Recommendation System** (Task 009)
  - Content-based recommendations using user preferences
  - Popularity-based recommendations with rating analysis
  - Advanced filtering and personalization
  - Recommendation feedback tracking and analytics

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile

### Books
- `GET /api/v1/books/` - List books with search and filters
- `GET /api/v1/books/{book_id}` - Get book details
- `POST /api/v1/books/` - Create new book (admin)

### Reviews
- `GET /api/v1/reviews/` - List reviews
- `POST /api/v1/reviews/` - Create review
- `GET /api/v1/reviews/{review_id}` - Get review details
- `PUT /api/v1/reviews/{review_id}` - Update review
- `DELETE /api/v1/reviews/{review_id}` - Delete review

### Favorites
- `GET /api/v1/favorites/` - Get user's favorite books
- `POST /api/v1/favorites/` - Add book to favorites
- `DELETE /api/v1/favorites/{book_id}` - Remove from favorites

### **Recommendations (NEW - Task 009)**
- `GET /api/v1/recommendations/content-based/` - Get personalized content-based recommendations
- `GET /api/v1/recommendations/popularity-based/` - Get popularity-based recommendations
- `GET /api/v1/recommendations/all/` - Get both recommendation types
- `POST /api/v1/recommendations/feedback/` - Submit recommendation feedback
- `GET /api/v1/recommendations/stats/` - Get recommendation analytics
- `POST /api/v1/recommendations/invalidate-cache/` - Clear user recommendation cache

## Recommendation System Details

### Content-Based Recommendations
The content-based recommendation system analyzes user preferences from their:
- Favorite books and their genres
- Highly-rated reviews (4+ stars)
- Reading patterns and genre preferences

**Algorithm Features:**
- Genre similarity scoring using TF-IDF vectors
- User preference profiling based on favorites and reviews
- Configurable parameters (limit, min_rating, exclude_user_books)
- Fallback to popular books when insufficient user data

### Popularity-Based Recommendations
The popularity-based system recommends books using:
- Average rating calculations
- Review count weighting
- Favorite count analysis
- Recency factors for trending books

**Scoring Formula:**
```
score = (avg_rating * 0.7) + (normalized_review_count * 0.2) + (normalized_favorite_count * 0.1)
```

### Advanced Features
- **Caching**: Redis-compatible caching for performance
- **Feedback Loop**: User feedback improves future recommendations
- **Analytics**: Comprehensive stats on recommendation effectiveness
- **Filtering**: Genre, rating, and user book exclusion filters
- **Pagination**: Configurable limits and pagination support

## Installation

1. **Prerequisites**
   ```bash
   python 3.8+
   PostgreSQL
   Redis (optional, for caching)
   ```

2. **Setup Environment**
   ```bash
   cd plottwist-backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb plottwist
   
   # Run migrations
   alembic upgrade head
   
   # Seed sample data (optional)
   python seed_database.py
   ```

4. **Environment Variables**
   Create `.env` file:
   ```env
   DATABASE_URL=postgresql://username:password@localhost/plottwist
   SECRET_KEY=your-secret-key-here
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ALGORITHM=HS256
   REDIS_URL=redis://localhost:6379  # Optional
   ```

5. **Run Application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test modules
pytest app/tests/test_recommendations_api.py -v
pytest app/tests/test_recommendation_service.py -v

# Test recommendation endpoints
pytest app/tests/test_recommendations_api.py::TestRecommendationsAPI::test_get_content_based_recommendations -v
```

## Recommendation API Usage Examples

### Get Content-Based Recommendations
```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/content-based/?limit=10&exclude_user_books=true&min_rating=4.0" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Submit Recommendation Feedback
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/feedback/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 123,
    "recommendation_type": "content_based",
    "is_positive": true,
    "context_data": "{\"page\": \"home\", \"position\": 1}"
  }'
```

### Get Recommendation Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/stats/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Architecture

```
app/
├── core/           # Core configuration and dependencies
├── models/         # SQLAlchemy database models
├── schemas/        # Pydantic schemas for API
├── routers/        # FastAPI route handlers
├── services/       # Business logic layer
│   └── recommendation_service.py  # Recommendation algorithms
├── tests/          # Test suite
└── utils/          # Utility functions
```

## Database Schema

### New Tables (Task 009)
- **recommendation_feedback**: Tracks user feedback on recommendations
- **recommendation_cache**: Caches recommendation results (optional)

### Key Relationships
- Users ↔ Favorites ↔ Books
- Users ↔ Reviews ↔ Books
- Books ↔ Genres (many-to-many)
- Users ↔ RecommendationFeedback ↔ Books

## Performance Considerations

1. **Caching**: Recommendation results cached for 1 hour
2. **Database Indexing**: Optimized queries on ratings, favorites, and genres
3. **Pagination**: Large result sets properly paginated
4. **Async Operations**: All database operations are async
5. **Connection Pooling**: PostgreSQL connection pooling enabled

## Development Notes

- **Code Quality**: 90%+ test coverage, type hints throughout
- **API Documentation**: Auto-generated OpenAPI/Swagger docs at `/docs`
- **Logging**: Comprehensive logging for debugging and monitoring
- **Error Handling**: Graceful error handling with appropriate HTTP status codes
- **Security**: JWT authentication, input validation, SQL injection protection

## Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Run `pytest` and ensure all tests pass
5. Use type hints for new functions

## License

MIT License
