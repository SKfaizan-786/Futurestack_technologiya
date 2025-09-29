"""
Main FastAPI application for MedMatch AI.

This module creates the FastAPI application with all necessary middleware,
CORS configuration, and route mounting for clinical trial matching.
"""
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..utils.config import settings
from .health import router as health_router
from .middleware import create_error_handler_middleware
from ..models.base import init_database, db_manager
from ..utils.logging import configure_logging

# Initialize structured logging
configure_logging()
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks like database connections,
    background tasks, and resource cleanup.
    """
    # Startup
    logger.info("Starting MedMatch AI application", 
               version=settings.app_version, environment=settings.environment)
    
    # Initialize database
    await init_database()
    
    # TODO: Start background tasks (trial data sync, etc.)
    # TODO: Warm up AI models if needed
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down MedMatch AI application")
        
        # Close database connections
        await db_manager.close()
        
        # TODO: Stop background tasks
        # TODO: Clean up resources


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered clinical trial matching system for patients and healthcare providers",
        openapi_url=f"{settings.api_prefix}/openapi.json" if not settings.environment == "production" else None,
        docs_url=f"{settings.api_prefix}/docs" if not settings.environment == "production" else None,
        redoc_url=f"{settings.api_prefix}/redoc" if not settings.environment == "production" else None,
        lifespan=lifespan,
        # HIPAA compliance metadata
        openapi_tags=[
            {
                "name": "health",
                "description": "System health and monitoring endpoints"
            },
            {
                "name": "trials",
                "description": "Clinical trial search and retrieval"
            },
            {
                "name": "matching",
                "description": "Patient-trial compatibility analysis"
            },
            {
                "name": "patients",
                "description": "Patient data management (HIPAA-compliant)"
            }
        ],
        openapi_extra={
            "info": {
                "contact": {
                    "name": "MedMatch AI Support",
                    "email": "support@medmatch.ai"
                },
                "license": {
                    "name": "HIPAA Compliant",
                    "url": "https://www.hhs.gov/hipaa"
                }
            },
            "servers": [
                {
                    "url": f"http://localhost:{settings.api_port}",
                    "description": "Development server"
                }
            ]
        }
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"]
    )
    
    # Add trusted host middleware for security
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["medmatch.ai", "*.medmatch.ai", "localhost"]
        )
    
    # Add error handling middleware
    app.add_middleware(create_error_handler_middleware())
    
    # Request/Response middleware for logging and monitoring
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        """
        Middleware for request logging and performance monitoring.
        
        Implements HIPAA-safe logging without exposing patient data.
        """
        # Generate request ID for tracing
        request_id = f"req_{int(time.time() * 1000000)}"
        
        # Start timing
        start_time = time.time()
        
        # Extract safe request information (no patient data)
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url.path),
            "query_params": dict(request.query_params) if request.query_params else None,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        }
        
        # HIPAA-safe logging (no patient data in logs)
        if settings.hipaa_safe_logging:
            # Remove potential PII from query params
            safe_params = {}
            if request_info.get("query_params"):
                for key, value in request_info["query_params"].items():
                    if key.lower() not in ["name", "email", "phone", "ssn", "mrn", "dob"]:
                        safe_params[key] = value
            request_info["query_params"] = safe_params if safe_params else None
        
        logger.info("Request started", **request_info)
        
        # Add request ID to request state for downstream use
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            
            # Log response (HIPAA-safe)
            logger.info("Request completed",
                       request_id=request_id,
                       status_code=response.status_code,
                       response_time=response_time,
                       content_length=response.headers.get("content-length"))
            
            return response
            
        except Exception as e:
            # Calculate response time for errors
            response_time = time.time() - start_time
            
            # Log error (HIPAA-safe)
            logger.error("Request failed",
                        request_id=request_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        response_time=response_time,
                        exc_info=True)
            
            # Return generic error response (no internal details exposed)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "message": "An error occurred processing your request. Please contact support if the issue persists."
                },
                headers={"X-Request-ID": request_id}
            )
    
    # Security headers middleware
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)
        
        # HIPAA-compliant security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
    
    # Mount API routers
    app.include_router(health_router, prefix=f"{settings.api_prefix}/health", tags=["health"])
    
    # TODO: Add remaining routers
    # app.include_router(trials.router, prefix=f"{settings.api_prefix}/trials", tags=["trials"])
    # app.include_router(matching.router, prefix=f"{settings.api_prefix}/match", tags=["matching"])
    # app.include_router(patients.router, prefix=f"{settings.api_prefix}/patients", tags=["patients"])
    
    logger.info("FastAPI application created", 
               title=app.title, version=app.version, environment=settings.environment)
    
    return app


# Create the application instance
app = create_app()


# Development server runner
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
        use_colors=True
    )