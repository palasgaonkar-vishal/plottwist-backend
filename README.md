# PlotTwist Backend

FastAPI-based backend for the PlotTwist book review platform with AI-powered recommendations.

## 🚀 Features

- **FastAPI** REST API with automatic OpenAPI documentation
- **PostgreSQL** database with SQLAlchemy ORM
- **JWT Authentication** with refresh token support
- **Alembic** database migrations
- **Comprehensive testing** with pytest (80%+ coverage)
- **Code quality** with Black formatting and Flake8 linting

## 📋 Requirements

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (for development)

## 🛠️ Development Setup

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the project root
2. Start all services:
   ```bash
   docker-compose up -d
   ```
3. The backend will be available at `http://localhost:8000`
4. API documentation at `http://localhost:8000/api/v1/docs`

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. Start PostgreSQL and create databases:
   ```sql
   CREATE DATABASE plottwist;
   CREATE DATABASE plottwist_test;
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## 🧪 Testing

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

## 📝 Code Quality

Format code:
```bash
black .
```

Lint code:
```bash
flake8 .
```

## 🏗️ Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application entry point
├── core/
│   ├── __init__.py
│   └── config.py        # Application configuration
├── api/                 # API routes (added in later tasks)
├── models/              # Database models (added in later tasks)
├── services/            # Business logic (added in later tasks)
└── tests/
    ├── __init__.py
    └── test_main.py     # Basic application tests
```

## 📚 API Documentation

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`

## 🔒 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://plottwist:plottwist@localhost/plottwist` |
| `TEST_DATABASE_URL` | Test database connection string | `postgresql://plottwist:plottwist@localhost/plottwist_test` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-change-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token expiration | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token expiration | `30` |
| `OPENAI_API_KEY` | OpenAI API key for recommendations | `None` |

## 🚀 Deployment

Deployment configuration will be added in Task 011.

## 📄 License

This project is part of the PlotTwist book review platform. 