"""
HIPAA-compliant error handling middleware for MedMatch AI.

Provides global exception handling, error sanitization,
and standardized error responses without exposing sensitive information.
"""
import time
from typing import Any, Dict, Optional, Union
from datetime import datetime
import structlog
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE
)

from ..integrations.cerebras_client import (
    CerebrasAPIError, 
    CerebrasAuthenticationError,
    CerebrasRateLimitError,
    CerebrasTimeoutError,
    CerebrasValidationError
)
from ..integrations.trials_api_client import (
    ClinicalTrialsAPIError,
    ClinicalTrialsRateLimitError,
    ClinicalTrialsValidationError
)
from ..utils.config import settings
from ..utils.logging import get_logger, log_patient_access

logger = get_logger(__name__)


class ErrorResponse:
    """Standardized error response format."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[str] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.request_id = request_id
        self.timestamp = timestamp or datetime.now()
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary."""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "timestamp": self.timestamp.isoformat()
            }
        }
        
        if self.details and settings.environment != "production":
            response["error"]["details"] = self.details
        
        if self.request_id:
            response["request_id"] = self.request_id
        
        return response


class HIPAAErrorHandler:
    """HIPAA-compliant error handler with PII sanitization."""
    
    @staticmethod
    def sanitize_error_message(error_message: str) -> str:
        """
        Remove potential PII from error messages.
        
        Args:
            error_message: Original error message
            
        Returns:
            Sanitized error message
        """
        if not settings.hipaa_safe_logging:
            return error_message
        
        # Common PII patterns to remove
        import re
        
        # Email addresses
        error_message = re.sub(r'\S+@\S+\.\S+', '[EMAIL_REDACTED]', error_message)
        
        # Phone numbers (various formats)
        error_message = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', error_message)
        
        # SSN patterns
        error_message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', error_message)
        
        # Credit card patterns
        error_message = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_REDACTED]', error_message)
        
        # Generic number sequences that might be sensitive
        error_message = re.sub(r'\b\d{9,}\b', '[ID_REDACTED]', error_message)
        
        return error_message
    
    @staticmethod
    def create_user_friendly_message(error_type: str, original_message: str) -> str:
        """
        Create user-friendly error messages for different error types.
        
        Args:
            error_type: Type of error
            original_message: Original error message
            
        Returns:
            User-friendly error message
        """
        user_messages = {
            "validation": "The provided information is invalid. Please check your input and try again.",
            "authentication": "Authentication failed. Please check your credentials.",
            "authorization": "You don't have permission to access this resource.",
            "not_found": "The requested resource was not found.",
            "rate_limit": "Too many requests. Please wait before trying again.",
            "timeout": "The request timed out. Please try again later.",
            "service_unavailable": "The service is temporarily unavailable. Please try again later.",
            "database": "A database error occurred. Please contact support if the issue persists.",
            "external_api": "An error occurred while communicating with external services. Please try again later.",
            "internal": "An internal error occurred. Please contact support if the issue persists."
        }
        
        return user_messages.get(error_type, user_messages["internal"])


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware.
    
    Catches all unhandled exceptions and converts them to
    standardized, HIPAA-compliant error responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process requests and handle errors.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware in chain
            
        Returns:
            Response with error handling applied
        """
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', None)
        
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(e, request, request_id)
            
        except CerebrasAuthenticationError as e:
            # Handle Cerebras authentication errors
            error_response = ErrorResponse(
                error_code="CEREBRAS_AUTH_ERROR",
                message=HIPAAErrorHandler.create_user_friendly_message("authentication", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)),
                request_id=request_id,
                status_code=HTTP_401_UNAUTHORIZED
            )
            return await self._create_error_response(error_response, request, start_time)
            
        except CerebrasRateLimitError as e:
            # Handle Cerebras rate limiting
            error_response = ErrorResponse(
                error_code="CEREBRAS_RATE_LIMIT",
                message=HIPAAErrorHandler.create_user_friendly_message("rate_limit", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)),
                request_id=request_id,
                status_code=HTTP_429_TOO_MANY_REQUESTS
            )
            return await self._create_error_response(error_response, request, start_time)
            
        except CerebrasTimeoutError as e:
            # Handle Cerebras timeouts
            error_response = ErrorResponse(
                error_code="CEREBRAS_TIMEOUT",
                message=HIPAAErrorHandler.create_user_friendly_message("timeout", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)),
                request_id=request_id,
                status_code=HTTP_503_SERVICE_UNAVAILABLE
            )
            return await self._create_error_response(error_response, request, start_time)
            
        except CerebrasValidationError as e:
            # Handle Cerebras validation errors
            error_response = ErrorResponse(
                error_code="CEREBRAS_VALIDATION_ERROR",
                message=HIPAAErrorHandler.create_user_friendly_message("validation", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)),
                request_id=request_id,
                status_code=HTTP_400_BAD_REQUEST
            )
            return await self._create_error_response(error_response, request, start_time)
            
        except CerebrasAPIError as e:
            # Handle general Cerebras API errors
            error_response = ErrorResponse(
                error_code="CEREBRAS_API_ERROR",
                message=HIPAAErrorHandler.create_user_friendly_message("external_api", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)),
                request_id=request_id,
                status_code=HTTP_503_SERVICE_UNAVAILABLE
            )
            return await self._create_error_response(error_response, request, start_time)
            
        except ClinicalTrialsRateLimitError as e:
            # Handle ClinicalTrials.gov rate limiting
            error_response = ErrorResponse(
                error_code="CLINICAL_TRIALS_RATE_LIMIT",
                message=HIPAAErrorHandler.create_user_friendly_message("rate_limit", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)),
                request_id=request_id,
                status_code=HTTP_429_TOO_MANY_REQUESTS
            )
            return await self._create_error_response(error_response, request, start_time)
            
        except ClinicalTrialsValidationError as e:
            # Handle ClinicalTrials.gov validation errors
            error_response = ErrorResponse(
                error_code="CLINICAL_TRIALS_VALIDATION_ERROR",
                message=HIPAAErrorHandler.create_user_friendly_message("validation", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)),
                request_id=request_id,
                status_code=HTTP_400_BAD_REQUEST
            )
            return await self._create_error_response(error_response, request, start_time)
            
        except ClinicalTrialsAPIError as e:
            # Handle general ClinicalTrials.gov API errors
            error_response = ErrorResponse(
                error_code="CLINICAL_TRIALS_API_ERROR",
                message=HIPAAErrorHandler.create_user_friendly_message("external_api", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)),
                request_id=request_id,
                status_code=HTTP_503_SERVICE_UNAVAILABLE
            )
            return await self._create_error_response(error_response, request, start_time)
            
        except ValueError as e:
            # Handle validation errors
            error_response = ErrorResponse(
                error_code="VALIDATION_ERROR",
                message=HIPAAErrorHandler.create_user_friendly_message("validation", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)),
                request_id=request_id,
                status_code=HTTP_400_BAD_REQUEST
            )
            return await self._create_error_response(error_response, request, start_time)
            
        except Exception as e:
            # Handle all other unexpected errors
            error_response = ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                message=HIPAAErrorHandler.create_user_friendly_message("internal", str(e)),
                details=HIPAAErrorHandler.sanitize_error_message(str(e)) if settings.environment != "production" else None,
                request_id=request_id,
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
            return await self._create_error_response(error_response, request, start_time)
    
    async def _handle_http_exception(
        self, 
        exc: HTTPException, 
        request: Request, 
        request_id: Optional[str]
    ) -> JSONResponse:
        """
        Handle FastAPI HTTP exceptions.
        
        Args:
            exc: HTTP exception
            request: Request object
            request_id: Request identifier
            
        Returns:
            JSON error response
        """
        # Map HTTP status codes to error types
        error_type_map = {
            HTTP_400_BAD_REQUEST: "validation",
            HTTP_401_UNAUTHORIZED: "authentication",
            HTTP_403_FORBIDDEN: "authorization",
            HTTP_404_NOT_FOUND: "not_found",
            HTTP_422_UNPROCESSABLE_ENTITY: "validation",
            HTTP_429_TOO_MANY_REQUESTS: "rate_limit",
            HTTP_500_INTERNAL_SERVER_ERROR: "internal",
            HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable"
        }
        
        error_type = error_type_map.get(exc.status_code, "internal")
        
        error_response = ErrorResponse(
            error_code=f"HTTP_{exc.status_code}",
            message=HIPAAErrorHandler.create_user_friendly_message(error_type, exc.detail),
            details=HIPAAErrorHandler.sanitize_error_message(exc.detail) if hasattr(exc, 'detail') else None,
            request_id=request_id,
            status_code=exc.status_code
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.to_dict(),
            headers={"X-Request-ID": request_id} if request_id else None
        )
    
    async def _create_error_response(
        self,
        error_response: ErrorResponse,
        request: Request,
        start_time: float
    ) -> JSONResponse:
        """
        Create standardized error response with logging.
        
        Args:
            error_response: Error response object
            request: Request object
            start_time: Request start time
            
        Returns:
            JSON error response
        """
        response_time = time.time() - start_time
        
        # Log error with sanitized information
        log_data = {
            "error_code": error_response.error_code,
            "status_code": error_response.status_code,
            "request_path": request.url.path,
            "request_method": request.method,
            "response_time_ms": response_time * 1000,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        }
        
        if error_response.request_id:
            log_data["request_id"] = error_response.request_id
        
        # Log with appropriate level based on error severity
        if error_response.status_code >= 500:
            logger.error("Internal server error", **log_data, exc_info=True)
        elif error_response.status_code >= 400:
            logger.warning("Client error", **log_data)
        
        # Create response
        response = JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
        
        # Add response headers
        if error_response.request_id:
            response.headers["X-Request-ID"] = error_response.request_id
        
        response.headers["X-Response-Time"] = f"{response_time:.3f}s"
        
        return response


def create_error_handler_middleware() -> ErrorHandlingMiddleware:
    """
    Create error handling middleware instance.
    
    Returns:
        Configured error handling middleware
    """
    return ErrorHandlingMiddleware()