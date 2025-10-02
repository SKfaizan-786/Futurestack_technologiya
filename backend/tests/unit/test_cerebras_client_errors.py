"""
Unit tests for CerebrasClient error handling scenarios.
Focuses on API timeouts, rate limits, server errors, and custom exceptions.
"""
import pytest
import httpx
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from src.integrations.cerebras_client import (
    CerebrasClient,
    CerebrasAPIError,
    CerebrasAuthenticationError,
    CerebrasRateLimitError,
    CerebrasTimeoutError,
    CerebrasValidationError,
    CerebrasResponse
)


class TestCerebrasClientErrorHandling:
    """Test error handling in CerebrasClient."""
    
    @pytest.fixture
    def client_config(self):
        """Standard client configuration for testing."""
        return {
            "api_key": "test-api-key",
            "base_url": "https://api.cerebras.ai/v1",
            "model": "llama3.1-8b",
            "timeout": 5.0,
            "max_retries": 2
        }
    
    @pytest.fixture
    def patient_data(self):
        """Sample patient data for testing."""
        return {
            "age": 45,
            "gender": "female",
            "medical_history": "diabetes, hypertension",
            "current_medications": ["metformin", "lisinopril"]
        }
    
    @pytest.fixture
    def trial_criteria(self):
        """Sample trial criteria for testing."""
        return {
            "min_age": 18,
            "max_age": 65,
            "conditions": ["diabetes"],
            "exclusions": ["pregnancy"]
        }
    
    def test_client_initialization_missing_api_key(self):
        """Test client raises error when API key is missing."""
        with patch('src.integrations.cerebras_client.settings') as mock_settings:
            mock_settings.cerebras_api_key = None
            mock_settings.cerebras_base_url = "https://api.cerebras.ai/v1"
            mock_settings.cerebras_model = "llama3.1-8b"
            
            with pytest.raises(CerebrasValidationError, match="Cerebras API key is required"):
                CerebrasClient(api_key=None)
    
    def test_client_initialization_empty_api_key(self):
        """Test client raises error when API key is empty."""
        with patch('src.integrations.cerebras_client.settings') as mock_settings:
            mock_settings.cerebras_api_key = ""
            mock_settings.cerebras_base_url = "https://api.cerebras.ai/v1"
            mock_settings.cerebras_model = "llama3.1-8b"
            
            with pytest.raises(CerebrasValidationError, match="Cerebras API key is required"):
                CerebrasClient(api_key="")
    
    @pytest.mark.asyncio
    async def test_authentication_error_401(self, client_config, patient_data, trial_criteria):
        """Test handling of 401 authentication errors."""
        client = CerebrasClient(**client_config)
        
        # Mock 401 response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(CerebrasAuthenticationError, match="Invalid API key"):
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_429_with_retry_after(self, client_config, patient_data, trial_criteria):
        """Test handling of 429 rate limit errors with Retry-After header."""
        client = CerebrasClient(**client_config)
        
        # Mock 429 response with Retry-After header
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.text = "Rate limit exceeded"
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(CerebrasRateLimitError) as exc_info:
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
            
            assert exc_info.value.retry_after == 60
            assert "Rate limit exceeded" in str(exc_info.value)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_429_no_retry_after(self, client_config, patient_data, trial_criteria):
        """Test handling of 429 rate limit errors without Retry-After header."""
        client = CerebrasClient(**client_config)
        
        # Mock 429 response without Retry-After header
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_response.text = "Rate limit exceeded"
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(CerebrasRateLimitError) as exc_info:
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
            
            assert exc_info.value.retry_after == 60  # Default fallback
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_server_error_500_with_retries(self, client_config, patient_data, trial_criteria):
        """Test handling of 500 server errors with retry logic."""
        client = CerebrasClient(**client_config)
        
        # Mock 500 response that persists through retries
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                with pytest.raises(CerebrasAPIError, match="Server error: 500"):
                    await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
                
                # Verify sleep was called for retries (2 retries with exponential backoff)
                assert mock_sleep.call_count == 2
                mock_sleep.assert_any_call(1)  # First retry
                mock_sleep.assert_any_call(2)  # Second retry
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_server_error_502_bad_gateway(self, client_config, patient_data, trial_criteria):
        """Test handling of 502 Bad Gateway errors."""
        client = CerebrasClient(**client_config)
        
        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(CerebrasAPIError, match="Server error: 502"):
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, client_config, patient_data, trial_criteria):
        """Test handling of request timeout errors."""
        client = CerebrasClient(**client_config)
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")
            
            with pytest.raises(CerebrasTimeoutError, match="Request timeout"):
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, client_config, patient_data, trial_criteria):
        """Test handling of connection errors."""
        client = CerebrasClient(**client_config)
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(CerebrasAPIError, match="Request error: Connection failed"):
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_generic_http_error_handling(self, client_config, patient_data, trial_criteria):
        """Test handling of other HTTP errors (4xx)."""
        client = CerebrasClient(**client_config)
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request - Invalid JSON"
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(CerebrasAPIError, match="HTTP 400: Bad Request - Invalid JSON"):
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_malformed_json_response(self, client_config, patient_data, trial_criteria):
        """Test handling of malformed JSON response."""
        client = CerebrasClient(**client_config)
        
        # Mock successful HTTP response but invalid JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(CerebrasAPIError):
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_missing_choices_in_response(self, client_config, patient_data, trial_criteria):
        """Test handling of response missing 'choices' field."""
        client = CerebrasClient(**client_config)
        
        # Mock response without choices
        invalid_response_data = {
            "id": "test-id",
            "usage": {"total_tokens": 100}
            # Missing 'choices' field
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = invalid_response_data
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises((KeyError, IndexError, CerebrasAPIError)):
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, client_config, patient_data, trial_criteria):
        """Test behavior when max retries are exceeded."""
        client = CerebrasClient(**client_config)
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            # Simulate repeated connection errors
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(CerebrasAPIError, match="Request error: Connection failed"):
                await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
            
            # Verify retries were attempted
            assert mock_post.call_count == client.max_retries + 1  # Initial call + retries
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_rate_limit_retry_with_eventual_success(self, client_config, patient_data, trial_criteria):
        """Test that rate limit errors eventually succeed after retry."""
        # Remove max_retries from client_config to avoid conflict
        config = {k: v for k, v in client_config.items() if k != 'max_retries'}
        client = CerebrasClient(max_retries=2, **config)
        
        # Mock first call returns 429, second call succeeds
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
            "usage": {"total_tokens": 100}
        }
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [rate_limit_response, success_response]
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
                
                assert isinstance(result, CerebrasResponse)
                assert result.content == "Success"
                assert mock_post.call_count == 2
        
        await client.close()
    
    @pytest.mark.asyncio 
    async def test_concurrent_request_handling(self, client_config, patient_data, trial_criteria):
        """Test client can handle concurrent requests with rate limiting."""
        client = CerebrasClient(**client_config)
        
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Analysis complete"}}],
            "usage": {"total_tokens": 100}
        }
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = success_response
            
            # Make multiple concurrent requests
            tasks = [
                client.analyze_patient_trial_compatibility(patient_data, trial_criteria)
                for _ in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(isinstance(r, CerebrasResponse) for r in results)
            assert mock_post.call_count == 3
        
        await client.close()


class TestCerebrasClientEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def client_config(self):
        """Standard client configuration for testing."""
        return {
            "api_key": "test-api-key",
            "base_url": "https://api.cerebras.ai/v1",
            "model": "llama3.1-8b",
            "timeout": 5.0,
            "max_retries": 2
        }
    
    @pytest.mark.asyncio
    async def test_empty_patient_data(self):
        """Test handling of empty patient data."""
        client = CerebrasClient(api_key="test-key")
        
        # Mock the API request to avoid actual HTTP calls
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Analysis complete"}}],
            "usage": {"total_tokens": 100}
        }
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = success_response
            
            # Should not raise an error - empty data is valid input
            result = await client.analyze_patient_trial_compatibility({}, {"condition": "diabetes"})
            assert isinstance(result, CerebrasResponse)
        
        await client.close()
    
    @pytest.mark.asyncio 
    async def test_empty_trial_criteria(self):
        """Test handling of empty trial criteria."""
        client = CerebrasClient(api_key="test-key")
        
        # Mock the API request to avoid actual HTTP calls
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Analysis complete"}}],
            "usage": {"total_tokens": 100}
        }
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = success_response
            
            # Should not raise an error - empty criteria is valid input
            result = await client.analyze_patient_trial_compatibility({"age": 45}, {})
            assert isinstance(result, CerebrasResponse)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_very_large_response(self, client_config):
        """Test handling of very large API responses."""
        client = CerebrasClient(**client_config)
        
        # Mock response with very large content
        large_content = "x" * 100000  # 100KB response
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": large_content}}],
            "usage": {"total_tokens": 50000}
        }
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = success_response
            
            result = await client.analyze_patient_trial_compatibility(
                {"age": 45}, {"condition": "diabetes"}
            )
            
            assert len(result.content) == 100000
            assert result.usage["total_tokens"] == 50000
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_context_manager_error_handling(self, client_config):
        """Test error handling within async context manager."""
        async with CerebrasClient(**client_config) as client:
            with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = CerebrasTimeoutError("Timeout")
                
                with pytest.raises(CerebrasTimeoutError):
                    await client.analyze_patient_trial_compatibility(
                        {"age": 45}, {"condition": "diabetes"}
                    )