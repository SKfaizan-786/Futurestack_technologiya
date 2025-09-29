"""
Health check endpoints for MedMatch AI.

Provides system health monitoring, dependency status checks,
and readiness probes for Kubernetes deployment.
"""
import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import httpx

from ..integrations.cerebras_client import CerebrasClient
from ..integrations.trials_api_client import ClinicalTrialsClient
from ..utils.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    checks: Dict[str, Any] = Field(..., description="Individual component health checks")


class ComponentHealth(BaseModel):
    """Individual component health status."""
    status: str = Field(..., description="Component status (healthy/unhealthy/degraded)")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    last_checked: datetime = Field(..., description="Last health check timestamp")


# Application start time for uptime calculation
_start_time = time.time()


async def check_database_health() -> ComponentHealth:
    """
    Check database connectivity and performance.
    
    Returns:
        Database health status
    """
    start_time = time.time()
    
    try:
        # TODO: Implement actual database health check
        # For now, simulate a quick check
        await asyncio.sleep(0.001)  # Simulate DB query
        
        latency_ms = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            status="healthy",
            latency_ms=latency_ms,
            last_checked=datetime.now()
        )
        
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return ComponentHealth(
            status="unhealthy",
            error=str(e),
            last_checked=datetime.now()
        )


async def check_cerebras_api_health() -> ComponentHealth:
    """
    Check Cerebras API connectivity and authentication.
    
    Returns:
        Cerebras API health status
    """
    start_time = time.time()
    
    try:
        # Quick authentication test (no actual model call)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.cerebras_base_url}/models",
                headers={"Authorization": f"Bearer {settings.cerebras_api_key}"},
                timeout=5.0
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ComponentHealth(
                    status="healthy",
                    latency_ms=latency_ms,
                    last_checked=datetime.now()
                )
            elif response.status_code == 401:
                return ComponentHealth(
                    status="unhealthy",
                    error="Authentication failed - check API key",
                    last_checked=datetime.now()
                )
            else:
                return ComponentHealth(
                    status="degraded",
                    latency_ms=latency_ms,
                    error=f"HTTP {response.status_code}",
                    last_checked=datetime.now()
                )
                
    except httpx.TimeoutException:
        return ComponentHealth(
            status="unhealthy",
            error="Request timeout",
            last_checked=datetime.now()
        )
    except Exception as e:
        logger.error("Cerebras API health check failed", error=str(e))
        return ComponentHealth(
            status="unhealthy",
            error=str(e),
            last_checked=datetime.now()
        )


async def check_clinicaltrials_api_health() -> ComponentHealth:
    """
    Check ClinicalTrials.gov API connectivity.
    
    Returns:
        ClinicalTrials API health status
    """
    start_time = time.time()
    
    try:
        # Quick connectivity test
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.clinicaltrials_base_url}/studies",
                params={"query.cond": "diabetes", "pageSize": 1},
                timeout=5.0
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ComponentHealth(
                    status="healthy",
                    latency_ms=latency_ms,
                    last_checked=datetime.now()
                )
            else:
                return ComponentHealth(
                    status="degraded",
                    latency_ms=latency_ms,
                    error=f"HTTP {response.status_code}",
                    last_checked=datetime.now()
                )
                
    except httpx.TimeoutException:
        return ComponentHealth(
            status="unhealthy",
            error="Request timeout",
            last_checked=datetime.now()
        )
    except Exception as e:
        logger.error("ClinicalTrials API health check failed", error=str(e))
        return ComponentHealth(
            status="unhealthy",
            error=str(e),
            last_checked=datetime.now()
        )


