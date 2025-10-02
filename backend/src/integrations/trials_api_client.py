"""
ClinicalTrials.gov API v2.0 client for trial data retrieval.
Implements rate limiting, pagination, and data normalization.
"""
import asyncio
import time
import hashlib
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from dataclasses import dataclass, field
from datetime import datetime
import httpx
import structlog
from urllib.parse import urlencode

from ..utils.config import settings

logger = structlog.get_logger(__name__)


class ClinicalTrialsAPIError(Exception):
    """Base exception for ClinicalTrials.gov API errors."""
    pass


class ClinicalTrialsRateLimitError(ClinicalTrialsAPIError):
    """Rate limit exceeded for ClinicalTrials.gov API."""
    pass


class ClinicalTrialsValidationError(ClinicalTrialsAPIError):
    """Validation error for API request parameters."""
    pass


@dataclass
class TrialLocation:
    """Normalized trial location data."""
    facility: str
    city: str
    state: Optional[str]
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass 
class EligibilityCriteria:
    """Normalized eligibility criteria."""
    inclusion: List[str] = field(default_factory=list)
    exclusion: List[str] = field(default_factory=list)
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    sex: str = "All"
    healthy_volunteers: bool = False


@dataclass
class ClinicalTrial:
    """Normalized clinical trial data structure."""
    nct_id: str
    title: str
    brief_title: str
    status: str
    phase: Optional[str]
    study_type: str
    conditions: List[str]
    eligibility_criteria: EligibilityCriteria
    locations: List[TrialLocation]
    last_updated: datetime
    url: str
    sponsor: Optional[str] = None
    description: Optional[str] = None
    
    # For semantic search
    embedding_vector: Optional[List[float]] = None
    search_text: Optional[str] = None


@dataclass
class SearchResults:
    """Paginated search results from ClinicalTrials.gov."""
    trials: List[ClinicalTrial]
    total_count: int
    next_page_token: Optional[str]
    search_params: Dict[str, Any]


