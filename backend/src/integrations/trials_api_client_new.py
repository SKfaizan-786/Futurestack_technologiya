"""
ClinicalTrials.gov API client using pytrials library.
Implements search functionality with real trial data retrieval.
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import structlog
from pytrials.client import ClinicalTrials as PyTrialsClient

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
    ClinicalTrials.gov client using pytrials library.
    
    Provides search and retrieval of clinical trial data without API blocking issues.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        rate_limit: int = 100,  # requests per minute
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize ClinicalTrials.gov client with pytrials.
        
        Args:
            base_url: Ignored - pytrials handles URLs
            rate_limit: Ignored - pytrials handles rate limiting
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize pytrials client
        self.client = PyTrialsClient()
        
        logger.info("ClinicalTrials.gov client initialized with pytrials", 
                   timeout=timeout, max_retries=max_retries)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    async def close(self):
        """Close the client (no-op for pytrials)."""
        pass
    
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
                parts = str(age_str).lower().split()
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
            study_data: Raw study data from pytrials
            
        Returns:
            Normalized ClinicalTrial object
        """
        # Defensive check - ensure study_data is a dictionary
        if not isinstance(study_data, dict):
            raise ValueError(f"Expected dict for study_data, got {type(study_data)}: {study_data}")
        
        protocol = study_data.get("ProtocolSection", {})
        
        # Basic identification
        identification = protocol.get("IdentificationModule", {})
        nct_id = identification.get("NCTId", "")
        brief_title = identification.get("BriefTitle", "")
        official_title = identification.get("OfficialTitle", brief_title)
        
        # Status information
        status_module = protocol.get("StatusModule", {})
        status = status_module.get("OverallStatus", "Unknown")
        last_update = status_module.get("LastUpdatePostDateStruct", {}).get("LastUpdatePostDate")
        
        # Parse last update date
        last_updated = datetime.now()
        if last_update:
            try:
                last_updated = datetime.strptime(last_update, "%B %d, %Y")
            except ValueError:
                try:
                    last_updated = datetime.strptime(last_update, "%Y-%m-%d")
                except ValueError:
                    pass
        
        # Design information
        design = protocol.get("DesignModule", {})
        study_type = design.get("StudyType", "Unknown")
        phases = design.get("PhaseList", {}).get("Phase", [])
        phase = phases[0] if phases else None
        
        # Conditions
        conditions_module = protocol.get("ConditionsModule", {})
        conditions = conditions_module.get("ConditionList", {}).get("Condition", [])
        
        # Eligibility
        eligibility_module = protocol.get("EligibilityModule", {})
        criteria_text = eligibility_module.get("EligibilityCriteria", "")
        eligibility = self._parse_eligibility_criteria(criteria_text)
        
        # Update age range from API data
        min_age, max_age = self._parse_age_range(
            eligibility_module.get("MinimumAge"),
            eligibility_module.get("MaximumAge")
        )
        eligibility.age_min = min_age
        eligibility.age_max = max_age
        eligibility.sex = eligibility_module.get("Gender", "All")
        eligibility.healthy_volunteers = eligibility_module.get("HealthyVolunteers", "No") == "Yes"
        
        # Locations
        contacts_locations = protocol.get("ContactsLocationsModule", {})
        location_data = contacts_locations.get("LocationList", {}).get("Location", [])
        locations = []
        
        for loc in location_data:
            location = TrialLocation(
                facility=loc.get("LocationFacility", ""),
                city=loc.get("LocationCity", ""),
                state=loc.get("LocationState"),
                country=loc.get("LocationCountry", ""),
                # Note: lat/lon not provided by API, would need geocoding
            )
            locations.append(location)
        
        # Sponsor information
        sponsor_module = protocol.get("SponsorCollaboratorsModule", {})
        lead_sponsor = sponsor_module.get("LeadSponsor", {})
        sponsor = lead_sponsor.get("LeadSponsorName")
        
        # Description
        description_module = protocol.get("DescriptionModule", {})
        description = description_module.get("BriefSummary", {}).get("BriefSummary")
        
        # Generate search text for semantic search
        search_components = [
            brief_title,
            official_title,
            " ".join(conditions) if isinstance(conditions, list) else str(conditions),
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
            conditions=conditions if isinstance(conditions, list) else [conditions] if conditions else [],
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
        Search for clinical trials with filtering using pytrials.
        
        Args:
            conditions: Medical conditions to search for
            keywords: Keywords to search in title/description
            status_filter: Trial statuses to include
            location: Geographic filter (not implemented in pytrials)
            age_range: Age range tuple (min_age, max_age)
            page_size: Number of results per page (max 1000)
            page_token: Token for pagination (not implemented in pytrials)
            
        Returns:
            Search results with trials and pagination info
        """
        # Build search expression for pytrials
        search_expr_parts = []
        
        if conditions:
            # Use the primary condition for search
            primary_condition = conditions[0]
            search_expr_parts.append(f"AREA[Condition]{primary_condition}")
        
        if keywords:
            for keyword in keywords:
                search_expr_parts.append(f"AREA[OtherTerm]{keyword}")
        
        # Default to a general search if no conditions/keywords
        if not search_expr_parts:
            search_expr_parts.append("AREA[Condition]cancer")
        
        search_expr = " OR ".join(search_expr_parts)
        
        # Status filtering (convert to pytrials format)
        status_mapping = {
            "RECRUITING": "Recruiting",
            "NOT_YET_RECRUITING": "Not yet recruiting", 
            "ACTIVE_NOT_RECRUITING": "Active, not recruiting",
            "COMPLETED": "Completed",
            "TERMINATED": "Terminated"
        }
        
        if status_filter:
            status_parts = []
            for status in status_filter:
                mapped_status = status_mapping.get(status.upper(), status)
                status_parts.append(f"AREA[OverallStatus]{mapped_status}")
            if status_parts:
                search_expr += " AND (" + " OR ".join(status_parts) + ")"
        
        logger.info(f"PyTrials search expression: {search_expr}")
        logger.info(f"Requesting max {page_size} studies")
        
        try:
            # Use pytrials to get studies
            studies = self.client.get_full_studies(
                search_expr=search_expr,
                max_studies=min(page_size, 1000)
            )
            
            logger.info(f"PyTrials returned {len(studies)} studies")
            
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
                                 nct_id=study.get("ProtocolSection", {}).get("IdentificationModule", {}).get("NCTId"),
                                 error=str(e))
                    continue
            
            logger.info("Trial search completed",
                       total_results=len(trials), 
                       normalized_successfully=len(trials))
            
            return SearchResults(
                trials=trials,
                total_count=len(trials),
                next_page_token=None,  # pytrials doesn't support pagination tokens
                search_params={"search_expr": search_expr, "max_studies": page_size}
            )
            
        except Exception as e:
            logger.error("PyTrials search failed", error=str(e))
            raise ClinicalTrialsAPIError(f"PyTrials search failed: {str(e)}")
    
    async def get_trial_details(self, nct_id: str) -> Optional[ClinicalTrial]:
        """
        Get detailed information for a specific trial.
        
        Args:
            nct_id: NCT identifier for the trial
            
        Returns:
            Detailed trial information or None if not found
        """
        try:
            search_expr = f"AREA[NCTId]{nct_id}"
            studies = self.client.get_full_studies(search_expr=search_expr, max_studies=1)
            
            if not studies:
                return None
            
            return self._normalize_trial_data(studies[0])
            
        except Exception as e:
            logger.error("Failed to get trial details", nct_id=nct_id, error=str(e))
            return None
    
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
            max_distance_miles: Maximum distance for location filtering (not implemented)
            max_results: Maximum number of trials to return
            
        Returns:
            List of relevant trials for the patient
        """
        # Extract search parameters from patient data
        conditions = patient_data.get("conditions", [])
        age = patient_data.get("age")
        
        # Build age range (±5 years for flexibility)
        age_range = None
        if age:
            age_range = (max(0, age - 5), age + 5)
        
        # Search trials
        results = await self.search_trials(
            conditions=conditions,
            age_range=age_range,
            page_size=max_results
        )
        
        return results.trials[:max_results]