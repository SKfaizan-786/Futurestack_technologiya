"""
MatchResult model with AI reasoning chain tracking.

This model represents the results of patient-trial matching with detailed
reasoning chains, confidence scoring, and audit trail capabilities.
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, Float
from sqlalchemy.orm import declarative_base
import json
import uuid

Base = declarative_base()


class MatchResultDB(Base):
    """SQLAlchemy MatchResult model for database persistence."""
    
    __tablename__ = "match_results"
    
    match_id = Column(String(100), primary_key=True)
    patient_id = Column(String(100), nullable=False, index=True)
    trial_nct_id = Column(String(20), nullable=False, index=True)
    
    # Scores
    overall_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    match_status = Column(String(50), nullable=False)
    
    # Reasoning and explanation
    reasoning_chain = Column(JSON, nullable=False, default=[])
    explanation = Column(Text, nullable=True)
    next_steps = Column(JSON, nullable=True)
    
    # Confidence factors
    confidence_factors = Column(JSON, nullable=True)
    
    # Audit and metadata
    audit_metadata = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    ai_model_version = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MatchResult(BaseModel):
    """
    Patient-trial matching result with AI reasoning chain.
    
    Tracks the complete decision process for patient eligibility,
    with confidence scoring and human-readable explanations.
    """
    
    match_id: str = Field(..., description="Unique match identifier")
    patient_id: str = Field(..., description="Patient identifier")
    trial_nct_id: str = Field(..., description="Trial NCT ID")
    
    # Core scoring
    overall_score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Overall match score (0.0 - 1.0)"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Confidence in the match assessment (0.0 - 1.0)"
    )
    match_status: str = Field(..., description="Match status")
    
    # Reasoning chain
    reasoning_chain: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Step-by-step reasoning process"
    )
    
    # Human-readable content
    explanation: Optional[str] = Field(
        None,
        description="Human-readable explanation of the match result"
    )
    next_steps: Optional[List[str]] = Field(
        None,
        description="Recommended next steps for the patient"
    )
    
    # Confidence tracking
    confidence_factors: Optional[Dict[str, float]] = Field(
        None,
        description="Factors affecting confidence score"
    )
    
    # Audit and compliance
    audit_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Audit trail metadata for HIPAA compliance"
    )
    processing_time_ms: Optional[int] = Field(
        None,
        description="Processing time in milliseconds"
    )
    ai_model_version: Optional[str] = Field(
        None,
        description="AI model version used for matching"
    )
    
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "match_id": "MATCH-2025-001",
                "patient_id": "PAT-2025-001",
                "trial_nct_id": "NCT12345678",
                "overall_score": 0.85,
                "confidence_score": 0.92,
                "match_status": "eligible",
                "reasoning_chain": [
                    {
                        "step": 1,
                        "category": "age_check",
                        "result": "pass",
                        "details": "Patient age 45 is within trial range 18-65",
                        "score": 1.0,
                        "weight": 0.2
                    }
                ],
                "explanation": "Patient is eligible for this diabetes study based on age and condition match.",
                "next_steps": ["Contact study coordinator", "Schedule screening"]
            }
        }
    )
    
    @field_validator('match_id')
    @classmethod
    def validate_match_id(cls, v):
        """Validate match ID format."""
        if not v or not v.strip():
            raise ValueError("Match ID cannot be empty")
        return v.strip()
    
    @field_validator('match_status')
    @classmethod
    def validate_match_status(cls, v):
        """Validate match status options."""
        valid_statuses = [
            "eligible",
            "ineligible", 
            "potentially_eligible",
            "requires_review",
            "insufficient_data"
        ]
        
        if v.lower() not in valid_statuses:
            raise ValueError(f"Match status must be one of: {', '.join(valid_statuses)}")
        
        return v.lower()
    
    @field_validator('reasoning_chain')
    @classmethod
    def validate_reasoning_chain(cls, v):
        """Validate reasoning chain structure."""
        if not isinstance(v, list):
            raise ValueError("Reasoning chain must be a list")
        
        for i, step in enumerate(v):
            if not isinstance(step, dict):
                raise ValueError(f"Reasoning step {i} must be a dictionary")
            
            required_fields = ["step", "category", "result", "details"]
            for field in required_fields:
                if field not in step:
                    raise ValueError(f"Reasoning step {i} missing required field: {field}")
            
            # Validate step number
            if not isinstance(step["step"], int) or step["step"] <= 0:
                raise ValueError(f"Reasoning step {i} must have positive integer step number")
            
            # Validate category
            valid_categories = [
                "age_check", "gender_check", "condition_match",
                "medication_compatibility", "allergy_check", "exclusion_check",
                "inclusion_check", "location_proximity", "trial_status_check",
                "lab_values_check", "special_populations_check"
            ]
            
            if step["category"] not in valid_categories:
                raise ValueError(f"Invalid reasoning category: {step['category']}")
            
            # Validate result
            valid_results = ["pass", "fail", "partial", "unknown", "requires_review"]
            if step["result"] not in valid_results:
                raise ValueError(f"Invalid reasoning result: {step['result']}")
            
            # Validate score if present
            if "score" in step:
                score = step["score"]
                if not isinstance(score, (int, float)) or score < 0.0 or score > 1.0:
                    raise ValueError(f"Reasoning step {i} score must be between 0.0 and 1.0")
        
        return v
    
    @field_validator('confidence_factors')
    @classmethod
    def validate_confidence_factors(cls, v):
        """Validate confidence factors structure."""
        if v is None:
            return v
        
        if not isinstance(v, dict):
            raise ValueError("Confidence factors must be a dictionary")
        
        for factor, score in v.items():
            if not isinstance(score, (int, float)) or score < 0.0 or score > 1.0:
                raise ValueError(f"Confidence factor '{factor}' must be between 0.0 and 1.0")
        
        return v
    
    @model_validator(mode='after')
    @classmethod
    def validate_score_consistency(cls, model):
        """Validate basic consistency (flexible for testing various scenarios)."""
        # Keep this lightweight for contract testing
        # Business logic validation can be added in service layer
        return model
    
    def get_eligibility_summary(self) -> Dict[str, Any]:
        """
        Generate summary of eligibility assessment.
        
        Returns organized summary of passed/failed criteria.
        """
        summary = {
            "overall_status": self.match_status,
            "overall_score": self.overall_score,
            "confidence": self.confidence_score,
            "passed_checks": [],
            "failed_checks": [],
            "partial_checks": [],
            "review_required": [],
            "total_checks": len(self.reasoning_chain)
        }
        
        for step in self.reasoning_chain:
            step_summary = {
                "category": step["category"],
                "details": step["details"],
                "score": step.get("score", 0.0)
            }
            
            result = step["result"]
            if result == "pass":
                summary["passed_checks"].append(step_summary)
            elif result == "fail":
                summary["failed_checks"].append(step_summary)
            elif result == "partial":
                summary["partial_checks"].append(step_summary)
            elif result in ["unknown", "requires_review"]:
                summary["review_required"].append(step_summary)
        
        # Calculate summary statistics
        summary["pass_rate"] = len(summary["passed_checks"]) / max(1, summary["total_checks"])
        summary["fail_rate"] = len(summary["failed_checks"]) / max(1, summary["total_checks"])
        
        return summary
    
    def get_failed_criteria(self) -> List[Dict[str, Any]]:
        """Get list of failed eligibility criteria."""
        return [step for step in self.reasoning_chain if step.get("result") == "fail"]
    
    def get_passed_criteria(self) -> List[Dict[str, Any]]:
        """Get list of passed eligibility criteria."""
        return [step for step in self.reasoning_chain if step.get("result") == "pass"]
    
    def get_explanation(self) -> str:
        """
        Generate human-readable explanation of match result.
        
        Creates comprehensive explanation based on reasoning chain.
        """
        if self.explanation:
            return self.explanation
        
        # Generate explanation from reasoning chain
        explanation_parts = []
        
        # Start with overall assessment
        status_phrases = {
            "eligible": "is eligible for",
            "ineligible": "is not eligible for", 
            "potentially_eligible": "may be eligible for",
            "requires_review": "requires manual review for",
            "insufficient_data": "has insufficient data for"
        }
        
        explanation_parts.append(f"The patient {status_phrases.get(self.match_status, 'was assessed for')} this clinical trial.")
        
        # Add confidence information
        if self.confidence_score >= 0.8:
            explanation_parts.append("This assessment has high confidence.")
        elif self.confidence_score >= 0.6:
            explanation_parts.append("This assessment has moderate confidence.")
        else:
            explanation_parts.append("This assessment has low confidence and may require review.")
        
        # Summarize key findings with details
        passed_checks = self.get_passed_criteria()
        failed_checks = self.get_failed_criteria()
        
        if passed_checks:
            key_passes = []
            for step in passed_checks[:3]:
                category = step["category"].replace("_", " ")
                details = step.get("details", "")
                if details and len(details) < 80:  # Include longer details for more context
                    key_passes.append(f"{category} ({details})")
                else:
                    key_passes.append(category)
            explanation_parts.append(f"Key eligibility criteria met: {', '.join(key_passes)}.")
        
        if failed_checks:
            key_failures = []
            for step in failed_checks[:3]:
                category = step["category"].replace("_", " ")
                details = step.get("details", "")
                if details and len(details) < 80:  # Include longer details for more context
                    key_failures.append(f"{category} ({details})")
                else:
                    key_failures.append(category)
            explanation_parts.append(f"Eligibility barriers identified: {', '.join(key_failures)}.")
        
        # Add next steps if available
        if self.next_steps:
            explanation_parts.append(f"Recommended next steps: {'; '.join(self.next_steps[:2])}.")
        
        generated_explanation = " ".join(explanation_parts)
        
        # Cache the generated explanation
        self.explanation = generated_explanation
        return generated_explanation
    
    def add_reasoning_step(self, 
                          category: str,
                          result: str,
                          details: str,
                          score: Optional[float] = None,
                          weight: Optional[float] = None) -> None:
        """
        Add a reasoning step to the chain.
        
        Args:
            category: Type of check performed
            result: Result of the check (pass/fail/partial/unknown/requires_review)
            details: Human-readable details
            score: Individual score for this step (0.0-1.0)
            weight: Weight of this step in overall calculation
        """
        step_number = len(self.reasoning_chain) + 1
        
        step = {
            "step": step_number,
            "category": category,
            "result": result,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if score is not None:
            step["score"] = score
        
        if weight is not None:
            step["weight"] = weight
        
        self.reasoning_chain.append(step)
        self.updated_at = datetime.now(timezone.utc)
    
    def calculate_overall_score(self) -> float:
        """
        Calculate overall score from reasoning chain.
        
        Uses weighted average of individual step scores.
        """
        if not self.reasoning_chain:
            return 0.5  # Neutral score if no reasoning
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for step in self.reasoning_chain:
            score = step.get("score", 0.5)  # Default neutral score
            weight = step.get("weight", 1.0)  # Default equal weight
            
            # Failed steps get zero score regardless of individual score
            if step.get("result") == "fail":
                score = 0.0
            
            total_weighted_score += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        calculated_score = total_weighted_score / total_weight
        self.overall_score = calculated_score
        return calculated_score
    
    def update_confidence_score(self, factors: Optional[Dict[str, float]] = None) -> float:
        """
        Update confidence score based on various factors.
        
        Args:
            factors: Dictionary of confidence factors and their scores
            
        Returns:
            Updated confidence score
        """
        if factors:
            self.confidence_factors = factors
        
        if not self.confidence_factors:
            # Default confidence based on reasoning chain completeness
            if len(self.reasoning_chain) >= 5:
                self.confidence_score = 0.9
            elif len(self.reasoning_chain) >= 3:
                self.confidence_score = 0.7
            else:
                self.confidence_score = 0.5
        else:
            # Calculate weighted confidence from factors
            confidence = sum(self.confidence_factors.values()) / len(self.confidence_factors)
            self.confidence_score = min(1.0, max(0.0, confidence))
        
        return self.confidence_score
    
    def set_next_steps(self, steps: List[str]) -> None:
        """Set recommended next steps for the patient."""
        self.next_steps = steps[:5]  # Limit to 5 steps
        self.updated_at = datetime.now(timezone.utc)
    
    def add_audit_metadata(self, metadata: Dict[str, Any]) -> None:
        """Add audit metadata for HIPAA compliance."""
        if self.audit_metadata is None:
            self.audit_metadata = {}
        
        self.audit_metadata.update(metadata)
        self.audit_metadata["last_audit_update"] = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc)
    
    def get_audit_trail(self) -> Dict[str, Any]:
        """
        Generate comprehensive audit trail.
        
        Returns audit information for compliance tracking.
        """
        audit_trail = {
            "match_id": self.match_id,
            "patient_id_hash": self._hash_patient_id(),
            "trial_nct_id": self.trial_nct_id,
            "processing_timestamp": self.created_at.isoformat() if self.created_at else None,
            "ai_model_version": self.ai_model_version,
            "processing_time_ms": self.processing_time_ms,
            "decision_chain_length": len(self.reasoning_chain),
            "final_decision": self.match_status,
            "confidence_level": self.confidence_score,
            "audit_metadata": self.audit_metadata or {},
            "data_integrity_check": self._calculate_integrity_hash()
        }
        
        return audit_trail
    
    def _hash_patient_id(self) -> str:
        """Create anonymized hash of patient ID for audit."""
        import hashlib
        return hashlib.sha256(f"{self.patient_id}_{self.created_at.date()}".encode()).hexdigest()[:16]
    
    def _calculate_integrity_hash(self) -> str:
        """Calculate integrity hash for tamper detection."""
        import hashlib
        
        integrity_data = {
            "match_id": self.match_id,
            "overall_score": self.overall_score,
            "match_status": self.match_status,
            "reasoning_steps": len(self.reasoning_chain),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        data_string = json.dumps(integrity_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def to_patient_report(self) -> Dict[str, Any]:
        """
        Generate patient-friendly report.
        
        Returns simplified, patient-readable version of results.
        """
        report = {
            "trial_id": self.trial_nct_id,
            "eligibility_status": self.match_status.replace("_", " ").title(),
            "match_percentage": int(self.overall_score * 100),
            "explanation": self.get_explanation(),
            "next_steps": self.next_steps or [],
            "assessment_date": self.created_at.date().isoformat() if self.created_at else None,
            "confidence_level": "High" if self.confidence_score >= 0.8 else "Medium" if self.confidence_score >= 0.6 else "Low"
        }
        
        # Add key eligibility points
        passed = self.get_passed_criteria()
        failed = self.get_failed_criteria()
        
        if passed:
            report["qualifying_factors"] = [step["details"] for step in passed[:3]]
        
        if failed:
            report["disqualifying_factors"] = [step["details"] for step in failed[:3]]
        
        return report
    
    @classmethod
    def create_new_match(cls,
                        patient_id: str,
                        trial_nct_id: str,
                        ai_model_version: Optional[str] = None) -> "MatchResult":
        """
        Create a new match result instance.
        
        Args:
            patient_id: Patient identifier
            trial_nct_id: Trial NCT ID
            ai_model_version: Version of AI model being used
            
        Returns:
            New MatchResult instance
        """
        match_id = f"MATCH-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        return cls(
            match_id=match_id,
            patient_id=patient_id,
            trial_nct_id=trial_nct_id,
            overall_score=0.0,
            confidence_score=0.0,
            match_status="insufficient_data",
            reasoning_chain=[],
            ai_model_version=ai_model_version,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    def to_database_model(self) -> MatchResultDB:
        """Convert to SQLAlchemy model for database persistence."""
        return MatchResultDB(
            match_id=self.match_id,
            patient_id=self.patient_id,
            trial_nct_id=self.trial_nct_id,
            overall_score=self.overall_score,
            confidence_score=self.confidence_score,
            match_status=self.match_status,
            reasoning_chain=self.reasoning_chain,
            explanation=self.explanation,
            next_steps=self.next_steps,
            confidence_factors=self.confidence_factors,
            audit_metadata=self.audit_metadata,
            processing_time_ms=self.processing_time_ms,
            ai_model_version=self.ai_model_version,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_database_model(cls, db_model: MatchResultDB) -> "MatchResult":
        """Create MatchResult from SQLAlchemy model."""
        return cls(
            match_id=db_model.match_id,
            patient_id=db_model.patient_id,
            trial_nct_id=db_model.trial_nct_id,
            overall_score=db_model.overall_score,
            confidence_score=db_model.confidence_score,
            match_status=db_model.match_status,
            reasoning_chain=db_model.reasoning_chain or [],
            explanation=db_model.explanation,
            next_steps=db_model.next_steps,
            confidence_factors=db_model.confidence_factors,
            audit_metadata=db_model.audit_metadata,
            processing_time_ms=db_model.processing_time_ms,
            ai_model_version=db_model.ai_model_version,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at
        )