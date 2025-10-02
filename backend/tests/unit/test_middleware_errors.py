"""
Unit tests for middleware error handling.
Focuses on HTTP error paths, CORS failures, authentication middleware errors.
"""
import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE
)

from src.api.middleware import (
    ErrorResponse,
    HIPAAErrorHandler,
    ErrorHandlingMiddleware
)
from src.integrations.cerebras_client import (
    CerebrasAPIError,
    CerebrasAuthenticationError,
    CerebrasRateLimitError,
    CerebrasTimeoutError,
    CerebrasValidationError
)
from src.integrations.trials_api_client import (
    ClinicalTrialsAPIError,
    ClinicalTrialsRateLimitError,
    ClinicalTrialsValidationError
)


class TestErrorResponse:
    """Test ErrorResponse class."""
    
    def test_error_response_creation(self):
        """Test basic error response creation."""
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test message",
            details="Test details",
            request_id="test-123",
            status_code=HTTP_400_BAD_REQUEST
        )
        
        assert response.error_code == "TEST_ERROR"
        assert response.message == "Test message"
        assert response.details == "Test details"
        assert response.request_id == "test-123"
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert isinstance(response.timestamp, datetime)


class TestHIPAAErrorHandler:
    """Test HIPAA error handler functionality."""
    
    def test_sanitize_error_message_removes_pii(self):
        """Test that PII is removed from error messages."""
        message = "Error for patient John Doe at email john@example.com"
        sanitized = HIPAAErrorHandler.sanitize_error_message(message)
        
        # Should contain redacted placeholders
        assert "REDACTED" in sanitized or "redacted" in sanitized
    
    def test_create_user_friendly_message_authentication(self):
        """Test user-friendly message for authentication errors."""
        message = HIPAAErrorHandler.create_user_friendly_message("authentication", "Invalid API key")
        
        assert "authentication" in message.lower() or "authorized" in message.lower()


class TestErrorHandlingMiddleware:
    """Test ErrorHandlingMiddleware error handling."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance for testing."""
        return ErrorHandlingMiddleware(None)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.request_id = "test-request-123"
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"
        return request
    
    @pytest.mark.asyncio
    async def test_successful_request_passthrough(self, middleware, mock_request):
        """Test that successful requests pass through unchanged."""
        async def mock_call_next(request):
            return Response("Success", status_code=200)
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_http_exception_handling(self, middleware, mock_request):
        """Test handling of FastAPI HTTP exceptions."""
        async def mock_call_next(request):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Not found")
        
        with patch.object(middleware, '_handle_http_exception', new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = JSONResponse({"error": "Not found"}, status_code=404)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            mock_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cerebras_authentication_error(self, middleware, mock_request):
        """Test handling of Cerebras authentication errors."""
        async def mock_call_next(request):
            raise CerebrasAuthenticationError("Invalid API key")
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "auth error"}, status_code=401)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "CEREBRAS_AUTH_ERROR"
            assert error_response.status_code == HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_cerebras_rate_limit_error(self, middleware, mock_request):
        """Test handling of Cerebras rate limit errors."""
        async def mock_call_next(request):
            raise CerebrasRateLimitError("Rate limit exceeded", retry_after=60)
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "rate limit"}, status_code=429)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "CEREBRAS_RATE_LIMIT"
            assert error_response.status_code == HTTP_429_TOO_MANY_REQUESTS
    
    @pytest.mark.asyncio
    async def test_cerebras_timeout_error(self, middleware, mock_request):
        """Test handling of Cerebras timeout errors."""
        async def mock_call_next(request):
            raise CerebrasTimeoutError("Request timeout")
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "timeout"}, status_code=503)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "CEREBRAS_TIMEOUT"
            assert error_response.status_code == HTTP_503_SERVICE_UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_cerebras_validation_error(self, middleware, mock_request):
        """Test handling of Cerebras validation errors."""
        async def mock_call_next(request):
            raise CerebrasValidationError("Invalid input data")
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "validation"}, status_code=400)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "CEREBRAS_VALIDATION_ERROR"
            assert error_response.status_code == HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_cerebras_api_error(self, middleware, mock_request):
        """Test handling of general Cerebras API errors."""
        async def mock_call_next(request):
            raise CerebrasAPIError("API service unavailable")
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "api error"}, status_code=503)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "CEREBRAS_API_ERROR"
            assert error_response.status_code == HTTP_503_SERVICE_UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_clinical_trials_rate_limit_error(self, middleware, mock_request):
        """Test handling of ClinicalTrials.gov rate limit errors."""
        async def mock_call_next(request):
            raise ClinicalTrialsRateLimitError("Rate limit exceeded")
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "rate limit"}, status_code=429)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "CLINICAL_TRIALS_RATE_LIMIT"
            assert error_response.status_code == HTTP_429_TOO_MANY_REQUESTS
    
    @pytest.mark.asyncio
    async def test_clinical_trials_validation_error(self, middleware, mock_request):
        """Test handling of ClinicalTrials.gov validation errors."""
        async def mock_call_next(request):
            raise ClinicalTrialsValidationError("Invalid search criteria")
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "validation"}, status_code=400)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "CLINICAL_TRIALS_VALIDATION_ERROR"
            assert error_response.status_code == HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_clinical_trials_api_error(self, middleware, mock_request):
        """Test handling of general ClinicalTrials.gov API errors."""
        async def mock_call_next(request):
            raise ClinicalTrialsAPIError("Service unavailable")
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "api error"}, status_code=503)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "CLINICAL_TRIALS_API_ERROR"
            assert error_response.status_code == HTTP_503_SERVICE_UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_value_error_handling(self, middleware, mock_request):
        """Test handling of ValueError exceptions."""
        async def mock_call_next(request):
            raise ValueError("Invalid patient data format")
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "validation"}, status_code=400)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "VALIDATION_ERROR"
            assert error_response.status_code == HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_generic_exception_handling(self, middleware, mock_request):
        """Test handling of unexpected exceptions."""
        async def mock_call_next(request):
            raise RuntimeError("Unexpected database error")
        
        with patch.object(middleware, '_create_error_response', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = JSONResponse({"error": "internal"}, status_code=500)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            mock_create.assert_called_once()
            error_response = mock_create.call_args[0][0]
            assert error_response.error_code == "INTERNAL_SERVER_ERROR"
            assert error_response.status_code == HTTP_500_INTERNAL_SERVER_ERROR