async def run_all_health_checks() -> Dict[str, ComponentHealth]:
    """
    Run all health checks concurrently.
    
    Returns:
        Dictionary of component health statuses
    """
    # Run all checks concurrently for better performance
    db_check, cerebras_check, trials_check = await asyncio.gather(
        check_database_health(),
        check_cerebras_api_health(),
        check_clinicaltrials_api_health(),
        return_exceptions=True
    )
    
    # Handle any exceptions from gather
    checks = {}
    
    if isinstance(db_check, Exception):
        checks["database"] = ComponentHealth(
            status="unhealthy",
            error=str(db_check),
            last_checked=datetime.now()
        )
    else:
        checks["database"] = db_check
    
    if isinstance(cerebras_check, Exception):
        checks["cerebras_api"] = ComponentHealth(
            status="unhealthy",
            error=str(cerebras_check),
            last_checked=datetime.now()
        )
    else:
        checks["cerebras_api"] = cerebras_check
    
    if isinstance(trials_check, Exception):
        checks["clinicaltrials_api"] = ComponentHealth(
            status="unhealthy",
            error=str(trials_check),
            last_checked=datetime.now()
        )
    else:
        checks["clinicaltrials_api"] = trials_check
    
    return checks


def calculate_overall_status(checks: Dict[str, ComponentHealth]) -> str:
    """
    Calculate overall system status based on component health.
    
    Args:
        checks: Individual component health checks
        
    Returns:
        Overall status (healthy/degraded/unhealthy)
    """
    statuses = [check.status for check in checks.values()]
    
    if all(status == "healthy" for status in statuses):
        return "healthy"
    elif any(status == "unhealthy" for status in statuses):
        return "unhealthy"
    else:
        return "degraded"


@router.get("/", response_model=HealthStatus, summary="Basic health check")
async def health_check() -> HealthStatus:
    """
    Basic health check endpoint.
    
    Returns basic system status without dependency checks.
    Suitable for load balancer health checks.
    """
    uptime = time.time() - _start_time
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=uptime,
        checks={}
    )


@router.get("/ready", response_model=HealthStatus, summary="Readiness probe")
async def readiness_check() -> HealthStatus:
    """
    Readiness probe for Kubernetes deployment.
    
    Checks all critical dependencies and returns detailed health status.
    Returns 503 if any critical component is unhealthy.
    """
    uptime = time.time() - _start_time
    
    # Run all health checks
    checks = await run_all_health_checks()
    overall_status = calculate_overall_status(checks)
    
    # Convert ComponentHealth objects to dictionaries for JSON serialization
    checks_dict = {name: check.dict() for name, check in checks.items()}
    
    health_response = HealthStatus(
        status=overall_status,
        timestamp=datetime.now(),
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=uptime,
        checks=checks_dict
    )
    
    # Return 503 if system is unhealthy
    if overall_status == "unhealthy":
        raise HTTPException(
            status_code=503,
            detail=health_response.dict()
        )
    
    logger.info("Health check completed",
               status=overall_status,
               component_count=len(checks),
               uptime_seconds=uptime)
    
    return health_response


@router.get("/live", summary="Liveness probe")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness probe for Kubernetes deployment.
    
    Simple check to verify the application is running.
    Should only fail if the application is completely broken.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(),
        "uptime_seconds": time.time() - _start_time
    }


@router.get("/metrics", summary="Application metrics")
async def metrics() -> Dict[str, Any]:
    """
    Application metrics endpoint.
    
    Provides basic performance and usage metrics.
    Can be extended for Prometheus monitoring.
    """
    uptime = time.time() - _start_time
    
    # TODO: Add actual metrics from database
    # - Total patients processed
    # - Total trials analyzed
    # - Average matching latency
    # - API call counts and latencies
    
    return {
        "uptime_seconds": uptime,
        "environment": settings.environment,
        "version": settings.app_version,
        "python_version": "3.12+",
        "database_url": settings.database_url.split("://")[0] + "://***",  # Hide credentials
        "api_endpoints": {
            "cerebras": settings.cerebras_base_url,
            "clinicaltrials": settings.clinicaltrials_base_url
        },
        "features": {
            "hipaa_compliance": settings.hipaa_safe_logging,
            "cors_enabled": len(settings.cors_origins) > 0,
            "debug_mode": settings.debug
        }
    }