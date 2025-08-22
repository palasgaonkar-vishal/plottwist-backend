"""
Application configuration management using environment variables.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PlotTwist API"
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://plottwist:plottwist@localhost/plottwist"
    )
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql://plottwist:plottwist@localhost/plottwist_test"
    )
    
    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",
        "http://localhost:8080",  # Alternative frontend port
    ]
    
    # Environment Configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Application Configuration
    MAX_CONNECTIONS_COUNT: int = 10
    MIN_CONNECTIONS_COUNT: int = 10
    
    class Config:
        case_sensitive = True


# Create settings instance
settings = Settings() 