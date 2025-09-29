"""
Cerebras API client for LLM-powered medical reasoning.
Implements Chain-of-Thought prompting for clinical trial matching.
"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
import structlog

from ..utils.config import settings

logger = structlog.get_logger(__name__)


class CerebrasAPIError(Exception):
    """Base exception for Cerebras API errors."""
    pass


class CerebrasAuthenticationError(CerebrasAPIError):
    """Authentication failed with Cerebras API."""
    pass


class CerebrasRateLimitError(CerebrasAPIError):
    """Rate limit exceeded for Cerebras API."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class CerebrasTimeoutError(CerebrasAPIError):
    """Request timeout for Cerebras API."""
    pass


class CerebrasValidationError(CerebrasAPIError):
    """Validation error for Cerebras API request."""
    pass


@dataclass
class CerebrasResponse:
    """Structured response from Cerebras API."""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    response_time: float
    request_id: Optional[str] = None


@dataclass
class RateLimiter:
    """Simple rate limiter for API requests."""
    requests_per_minute: int
    requests: List[float]
    
    def __post_init__(self):
        self.requests = []
    
    async def acquire(self) -> None:
        """Acquire rate limit token, blocking if necessary."""
        now = time.time()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        if len(self.requests) >= self.requests_per_minute:
            # Wait until oldest request expires
            sleep_time = 60 - (now - self.requests[0]) + 0.1
            if sleep_time > 0:
                logger.info("Rate limit reached, sleeping", sleep_time=sleep_time)
                await asyncio.sleep(sleep_time)
                return await self.acquire()
        
        self.requests.append(now)


