"""
Trial model with vector embeddings support for semantic search.

This model represents clinical trial data with AI-powered semantic search
capabilities and structured eligibility criteria processing.
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, Float
from sqlalchemy.orm import declarative_base
import re
import json

# Import AI pipeline services
from ..services.hybrid_search import VectorEmbeddings

Base = declarative_base()


class TrialDB(Base):
    """SQLAlchemy Trial model for database persistence."""
    
    __tablename__ = "trials"
    
    nct_id = Column(String(20), primary_key=True)
    title = Column(Text, nullable=False)
    brief_summary = Column(Text, nullable=False)
    detailed_description = Column(Text, nullable=True)
    primary_purpose = Column(String(100), nullable=False)
    phase = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False)
    enrollment = Column(Integer, nullable=True)
    estimated_enrollment = Column(Integer, nullable=True)
    study_type = Column(String(50), nullable=False)
    sponsor = Column(String(500), nullable=True)
    location = Column(String(500), nullable=True)
    
    # JSON fields for complex data
    conditions = Column(JSON, nullable=False, default=[])
    interventions = Column(JSON, nullable=False, default=[])
    eligibility_criteria = Column(JSON, nullable=True)
    locations = Column(JSON, nullable=True)
    primary_outcomes = Column(JSON, nullable=True)
    
    # Vector embedding for semantic search
    embedding = Column(JSON, nullable=True)  # Store as JSON array
    embedding_model = Column(String(100), nullable=True)
    
    # Timeline fields
    start_date = Column(String(20), nullable=True)  # Store as ISO date string
    completion_date = Column(String(20), nullable=True)
    primary_completion_date = Column(String(20), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_fetched = Column(DateTime, nullable=True)


class Trial(BaseModel):
    """
    Clinical trial model with semantic search and eligibility matching.
    
    Supports vector embeddings, structured criteria processing,
    and integration with AI matching pipeline.
    """
    
    nct_id: str = Field(..., description="ClinicalTrials.gov NCT identifier")
    title: str = Field(..., description="Study title")
    brief_summary: str = Field(..., description="Brief study description")
    detailed_description: Optional[str] = Field(None, description="Detailed protocol description")
    primary_purpose: str = Field(..., description="Primary purpose of the study")
    phase: Optional[str] = Field(None, description="Study phase")
    status: str = Field(..., description="Current recruitment status")
    enrollment: Optional[int] = Field(None, description="Target enrollment")
    estimated_enrollment: Optional[int] = Field(None, description="Estimated enrollment")
    study_type: str = Field(..., description="Type of study (interventional/observational)")
    sponsor: Optional[str] = Field(None, description="Study sponsor")
    location: Optional[str] = Field(None, description="Primary location")
    
    # Structured data fields
    conditions: List[str] = Field(default_factory=list, description="Target medical conditions")
    interventions: List[str] = Field(default_factory=list, description="Study interventions")
    eligibility_criteria: Optional[Dict[str, Any]] = Field(None, description="Structured eligibility criteria")
    locations: Optional[List[Dict[str, Any]]] = Field(None, description="Study locations with contact info")
    primary_outcomes: Optional[List[Dict[str, Any]]] = Field(None, description="Primary outcome measures")
    
    # Timeline
    start_date: Optional[str] = Field(None, description="Study start date")
    completion_date: Optional[str] = Field(None, description="Study completion date")
    primary_completion_date: Optional[str] = Field(None, description="Primary completion date")
    
    # AI/ML fields
    embedding: Optional[List[float]] = Field(None, description="Vector embedding for semantic search")
    embedding_model: Optional[str] = Field(None, description="Model used for embedding generation")
    
    # Metadata
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Record creation time")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Last update time")
    last_fetched: Optional[datetime] = Field(None, description="Last data fetch from ClinicalTrials.gov")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nct_id": "NCT12345678",
                "title": "A Study of Drug X in Patients with Type 2 Diabetes",
                "brief_summary": "This study evaluates the safety and efficacy of Drug X in adults with Type 2 diabetes.",
                "primary_purpose": "treatment",
                "phase": "Phase 2",
                "status": "recruiting",
                "enrollment": 200,
                "study_type": "interventional",
                "conditions": ["Type 2 Diabetes"],
                "interventions": ["Drug X", "Placebo"],
                "eligibility_criteria": {
                    "min_age": 18,
                    "max_age": 65,
                    "gender": "all",
                    "inclusion_criteria": ["Diagnosed with Type 2 diabetes"],
                    "exclusion_criteria": ["Pregnant women"]
                }
            }
        }
    )
    
    @field_validator('nct_id')
    @classmethod
    def validate_nct_id(cls, v):
        """Validate NCT ID format."""
        if not v:
            raise ValueError("NCT ID is required")
        
        # NCT ID format: NCT followed by 8 digits
        pattern = r'^NCT\d{8}$'
        if not re.match(pattern, v):
            raise ValueError("NCT ID must be in format NCT12345678 (NCT + 8 digits)")
        
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate trial status."""
        valid_statuses = [
            "recruiting", "not_yet_recruiting", "active_not_recruiting",
            "completed", "suspended", "terminated", "withdrawn",
            "enrolling_by_invitation", "available", "no_longer_available"
        ]
        
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return v.lower()
    
    @field_validator('phase')
    @classmethod
    def validate_phase(cls, v):
        """Validate study phase."""
        if v is None:
            return v
        
        valid_phases = [
            "Early Phase 1", "Phase 1", "Phase 1/Phase 2",
            "Phase 2", "Phase 2/Phase 3", "Phase 3", "Phase 4",
            "Not Applicable"
        ]
        
        if v not in valid_phases:
            raise ValueError(f"Phase must be one of: {', '.join(valid_phases)}")
        
        return v
    
    @field_validator('primary_purpose')
    @classmethod
    def validate_primary_purpose(cls, v):
        """Validate primary purpose."""
        valid_purposes = [
            "treatment", "prevention", "diagnostic", "supportive_care",
            "screening", "health_services_research", "basic_science", "other"
        ]
        
        if v.lower() not in valid_purposes:
            raise ValueError(f"Primary purpose must be one of: {', '.join(valid_purposes)}")
        
        return v.lower()
    
    @field_validator('study_type')
    @classmethod
    def validate_study_type(cls, v):
        """Validate study type."""
        valid_types = ["interventional", "observational", "expanded_access"]
        
        if v.lower() not in valid_types:
            raise ValueError(f"Study type must be one of: {', '.join(valid_types)}")
        
        return v.lower()
    
    @field_validator('enrollment', 'estimated_enrollment')
    @classmethod
    def validate_enrollment(cls, v):
        """Validate enrollment numbers."""
        if v is not None and v <= 0:
            raise ValueError("Enrollment must be positive")
        return v
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v):
        """Validate embedding vector."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Embedding must be a list of floats")
            if len(v) == 0:
                raise ValueError("Embedding cannot be empty")
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("Embedding must contain only numbers")
        return v
    
    def generate_embedding(self, embedding_service=None) -> List[float]:
        """
        Generate vector embedding for semantic search using AI pipeline.
        
        Args:
            embedding_service: Optional embedding service to use
            
        Returns:
            Vector embedding as list of floats
        """
        if embedding_service is None:
            # Use our VectorEmbeddings service from the AI pipeline
            embedding_service = VectorEmbeddings()
            
        # Get text for embedding
        text = self.get_embedding_text()
        
        # Generate embedding using our AI service
        embedding = embedding_service.generate_embedding(text)
        
        # Store embedding in the model
        self.embedding = embedding
        self.embedding_model = "medical_nlp_v1"
        
        return embedding
    
    def get_embedding_text(self) -> str:
        """
        Generate text representation for embedding generation.
        
        Combines key trial information for semantic search.
        """
        text_components = []
        
        # Add title and summary
        text_components.append(self.title)
        text_components.append(self.brief_summary)
        
        # Add conditions
        if self.conditions:
            conditions_text = "Medical conditions: " + ", ".join(self.conditions)
            text_components.append(conditions_text)
        
        # Add interventions
        if self.interventions:
            interventions_text = "Interventions: " + ", ".join(self.interventions)
            text_components.append(interventions_text)
        
        # Add eligibility criteria text
        if self.eligibility_criteria:
            if "inclusion_criteria" in self.eligibility_criteria:
                inclusion_text = "Inclusion: " + "; ".join(self.eligibility_criteria["inclusion_criteria"])
                text_components.append(inclusion_text)
            
            if "exclusion_criteria" in self.eligibility_criteria:
                exclusion_text = "Exclusion: " + "; ".join(self.eligibility_criteria["exclusion_criteria"])
                text_components.append(exclusion_text)
        
        # Add study purpose and phase
        text_components.append(f"Purpose: {self.primary_purpose}")
        if self.phase:
            text_components.append(f"Phase: {self.phase}")
        
        return " | ".join(text_components)
    
    def get_search_keywords(self) -> List[str]:
        """
        Extract keywords for lexical search.
        
        Returns list of important terms for text-based search.
        """
        keywords = set()
        
        # Extract from conditions
        for condition in self.conditions:
            keywords.update(condition.lower().split())
        
        # Extract from interventions
        for intervention in self.interventions:
            keywords.update(intervention.lower().split())
        
        # Extract from title
        title_words = re.findall(r'\b\w+\b', self.title.lower())
        keywords.update([word for word in title_words if len(word) > 3])
        
        # Add study type and phase
        keywords.add(self.study_type)
        if self.phase:
            keywords.add(self.phase.lower().replace(" ", "_"))
        
        # Remove common stop words
        stop_words = {"the", "and", "for", "with", "study", "trial", "patients", "treatment"}
        keywords = keywords - stop_words
        
        return list(keywords)
    
    def get_lexical_search_text(self) -> str:
        """
        Generate text optimized for lexical search.
        
        Creates searchable text with emphasis on medical terms.
        """
        search_parts = []
        
        # Conditions with emphasis
        if self.conditions:
            search_parts.append(" ".join(self.conditions))
        
        # Interventions
        if self.interventions:
            search_parts.append(" ".join(self.interventions))
        
        # Phase and purpose
        search_parts.append(self.primary_purpose)
        if self.phase:
            search_parts.append(self.phase)
        
        # Extract key terms from title and summary
        combined_text = f"{self.title} {self.brief_summary}"
        medical_terms = re.findall(r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\b', combined_text)
        search_parts.extend(medical_terms)
        
        return " ".join(search_parts)
    
    def get_eligibility_requirements(self) -> Dict[str, Any]:
        """
        Extract structured eligibility requirements.
        
        Returns data formatted for AI-powered eligibility matching.
        """
        requirements = {
            "age_range": {},
            "gender_requirements": "all",
            "medical_conditions": [],
            "exclusion_conditions": [],
            "special_requirements": []
        }
        
        if not self.eligibility_criteria:
            return requirements
        
        criteria = self.eligibility_criteria
        
        # Age requirements
        if "min_age" in criteria or "max_age" in criteria:
            requirements["age_range"] = {
                "min_age": criteria.get("min_age"),
                "max_age": criteria.get("max_age"),
                "units": criteria.get("age_units", "years")
            }
        
        # Gender requirements
        if "gender" in criteria:
            requirements["gender_requirements"] = criteria["gender"]
        
        # Extract medical conditions from inclusion criteria
        if "inclusion_criteria" in criteria:
            for criterion in criteria["inclusion_criteria"]:
                # Simple extraction - in production, use NLP
                if any(keyword in criterion.lower() for keyword in ["diagnosed", "condition", "disease"]):
                    requirements["medical_conditions"].append(criterion)
                else:
                    requirements["special_requirements"].append(criterion)
        
        # Extract exclusion conditions
        if "exclusion_criteria" in criteria:
            requirements["exclusion_conditions"] = criteria["exclusion_criteria"]
        
        return requirements
    
    def calculate_location_proximity(self, patient_location: Optional[Dict[str, str]] = None) -> float:
        """
        Calculate proximity score based on trial locations.
        
        Args:
            patient_location: Dict with patient location info (city, state, country)
            
        Returns:
            Proximity score between 0.0 and 1.0
        """
        if not patient_location or not self.locations:
            return 0.5  # Neutral score if no location data
        
        max_proximity = 0.0
        patient_state = patient_location.get("state", "").lower()
        patient_country = patient_location.get("country", "usa").lower()
        
        for location in self.locations:
            location_score = 0.0
            
            # Country match
            loc_country = location.get("country", "usa").lower()
            if loc_country == patient_country:
                location_score += 0.5
            
            # State/region match
            loc_state = location.get("state", "").lower()
            if loc_state == patient_state:
                location_score += 0.5
            
            max_proximity = max(max_proximity, location_score)
        
        return max_proximity
    
    def is_actively_recruiting(self) -> bool:
        """Check if trial is actively recruiting patients."""
        active_statuses = ["recruiting", "not_yet_recruiting", "enrolling_by_invitation"]
        return self.status in active_statuses
    
    def get_contact_information(self) -> List[Dict[str, str]]:
        """
        Extract contact information for patient inquiries.
        
        Returns list of contact info for trial sites.
        """
        contacts = []
        
        if not self.locations:
            return contacts
        
        for location in self.locations:
            contact = {
                "facility": location.get("facility", ""),
                "city": location.get("city", ""),
                "state": location.get("state", ""),
                "phone": location.get("contact_phone", ""),
                "email": location.get("contact_email", "")
            }
            
            # Only include if we have meaningful contact info
            if contact["phone"] or contact["email"]:
                contacts.append(contact)
        
        return contacts
    
    def to_database_model(self) -> TrialDB:
        """Convert to SQLAlchemy model for database persistence."""
        return TrialDB(
            nct_id=self.nct_id,
            title=self.title,
            brief_summary=self.brief_summary,
            detailed_description=self.detailed_description,
            primary_purpose=self.primary_purpose,
            phase=self.phase,
            status=self.status,
            enrollment=self.enrollment,
            estimated_enrollment=self.estimated_enrollment,
            study_type=self.study_type,
            sponsor=self.sponsor,
            location=self.location,
            conditions=self.conditions,
            interventions=self.interventions,
            eligibility_criteria=self.eligibility_criteria,
            locations=self.locations,
            primary_outcomes=self.primary_outcomes,
            embedding=self.embedding,
            embedding_model=self.embedding_model,
            start_date=self.start_date,
            completion_date=self.completion_date,
            primary_completion_date=self.primary_completion_date,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_fetched=self.last_fetched
        )
    
    @classmethod
    def from_database_model(cls, db_model: TrialDB) -> "Trial":
        """Create Trial from SQLAlchemy model."""
        return cls(
            nct_id=db_model.nct_id,
            title=db_model.title,
            brief_summary=db_model.brief_summary,
            detailed_description=db_model.detailed_description,
            primary_purpose=db_model.primary_purpose,
            phase=db_model.phase,
            status=db_model.status,
            enrollment=db_model.enrollment,
            estimated_enrollment=db_model.estimated_enrollment,
            study_type=db_model.study_type,
            sponsor=db_model.sponsor,
            location=db_model.location,
            conditions=db_model.conditions or [],
            interventions=db_model.interventions or [],
            eligibility_criteria=db_model.eligibility_criteria,
            locations=db_model.locations,
            primary_outcomes=db_model.primary_outcomes,
            embedding=db_model.embedding,
            embedding_model=db_model.embedding_model,
            start_date=db_model.start_date,
            completion_date=db_model.completion_date,
            primary_completion_date=db_model.primary_completion_date,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
            last_fetched=db_model.last_fetched
        )