class ClinicalTrialsClient:
    """
    Async client for ClinicalTrials.gov API v2.0.
    
    Provides search, retrieval, and normalization of clinical trial data
    with proper rate limiting and pagination handling.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        rate_limit: int = 100,  # requests per minute
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize ClinicalTrials.gov API client.
        
        Args:
            base_url: API base URL (defaults to settings)
            rate_limit: Maximum requests per minute
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.base_url = base_url or settings.clinicaltrials_base_url
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Rate limiting state
        self.request_times: List[float] = []
        self.last_request_time = 0.0
        
        # HTTP client with proper headers
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
        
        logger.info("ClinicalTrials.gov client initialized", 
                   base_url=self.base_url, rate_limit=rate_limit)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting for API requests."""
        now = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.rate_limit:
            # Calculate wait time until oldest request expires
            sleep_time = 60 - (now - self.request_times[0]) + 0.1
            if sleep_time > 0:
                logger.info("Rate limit reached, sleeping", 
                          sleep_time=sleep_time, current_requests=len(self.request_times))
                await asyncio.sleep(sleep_time)
                return await self._enforce_rate_limit()
        
        self.request_times.append(now)
        self.last_request_time = now
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make API request with rate limiting and retries.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            HTTP response object
            
        Raises:
            ClinicalTrialsAPIError: For various API errors
        """
        await self._enforce_rate_limit()
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                response = await self.client.get(endpoint, params=params)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    logger.debug("ClinicalTrials API request successful",
                               endpoint=endpoint, attempt=attempt, 
                               response_time=response_time)
                    return response
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.max_retries:
                        logger.warning("Rate limited, retrying", 
                                     retry_after=retry_after, attempt=attempt)
                        await asyncio.sleep(retry_after)
                        continue
                    raise ClinicalTrialsRateLimitError("Rate limit exceeded after retries")
                elif response.status_code >= 500:
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning("Server error, retrying",
                                     status_code=response.status_code, 
                                     wait_time=wait_time, attempt=attempt)
                        await asyncio.sleep(wait_time)
                        continue
                    raise ClinicalTrialsAPIError(f"Server error: {response.status_code}")
                else:
                    error_text = response.text[:200] if response.text else "No response body"
                    raise ClinicalTrialsAPIError(
                        f"HTTP {response.status_code}: {error_text}"
                    )
                    
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    logger.warning("Request timeout, retrying", attempt=attempt)
                    continue
                raise ClinicalTrialsAPIError("Request timeout after retries")
            except httpx.RequestError as e:
                if attempt < self.max_retries:
                    logger.warning("Request error, retrying", 
                                 error=str(e), attempt=attempt)
                    await asyncio.sleep(1)
                    continue
                raise ClinicalTrialsAPIError(f"Request error: {str(e)}")
        
        raise ClinicalTrialsAPIError("Max retries exceeded")
    
    def _parse_age_range(self, min_age: Optional[str], max_age: Optional[str]) -> tuple:
        """
        Parse age range strings into integers.
        
        Args:
            min_age: Minimum age string (e.g., "18 Years")
            max_age: Maximum age string (e.g., "75 Years")
            
        Returns:
            Tuple of (min_age_int, max_age_int)
        """
        def parse_age_string(age_str: Optional[str]) -> Optional[int]:
            if not age_str:
                return None
            try:
                # Extract number from strings like "18 Years", "6 Months"
                parts = age_str.lower().split()
                if len(parts) >= 2:
                    number = float(parts[0])
                    unit = parts[1]
                    if unit.startswith("year"):
                        return int(number)
                    elif unit.startswith("month"):
                        return int(number / 12)  # Convert months to years
                    elif unit.startswith("day"):
                        return int(number / 365)  # Convert days to years
                return int(float(parts[0]))  # Just a number
            except (ValueError, IndexError):
                return None
        
        return parse_age_string(min_age), parse_age_string(max_age)
    
    def _parse_eligibility_criteria(self, criteria_text: Optional[str]) -> EligibilityCriteria:
        """
        Parse eligibility criteria text into structured format.
        
        Args:
            criteria_text: Raw eligibility criteria text
            
        Returns:
            Structured eligibility criteria
        """
        if not criteria_text:
            return EligibilityCriteria()
        
        inclusion = []
        exclusion = []
        current_section = None
        
        for line in criteria_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Detect section headers
            if 'inclusion' in line.lower():
                current_section = 'inclusion'
                continue
            elif 'exclusion' in line.lower():
                current_section = 'exclusion'
                continue
            
            # Skip section headers and non-criteria lines
            if line.lower().startswith(('inclusion', 'exclusion', 'criteria:')):
                continue
            
            # Parse criteria items (usually start with -, *, or number)
            if any(line.startswith(prefix) for prefix in ['-', '*', '•']) or \
               (line[0].isdigit() and '.' in line[:5]):
                criterion = line.lstrip('-*•0123456789. ').strip()
                if criterion:
                    if current_section == 'inclusion':
                        inclusion.append(criterion)
                    elif current_section == 'exclusion':
                        exclusion.append(criterion)
                    else:
                        # Default to inclusion if section unclear
                        inclusion.append(criterion)
            elif current_section and line:
                # Continuation of previous criterion
                if current_section == 'inclusion' and inclusion:
                    inclusion[-1] += f" {line}"
                elif current_section == 'exclusion' and exclusion:
                    exclusion[-1] += f" {line}"
        
        return EligibilityCriteria(
            inclusion=inclusion,
            exclusion=exclusion
        )
    
    def _normalize_trial_data(self, study_data: Dict[str, Any]) -> ClinicalTrial:
        """
        Normalize raw API response data into ClinicalTrial object.
        
        Args:
            study_data: Raw study data from API
            
        Returns:
            Normalized ClinicalTrial object
        """
        # Defensive check - ensure study_data is a dictionary
        if not isinstance(study_data, dict):
            raise ValueError(f"Expected dict for study_data, got {type(study_data)}: {study_data}")
        
        protocol = study_data.get("protocolSection", {})
        
        # Basic identification
        identification = protocol.get("identificationModule", {})
        nct_id = identification.get("nctId", "")
        brief_title = identification.get("briefTitle", "")
        official_title = identification.get("officialTitle", brief_title)
        
        # Status information
        status_module = protocol.get("statusModule", {})
        status = status_module.get("overallStatus", "Unknown")
        last_update = status_module.get("lastUpdatePostDateStruct", {}).get("date")
        
        # Parse last update date
        last_updated = datetime.now()
        if last_update:
            try:
                last_updated = datetime.strptime(last_update, "%Y-%m-%d")
            except ValueError:
                pass
        
        # Design information
        design = protocol.get("designModule", {})
        study_type = design.get("studyType", "Unknown")
        phases = design.get("phases", [])
        phase = phases[0] if phases else None
        
        # Conditions
        conditions_module = protocol.get("conditionsModule", {})
        conditions = conditions_module.get("conditions", [])
        
        # Eligibility
        eligibility_module = protocol.get("eligibilityModule", {})
        criteria_text = eligibility_module.get("eligibilityCriteria", "")
        eligibility = self._parse_eligibility_criteria(criteria_text)
        
        # Update age range from API data
        min_age, max_age = self._parse_age_range(
            eligibility_module.get("minimumAge"),
            eligibility_module.get("maximumAge")
        )
        eligibility.age_min = min_age
        eligibility.age_max = max_age
        eligibility.sex = eligibility_module.get("sex", "All")
        eligibility.healthy_volunteers = eligibility_module.get("healthyVolunteers", False)
        
        # Locations
        contacts_locations = protocol.get("contactsLocationsModule", {})
        location_data = contacts_locations.get("locations", [])
        locations = []
        
        for loc in location_data:
            location = TrialLocation(
                facility=loc.get("facility", ""),
                city=loc.get("city", ""),
                state=loc.get("state"),
                country=loc.get("country", ""),
                # Note: lat/lon not provided by API, would need geocoding
            )
            locations.append(location)
        
        # Sponsor information
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        lead_sponsor = sponsor_module.get("leadSponsor", {})
        sponsor = lead_sponsor.get("name")
        
        # Description
        description_module = protocol.get("descriptionModule", {})
        description = description_module.get("briefSummary", {}).get("textMd")
        
        # Generate search text for semantic search
        search_components = [
            brief_title,
            official_title,
            " ".join(conditions),
            criteria_text,
            description or ""
        ]
        search_text = " ".join(filter(None, search_components))
        
        return ClinicalTrial(
            nct_id=nct_id,
            title=official_title,
            brief_title=brief_title,
            status=status,
            phase=phase,
            study_type=study_type,
            conditions=conditions,
            eligibility_criteria=eligibility,
            locations=locations,
            last_updated=last_updated,
            url=f"https://clinicaltrials.gov/study/{nct_id}",
            sponsor=sponsor,
            description=description,
            search_text=search_text
        )
    
    async def search_trials(
        self,
        conditions: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        status_filter: Optional[List[str]] = None,
        location: Optional[Dict[str, Any]] = None,
        age_range: Optional[tuple] = None,
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> SearchResults:
        """
        Search for clinical trials with filtering.
        
        Args:
            conditions: Medical conditions to search for
            keywords: Keywords to search in title/description
            status_filter: Trial statuses to include
            location: Geographic filter {"lat": float, "lon": float, "radius_miles": int}
            age_range: Age range tuple (min_age, max_age)
            page_size: Number of results per page (max 1000)
            page_token: Token for pagination
            
        Returns:
            Search results with trials and pagination info
        """
        params = {
            "format": "json",
            "pageSize": min(page_size, 1000)  # API limit
        }
        
        # Build query string for ClinicalTrials.gov API v2.0
        query_parts = []
        
        if conditions:
            for condition in conditions:
                # Use simpler query format that's more likely to work
                query_parts.append(condition)
        
        if keywords:
            for keyword in keywords:
                # Use simpler query format
                query_parts.append(keyword)
        
        if query_parts:
            # Use query.term instead of query.cond for API v2
            params["query.term"] = " AND ".join(f'"{part}"' for part in query_parts)
        
        # Status filtering
        if status_filter:
            # Ensure comma-separated format for API
            if isinstance(status_filter, list):
                params["filter.overallStatus"] = ",".join(status_filter)
            else:
                params["filter.overallStatus"] = status_filter
        # Temporarily disable default status filter to fix API parameter errors
        # The correct status values need to be researched from ClinicalTrials.gov API documentation
        # else:
        #     # Default to actively recruiting trials
        #     params["filter.overallStatus"] = ",".join([
        #         "Recruiting", "Not yet recruiting", "Active, not recruiting"
        #     ])
        
        # Geographic filtering
        if location:
            lat = location.get("lat")
            lon = location.get("lon") 
            radius_miles = location.get("radius_miles", 100)
            if lat is not None and lon is not None:
                params["filter.geo"] = f"distance({lat},{lon},{radius_miles}mi)"
        
        # Age filtering (handled post-processing since API doesn't support direct age filter)
        
        # Pagination
        if page_token:
            params["pageToken"] = page_token
        
        # Debug logging
        logger.info(f"API request parameters: {params}")
        
        # Make request
        response = await self._make_request("/studies", params)
        data = response.json()
        
        # Parse results
        studies = data.get("studies", [])
        total_count = data.get("totalCount", 0)
        next_page_token = data.get("nextPageToken")
        
        # Normalize trial data
        trials = []
        for study in studies:
            try:
                trial = self._normalize_trial_data(study)
                
                # Apply age filtering if specified
                if age_range:
                    min_age, max_age = age_range
                    trial_min = trial.eligibility_criteria.age_min
                    trial_max = trial.eligibility_criteria.age_max
                    
                    # Skip if age ranges don't overlap
                    if trial_min and max_age and trial_min > max_age:
                        continue
                    if trial_max and min_age and trial_max < min_age:
                        continue
                
                trials.append(trial)
                
            except Exception as e:
                logger.warning("Failed to normalize trial data", 
                             nct_id=study.get("protocolSection", {}).get("identificationModule", {}).get("nctId"),
                             error=str(e))
                continue
        
        logger.info("Trial search completed",
                   total_results=len(trials), total_count=total_count,
                   has_next_page=bool(next_page_token))
        
        return SearchResults(
            trials=trials,
            total_count=total_count,
            next_page_token=next_page_token,
            search_params=params
        )
    
    async def get_trial_details(self, nct_id: str) -> Optional[ClinicalTrial]:
        """
        Get detailed information for a specific trial.
        
        Args:
            nct_id: NCT identifier for the trial
            
        Returns:
            Detailed trial information or None if not found
        """
        try:
            response = await self._make_request(f"/studies/{nct_id}")
            data = response.json()
            
            studies = data.get("studies", [])
            if not studies:
                return None
            
            return self._normalize_trial_data(studies[0])
            
        except ClinicalTrialsAPIError as e:
            if "404" in str(e):
                return None
            raise
    
    async def search_trials_for_patient(
        self,
        patient_data: Dict[str, Any],
        max_distance_miles: int = 100,
        max_results: int = 50
    ) -> List[ClinicalTrial]:
        """
        Search for trials relevant to a specific patient.
        
        Args:
            patient_data: Patient medical information
            max_distance_miles: Maximum distance for location filtering
            max_results: Maximum number of trials to return
            
        Returns:
            List of relevant trials for the patient
        """
        # Extract search parameters from patient data
        conditions = patient_data.get("conditions", [])
        age = patient_data.get("age")
        location = patient_data.get("location", {})
        
        # Build location filter
        location_filter = None
        if "latitude" in location and "longitude" in location:
            location_filter = {
                "lat": location["latitude"],
                "lon": location["longitude"], 
                "radius_miles": max_distance_miles
            }
        
        # Build age range (±5 years for flexibility)
        age_range = None
        if age:
            age_range = (max(0, age - 5), age + 5)
        
        # Search trials
        all_trials = []
        page_token = None
        
        while len(all_trials) < max_results:
            results = await self.search_trials(
                conditions=conditions,
                location=location_filter,
                age_range=age_range,
                page_size=min(100, max_results - len(all_trials)),
                page_token=page_token
            )
            
            all_trials.extend(results.trials)
            
            if not results.next_page_token or len(all_trials) >= max_results:
                break
                
            page_token = results.next_page_token
        
        return all_trials[:max_results]