class CerebrasClient:
    """
    Async client for Cerebras Inference API.
    
    Provides LLM-powered medical reasoning with Chain-of-Thought prompting
    for clinical trial patient matching.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit: int = 60  # requests per minute
    ):
        """
        Initialize Cerebras API client.
        
        Args:
            api_key: Cerebras API key (defaults to settings)
            base_url: API base URL (defaults to settings)
            model: Model name (defaults to settings)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limit: Maximum requests per minute
        """
        self.api_key = api_key or settings.cerebras_api_key
        self.base_url = base_url or settings.cerebras_base_url
        self.model = model or settings.cerebras_model
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            raise CerebrasValidationError("Cerebras API key is required")
        
        self.rate_limiter = RateLimiter(rate_limit, [])
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info("Cerebras client initialized", 
                   model=self.model, base_url=self.base_url)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _build_medical_reasoning_prompt(
        self,
        patient_data: Dict[str, Any],
        trial_criteria: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Build Chain-of-Thought prompt for medical reasoning.
        
        Args:
            patient_data: Sanitized patient information
            trial_criteria: Clinical trial eligibility criteria
            system_prompt: Custom system prompt (optional)
            
        Returns:
            List of messages for API request
        """
        if system_prompt is None:
            system_prompt = """You are a medical AI assistant specializing in clinical trial matching. 

Your task is to analyze patient eligibility for clinical trials using step-by-step reasoning.

INSTRUCTIONS:
1. Compare patient data against trial criteria systematically
2. Provide clear PASS/FAIL assessment for each criterion
3. Calculate overall compatibility percentage (0-100%)
4. Explain your reasoning step-by-step
5. Highlight any areas requiring human verification
6. Maintain HIPAA compliance - never include PII in responses

FORMAT YOUR RESPONSE AS:
COMPATIBILITY ASSESSMENT: [X]% Match

STEP-BY-STEP REASONING:
[Detailed analysis of each criterion]

RECOMMENDATION: [Clear recommendation]
NEXT STEPS: [Any required follow-up]"""

        # Sanitize patient data (remove any PII)
        safe_patient_data = self._sanitize_patient_data(patient_data)
        
        user_prompt = f"""
PATIENT PROFILE:
{json.dumps(safe_patient_data, indent=2)}

TRIAL ELIGIBILITY CRITERIA:
{json.dumps(trial_criteria, indent=2)}

Please analyze the compatibility between this patient and trial criteria.
"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _sanitize_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove PII from patient data for HIPAA compliance.
        
        Args:
            patient_data: Raw patient data
            
        Returns:
            Sanitized patient data safe for API transmission
        """
        # Define fields that are safe to include
        safe_fields = {
            "age", "gender", "conditions", "medications", 
            "medical_history", "lab_values", "allergies",
            "smoking_status", "alcohol_use"
        }
        
        # Fields that should be excluded (contain PII)
        pii_fields = {
            "name", "first_name", "last_name", "ssn", "mrn",
            "email", "phone", "address", "date_of_birth",
            "insurance", "emergency_contact"
        }
        
        sanitized = {}
        for key, value in patient_data.items():
            if key in pii_fields:
                continue  # Skip PII fields
            elif key in safe_fields:
                sanitized[key] = value
            elif key == "location":
                # Include only city/state, not full address
                if isinstance(value, dict):
                    sanitized["location"] = {
                        k: v for k, v in value.items() 
                        if k in ["city", "state", "country"]
                    }
        
        return sanitized
    
    async def _make_request(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        stream: bool = False
    ) -> httpx.Response:
        """
        Make API request with rate limiting and retries.
        
        Args:
            messages: Chat messages for API
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0-1.0)
            stream: Whether to stream response
            
        Returns:
            HTTP response object
            
        Raises:
            CerebrasAPIError: For various API errors
        """
        await self.rate_limiter.acquire()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or settings.cerebras_max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                response = await self.client.post("/chat/completions", json=payload)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    logger.info("Cerebras API request successful",
                              attempt=attempt, response_time=response_time)
                    return response
                elif response.status_code == 401:
                    raise CerebrasAuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.max_retries:
                        await asyncio.sleep(retry_after)
                        continue
                    raise CerebrasRateLimitError(
                        "Rate limit exceeded", retry_after=retry_after
                    )
                elif response.status_code >= 500:
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        await asyncio.sleep(wait_time)
                        continue
                    raise CerebrasAPIError(f"Server error: {response.status_code}")
                else:
                    raise CerebrasAPIError(f"HTTP {response.status_code}: {response.text}")
                    
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    continue
                raise CerebrasTimeoutError("Request timeout")
            except httpx.RequestError as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
                    continue
                raise CerebrasAPIError(f"Request error: {str(e)}")
        
        raise CerebrasAPIError("Max retries exceeded")
    
    async def analyze_patient_trial_compatibility(
        self,
        patient_data: Dict[str, Any],
        trial_criteria: Dict[str, Any],
        custom_prompt: Optional[str] = None
    ) -> CerebrasResponse:
        """
        Analyze patient-trial compatibility using LLM reasoning.
        
        Args:
            patient_data: Patient medical information
            trial_criteria: Trial eligibility criteria
            custom_prompt: Optional custom system prompt
            
        Returns:
            Structured response with compatibility analysis
            
        Raises:
            CerebrasAPIError: For various API errors
        """
        messages = self._build_medical_reasoning_prompt(
            patient_data, trial_criteria, custom_prompt
        )
        
        start_time = time.time()
        response = await self._make_request(messages)
        response_time = time.time() - start_time
        
        try:
            data = response.json()
            choice = data["choices"][0]
            
            return CerebrasResponse(
                content=choice["message"]["content"],
                usage=data.get("usage", {}),
                model=data.get("model", self.model),
                finish_reason=choice.get("finish_reason", "unknown"),
                response_time=response_time,
                request_id=response.headers.get("x-request-id")
            )
            
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise CerebrasAPIError(f"Invalid response format: {str(e)}")
    
    async def batch_analyze_trials(
        self,
        patient_data: Dict[str, Any],
        trials: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[CerebrasResponse]:
        """
        Analyze patient compatibility with multiple trials concurrently.
        
        Args:
            patient_data: Patient medical information
            trials: List of trial criteria
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of analysis responses in same order as input trials
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_single_trial(trial_criteria: Dict[str, Any]) -> CerebrasResponse:
            async with semaphore:
                return await self.analyze_patient_trial_compatibility(
                    patient_data, trial_criteria
                )
        
        tasks = [analyze_single_trial(trial) for trial in trials]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Batch analysis error", error=str(result))
                # Create error response
                error_response = CerebrasResponse(
                    content=f"Analysis failed: {str(result)}",
                    usage={},
                    model=self.model,
                    finish_reason="error",
                    response_time=0.0
                )
                processed_results.append(error_response)
            else:
                processed_results.append(result)
        
        return processed_results