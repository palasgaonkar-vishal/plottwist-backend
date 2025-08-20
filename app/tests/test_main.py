"""
Tests for main application endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to PlotTwist API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/api/v1/docs"


def test_health_check():
    """Test the health check endpoint returns healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "plottwist-backend"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_docs_endpoint():
    """Test that API documentation is accessible."""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200


def test_redoc_endpoint():
    """Test that ReDoc documentation is accessible."""
    response = client.get("/api/v1/redoc")
    assert response.status_code == 200 