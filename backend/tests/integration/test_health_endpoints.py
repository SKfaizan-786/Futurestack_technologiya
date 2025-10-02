"""
Integration tests for health check endpoints.

Tests comprehensive health monitoring, error handling,
and readiness/liveness probes under various failure scenarios.
"""
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import httpx
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.health import (
    check_database_health,
    check_cerebras_api_health, 
    check_clinicaltrials_api_health,
    run_all_health_checks,
    calculate_overall_status,
    ComponentHealth
)


class TestHealthEndpoints:
    """Test health check endpoints with various scenarios."""
    
    def test_basic_health_check(self):
        """Test basic health endpoint returns expected format."""
        client = TestClient(app)
        response = client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["checks"] == {}
    
    def test_liveness_probe(self):
        """Test liveness probe endpoint."""
        client = TestClient(app)
        response = client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint provides system information."""
        client = TestClient(app)
        response = client.get("/api/v1/health/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check basic metrics structure
        assert "uptime_seconds" in data
        assert "environment" in data
        assert "version" in data
        assert "python_version" in data
        assert "database_url" in data
        assert "api_endpoints" in data
        assert "features" in data
        
        # Verify URL masking
        assert "***" in data["database_url"]
        
        # Check nested structures
        assert "cerebras" in data["api_endpoints"]
        assert "clinicaltrials" in data["api_endpoints"]
        assert "hipaa_compliance" in data["features"]
        assert "cors_enabled" in data["features"]
        assert "debug_mode" in data["features"]
    
    @pytest.mark.asyncio
    async def test_readiness_check_all_healthy(self):
        """Test readiness check when all components are healthy."""
        client = TestClient(app)
        
        # Mock all health checks to return healthy
        with patch('src.api.health.run_all_health_checks') as mock_checks:
            mock_checks.return_value = {
                "database": ComponentHealth(
                    status="healthy",
                    latency_ms=1.0,
                    last_checked=datetime.now(timezone.utc)
                ),
                "cerebras_api": ComponentHealth(
                    status="healthy", 
                    latency_ms=50.0,
                    last_checked=datetime.now(timezone.utc)
                ),
                "clinicaltrials_api": ComponentHealth(
                    status="healthy",
                    latency_ms=100.0,
                    last_checked=datetime.now(timezone.utc)
                )
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "checks" in data
            assert len(data["checks"]) == 3
    
    @pytest.mark.asyncio 
    async def test_readiness_check_unhealthy_returns_503(self):
        """Test readiness check returns 503 when components are unhealthy."""
        client = TestClient(app)
        
        # Mock health checks with unhealthy database
        with patch('src.api.health.run_all_health_checks') as mock_checks:
            mock_checks.return_value = {
                "database": ComponentHealth(
                    status="unhealthy",
                    error="Connection failed",
                    last_checked=datetime.now(timezone.utc)
                ),
                "cerebras_api": ComponentHealth(
                    status="healthy",
                    latency_ms=50.0,
                    last_checked=datetime.now(timezone.utc)
                ),
                "clinicaltrials_api": ComponentHealth(
                    status="healthy", 
                    latency_ms=100.0,
                    last_checked=datetime.now(timezone.utc)
                )
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            # The detail should contain the health status
            detail = data["detail"]
            assert detail["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_readiness_check_degraded_returns_200(self):
        """Test readiness check returns 200 for degraded status."""
        client = TestClient(app)
        
        # Mock health checks with degraded component
        with patch('src.api.health.run_all_health_checks') as mock_checks:
            mock_checks.return_value = {
                "database": ComponentHealth(
                    status="healthy",
                    latency_ms=1.0,
                    last_checked=datetime.now(timezone.utc)
                ),
                "cerebras_api": ComponentHealth(
                    status="degraded",
                    latency_ms=500.0,
                    error="Slow response",
                    last_checked=datetime.now(timezone.utc)
                ),
                "clinicaltrials_api": ComponentHealth(
                    status="healthy",
                    latency_ms=100.0, 
                    last_checked=datetime.now(timezone.utc)
                )
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"


class TestComponentHealthChecks:
    """Test individual component health check functions."""
    
    @pytest.mark.asyncio
    async def test_database_health_check_success(self):
        """Test successful database health check."""
        result = await check_database_health()
        
        assert result.status == "healthy"
        assert result.latency_ms is not None
        assert result.latency_ms > 0
        assert result.last_checked is not None
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_database_health_check_exception(self):
        """Test database health check with exception."""
        with patch('asyncio.sleep', side_effect=Exception("Database error")):
            result = await check_database_health()
            
            assert result.status == "unhealthy"
            assert result.error == "Database error"
            assert result.last_checked is not None
    
    @pytest.mark.asyncio
    async def test_cerebras_api_health_test_environment(self):
        """Test Cerebras API health check in test environment."""
        with patch('src.api.health.settings') as mock_settings:
            mock_settings.environment = "test"
            mock_settings.cerebras_api_key = "test-key"
            
            result = await check_cerebras_api_health()
            
            assert result.status == "healthy"
            assert result.latency_ms == 1.0
            assert result.last_checked is not None
    
    @pytest.mark.asyncio
    async def test_cerebras_api_health_200_response(self):
        """Test Cerebras API health check with successful response."""
        with patch('src.api.health.settings') as mock_settings:
            mock_settings.environment = "production"
            mock_settings.cerebras_api_key = "real-key"
            mock_settings.cerebras_base_url = "https://api.cerebras.ai/v1"
            
            # Mock successful HTTP response
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await check_cerebras_api_health()
                
                assert result.status == "healthy"
                assert result.latency_ms is not None
                assert result.error is None
    
    @pytest.mark.asyncio
    async def test_cerebras_api_health_401_response(self):
        """Test Cerebras API health check with authentication failure."""
        with patch('src.api.health.settings') as mock_settings:
            mock_settings.environment = "production"
            mock_settings.cerebras_api_key = "invalid-key"
            mock_settings.cerebras_base_url = "https://api.cerebras.ai/v1"
            
            # Mock 401 response
            mock_response = MagicMock()
            mock_response.status_code = 401
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await check_cerebras_api_health()
                
                assert result.status == "unhealthy"
                assert result.error == "Authentication failed - check API key"
    
    @pytest.mark.asyncio
    async def test_cerebras_api_health_timeout(self):
        """Test Cerebras API health check with timeout."""
        with patch('src.api.health.settings') as mock_settings:
            mock_settings.environment = "production"
            mock_settings.cerebras_api_key = "real-key"
            mock_settings.cerebras_base_url = "https://api.cerebras.ai/v1"
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")
                
                result = await check_cerebras_api_health()
                
                assert result.status == "unhealthy"
                assert result.error == "Request timeout"
    
    @pytest.mark.asyncio
    async def test_cerebras_api_health_other_status(self):
        """Test Cerebras API health check with other HTTP status."""
        with patch('src.api.health.settings') as mock_settings:
            mock_settings.environment = "production"
            mock_settings.cerebras_api_key = "real-key"
            mock_settings.cerebras_base_url = "https://api.cerebras.ai/v1"
            
            # Mock 500 response
            mock_response = MagicMock()
            mock_response.status_code = 500
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await check_cerebras_api_health()
                
                assert result.status == "degraded"
                assert result.error == "HTTP 500"
                assert result.latency_ms is not None
    
    @pytest.mark.asyncio
    async def test_clinicaltrials_api_health_test_environment(self):
        """Test ClinicalTrials API health check in test environment."""
        with patch('src.api.health.settings') as mock_settings:
            mock_settings.environment = "test"
            
            result = await check_clinicaltrials_api_health()
            
            assert result.status == "healthy"
            assert result.latency_ms == 10.0
            assert result.last_checked is not None
    
    @pytest.mark.asyncio
    async def test_clinicaltrials_api_health_success(self):
        """Test ClinicalTrials API health check with successful response."""
        with patch('src.api.health.settings') as mock_settings:
            mock_settings.environment = "production"
            mock_settings.clinicaltrials_base_url = "https://clinicaltrials.gov/api/v2"
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await check_clinicaltrials_api_health()
                
                assert result.status == "healthy"
                assert result.latency_ms is not None
                assert result.error is None
    
    @pytest.mark.asyncio
    async def test_clinicaltrials_api_health_timeout(self):
        """Test ClinicalTrials API health check with timeout."""
        with patch('src.api.health.settings') as mock_settings:
            mock_settings.environment = "production"
            mock_settings.clinicaltrials_base_url = "https://clinicaltrials.gov/api/v2"
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")
                
                result = await check_clinicaltrials_api_health()
                
                assert result.status == "unhealthy"
                assert result.error == "Request timeout"
    
    @pytest.mark.asyncio
    async def test_clinicaltrials_api_health_error_status(self):
        """Test ClinicalTrials API health check with error status."""
        with patch('src.api.health.settings') as mock_settings:
            mock_settings.environment = "production"
            mock_settings.clinicaltrials_base_url = "https://clinicaltrials.gov/api/v2"
            
            # Mock error response
            mock_response = MagicMock()
            mock_response.status_code = 404
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await check_clinicaltrials_api_health()
                
                assert result.status == "degraded"
                assert result.error == "HTTP 404"
                assert result.latency_ms is not None
    
    @pytest.mark.asyncio
    async def test_run_all_health_checks_success(self):
        """Test running all health checks successfully."""
        result = await run_all_health_checks()
        
        assert "database" in result
        assert "cerebras_api" in result
        assert "clinicaltrials_api" in result
        assert len(result) == 3
        
        # All should be ComponentHealth instances
        for component in result.values():
            assert isinstance(component, ComponentHealth)
    
    @pytest.mark.asyncio
    async def test_run_all_health_checks_with_exceptions(self):
        """Test running health checks when some raise exceptions."""
        with patch('src.api.health.check_database_health', side_effect=Exception("DB error")):
            with patch('src.api.health.check_cerebras_api_health', side_effect=Exception("API error")):
                result = await run_all_health_checks()
                
                assert len(result) == 3
                assert result["database"].status == "unhealthy"
                assert result["database"].error == "DB error"
                assert result["cerebras_api"].status == "unhealthy" 
                assert result["cerebras_api"].error == "API error"
                # ClinicalTrials should still work
                assert result["clinicaltrials_api"].status == "healthy"
    
    def test_calculate_overall_status_all_healthy(self):
        """Test overall status calculation with all healthy components."""
        checks = {
            "db": ComponentHealth(status="healthy", last_checked=datetime.now(timezone.utc)),
            "api": ComponentHealth(status="healthy", last_checked=datetime.now(timezone.utc))
        }
        
        result = calculate_overall_status(checks)
        assert result == "healthy"
    
    def test_calculate_overall_status_with_unhealthy(self):
        """Test overall status calculation with unhealthy component."""
        checks = {
            "db": ComponentHealth(status="healthy", last_checked=datetime.now(timezone.utc)),
            "api": ComponentHealth(status="unhealthy", last_checked=datetime.now(timezone.utc))
        }
        
        result = calculate_overall_status(checks)
        assert result == "unhealthy"
    
    def test_calculate_overall_status_with_degraded(self):
        """Test overall status calculation with degraded component."""
        checks = {
            "db": ComponentHealth(status="healthy", last_checked=datetime.now(timezone.utc)),
            "api": ComponentHealth(status="degraded", last_checked=datetime.now(timezone.utc))
        }
        
        result = calculate_overall_status(checks)
        assert result == "degraded"
    
    def test_calculate_overall_status_mixed_unhealthy_wins(self):
        """Test overall status calculation - unhealthy takes precedence over degraded."""
        checks = {
            "db": ComponentHealth(status="degraded", last_checked=datetime.now(timezone.utc)),
            "api": ComponentHealth(status="unhealthy", last_checked=datetime.now(timezone.utc)),
            "cache": ComponentHealth(status="healthy", last_checked=datetime.now(timezone.utc))
        }
        
        result = calculate_overall_status(checks)
        assert result == "unhealthy"