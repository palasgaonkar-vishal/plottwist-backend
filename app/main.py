"""
PlotTwist Backend - FastAPI Application
Main application entry point with basic configuration and health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime

app = FastAPI(
    title="PlotTwist API",
    description="A book review platform with AI-powered recommendations",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint returning basic API information."""
    return {
        "message": "Welcome to PlotTwist API",
        "version": "1.0.0",
        "docs": "/api/v1/docs"
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring and validation."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "plottwist-backend",
            "version": "1.0.0"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 