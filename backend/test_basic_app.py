"""
Simple test to verify FastAPI application starts correctly.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "uptime_seconds" in data


def test_readiness_check():
    """Test readiness probe endpoint."""
    response = client.get("/api/v1/health/ready")
    # May return 503 if external services are not available, but should not error
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "checks" in data


def test_liveness_check():
    """Test liveness probe endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "uptime_seconds" in data


def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "environment" in data
    assert "version" in data


def test_cors_headers():
    """Test CORS headers are present."""
    response = client.get("/api/v1/health/")
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers


def test_security_headers():
    """Test security headers are present."""
    response = client.get("/api/v1/health/")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert "x-request-id" in response.headers


def test_request_id_header():
    """Test that request ID is generated and returned."""
    response = client.get("/api/v1/health/")
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"].startswith("req_")


def test_response_time_header():
    """Test that response time is measured and returned."""
    response = client.get("/api/v1/health/")
    assert "x-response-time" in response.headers
    assert response.headers["x-response-time"].endswith("s")


if __name__ == "__main__":
    # Run basic tests
    test_health_check()
    test_liveness_check()
    test_metrics_endpoint()
    print("✅ All basic tests passed!")