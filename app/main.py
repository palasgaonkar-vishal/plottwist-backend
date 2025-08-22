"""
PlotTwist Backend - FastAPI Application
Main application entry point with basic configuration and health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from app.routers import auth_router, users_router, books_router
from app.core.config import settings
from app.database import create_tables

app = FastAPI(
    title="PlotTwist API",
    description="A book review platform with AI-powered recommendations",
    version="1.0.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database initialization
@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    create_tables()


# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(books_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to PlotTwist API",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs",
        "features": [
            "User Authentication with JWT",
            "Book Reviews and Ratings",
            "User Profiles and Favorites",
            "AI-Powered Recommendations",
        ],
    }


@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "plottwist-backend",
            "version": "1.0.0",
            "database": "postgresql",
            "features": {
                "authentication": True,
                "user_management": True,
                "database_models": True,
            },
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
