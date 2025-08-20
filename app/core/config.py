"""
Application configuration management using environment variables.
"""

from decouple import config
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    # Database configuration
    DATABASE_URL: str = config(
        "DATABASE_URL", 
        default="postgresql://plottwist:plottwist@localhost/plottwist"
    )
    TEST_DATABASE_URL: str = config(
        "TEST_DATABASE_URL",
        default="postgresql://plottwist:plottwist@localhost/plottwist_test"
    )
    
    # JWT configuration
    SECRET_KEY: str = config(
        "SECRET_KEY", 
        default="your-secret-key-change-in-production"
    )
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=60, cast=int)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=30, cast=int)
    
    # API configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PlotTwist"
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = config("OPENAI_API_KEY", default=None)
    
    # Environment
    ENVIRONMENT: str = config("ENVIRONMENT", default="development")
    DEBUG: bool = config("DEBUG", default=True, cast=bool)
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000"]


settings = Settings() 