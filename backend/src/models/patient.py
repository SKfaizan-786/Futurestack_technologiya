"""
Patient model with medical data validation and HIPAA compliance.

This model represents patient data for clinical trial matching,
with built-in privacy protection and audit logging capabilities.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from sqlalchemy import Column, String, Integer, JSON, DateTime, Text
from sqlalchemy.orm import declarative_base
import hashlib
import json
import re

Base = declarative_base()


class PatientDB(Base):
    """SQLAlchemy Patient model for database persistence."""
    
    __tablename__ = "patients"
    
    patient_id = Column(String(100), primary_key=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)
    medical_conditions = Column(JSON, nullable=False, default=[])
    medications = Column(JSON, nullable=False, default=[])
    allergies = Column(JSON, nullable=False, default=[])
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Audit fields for HIPAA compliance
    audit_log_id = Column(String(100), nullable=True)
    data_hash = Column(String(64), nullable=True)  # For integrity verification


class Patient(BaseModel):
    """
    Patient model for clinical trial matching.
    
    Supports HIPAA-compliant data handling, validation,
    and integration with AI matching pipeline.
    """
    
    patient_id: str = Field(..., description="Unique patient identifier")
    age: int = Field(..., ge=18, le=100, description="Patient age in years")
    gender: str = Field(..., description="Patient gender")
    medical_conditions: List[str] = Field(
        default_factory=list,
        description="List of patient's medical conditions"
    )
    medications: List[str] = Field(
        default_factory=list,
        description="List of current medications"
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="List of known allergies"
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Record creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Record last update timestamp"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "PAT-2025-001",
                "age": 45,
                "gender": "female",
                "medical_conditions": ["Type 2 Diabetes", "Hypertension"],
                "medications": ["Metformin", "Lisinopril"],
                "allergies": ["Penicillin"],
                "created_at": "2025-09-30T10:00:00Z"
            }
        }
    )
    
    @field_validator('patient_id')
    @classmethod
    def validate_patient_id(cls, v):
        """Validate patient ID format."""
        if not v or not v.strip():
            raise ValueError("Patient ID cannot be empty")
        
        # Allow flexible patient ID formats
        if len(v.strip()) < 3:
            raise ValueError("Patient ID must be at least 3 characters")
        
        return v.strip()
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        """Validate gender options."""
        valid_genders = ["male", "female", "other", "prefer_not_to_say"]
        if v.lower() not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
        return v.lower()
    
    @field_validator('medical_conditions', 'medications', 'allergies')
    @classmethod
    def validate_string_lists(cls, v):
        """Validate string list fields."""
        if not isinstance(v, list):
            raise ValueError("Must be a list")
        
        # Clean and validate each item
        cleaned_items = []
        for item in v:
            if isinstance(item, str) and item.strip():
                cleaned_items.append(item.strip())
        
        return cleaned_items
    
    @model_validator(mode='after')
    def validate_medical_data_consistency(self):
        """Validate overall medical data consistency."""
        age = self.age
        conditions = self.medical_conditions
        medications = self.medications
        
        # Basic consistency checks
        if age and age < 18:
            raise ValueError("Patient must be 18 or older for clinical trials")
        
        # Check for potential medication-condition mismatches
        # (In real implementation, this would use medical knowledge base)
        diabetes_meds = ['metformin', 'insulin', 'glipizide', 'glyburide']
        has_diabetes = any('diabetes' in condition.lower() for condition in conditions)
        has_diabetes_med = any(med.lower() in diabetes_meds for med in medications)
        
        if has_diabetes_med and not has_diabetes:
            # Warning rather than error for flexibility
            pass
        
        return self
    
    def get_anonymized_data(self) -> Dict[str, Any]:
        """
        Return anonymized patient data for research purposes.
        
        Removes direct identifiers while preserving medical information
        needed for trial matching.
        """
        anonymized = {
            "age_group": self._get_age_group(),
            "gender": self.gender,
            "medical_conditions": self.medical_conditions.copy(),
            "medications": self.medications.copy(),
            "allergies": self.allergies.copy(),
            "data_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return anonymized
    
    def _get_age_group(self) -> str:
        """Convert age to age group for anonymization."""
        if self.age < 30:
            return "18-29"
        elif self.age < 40:
            return "30-39"
        elif self.age < 50:
            return "40-49"
        elif self.age < 60:
            return "50-59"
        elif self.age < 70:
            return "60-69"
        else:
            return "70+"
    
    def get_audit_log(self) -> Dict[str, Any]:
        """
        Generate audit log entry for HIPAA compliance.
        
        Returns structured audit information without sensitive data.
        """
        audit_entry = {
            "event_type": "patient_data_access",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patient_hash": self._get_patient_hash(),
            "data_fields_accessed": [
                "age", "gender", "medical_conditions", 
                "medications", "allergies"
            ],
            "access_purpose": "clinical_trial_matching",
            "data_integrity_hash": self._get_data_integrity_hash()
        }
        
        return audit_entry
    
    def _get_patient_hash(self) -> str:
        """Generate anonymized patient hash for audit trail."""
        # Use patient_id + creation time for consistent but anonymous hash
        hash_input = f"{self.patient_id}_{self.created_at.isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _get_data_integrity_hash(self) -> str:
        """Generate hash for data integrity verification."""
        data_string = json.dumps({
            "age": self.age,
            "gender": self.gender,
            "conditions": sorted(self.medical_conditions),
            "medications": sorted(self.medications),
            "allergies": sorted(self.allergies)
        }, sort_keys=True)
        
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def get_search_text(self) -> str:
        """
        Generate search-optimized text representation for AI matching.
        
        Combines all relevant medical information into searchable text.
        """
        search_components = []
        
        # Add demographic info
        search_components.append(f"{self.age} year old {self.gender}")
        
        # Add medical conditions
        if self.medical_conditions:
            conditions_text = ", ".join(self.medical_conditions)
            search_components.append(f"Medical conditions: {conditions_text}")
        
        # Add medications
        if self.medications:
            medications_text = ", ".join(self.medications)
            search_components.append(f"Current medications: {medications_text}")
        
        # Add allergies
        if self.allergies:
            allergies_text = ", ".join(self.allergies)
            search_components.append(f"Allergies: {allergies_text}")
        
        return ". ".join(search_components)
    
    def get_eligibility_data(self) -> Dict[str, Any]:
        """
        Extract data needed for eligibility checking.
        
        Returns structured data for AI-powered eligibility analysis.
        """
        eligibility_data = {
            "age": self.age,
            "gender": self.gender,
            "medical_conditions": self.medical_conditions.copy(),
            "medications": self.medications.copy(),
            "allergies": self.allergies.copy(),
            "demographics": {
                "age_group": self._get_age_group(),
                "gender_category": self.gender
            },
            "risk_factors": self._extract_risk_factors(),
            "contraindications": self._extract_contraindications()
        }
        
        return eligibility_data
    
    def _extract_risk_factors(self) -> List[str]:
        """Extract potential risk factors from patient data."""
        risk_factors = []
        
        # Age-based risk factors
        if self.age >= 65:
            risk_factors.append("advanced_age")
        
        # Condition-based risk factors
        high_risk_conditions = [
            "diabetes", "hypertension", "cardiovascular", "kidney", 
            "liver", "cancer", "immunocompromised"
        ]
        
        for condition in self.medical_conditions:
            condition_lower = condition.lower()
            for risk_condition in high_risk_conditions:
                if risk_condition in condition_lower:
                    risk_factors.append(f"condition_{risk_condition}")
        
        # Medication-based risk factors
        high_risk_medications = [
            "warfarin", "insulin", "chemotherapy", "immunosuppressant"
        ]
        
        for medication in self.medications:
            medication_lower = medication.lower()
            for risk_med in high_risk_medications:
                if risk_med in medication_lower:
                    risk_factors.append(f"medication_{risk_med}")
        
        return list(set(risk_factors))  # Remove duplicates
    
    def _extract_contraindications(self) -> List[str]:
        """Extract potential contraindications from patient data."""
        contraindications = []
        
        # Allergy-based contraindications
        for allergy in self.allergies:
            contraindications.append(f"allergy_{allergy.lower().replace(' ', '_')}")
        
        # Condition-based contraindications
        contraindication_conditions = [
            "pregnancy", "nursing", "severe_kidney_disease",
            "severe_liver_disease", "active_cancer"
        ]
        
        for condition in self.medical_conditions:
            condition_lower = condition.lower()
            for contraindication in contraindication_conditions:
                if contraindication.replace('_', ' ') in condition_lower:
                    contraindications.append(condition_lower.replace(' ', '_'))
        
        return contraindications
    
    def to_database_model(self) -> PatientDB:
        """Convert to SQLAlchemy model for database persistence."""
        return PatientDB(
            patient_id=self.patient_id,
            age=self.age,
            gender=self.gender,
            medical_conditions=self.medical_conditions,
            medications=self.medications,
            allergies=self.allergies,
            created_at=self.created_at,
            updated_at=self.updated_at,
            data_hash=self._get_data_integrity_hash()
        )
    
    @classmethod
    def from_database_model(cls, db_model: PatientDB) -> "Patient":
        """Create Patient from SQLAlchemy model."""
        return cls(
            patient_id=db_model.patient_id,
            age=db_model.age,
            gender=db_model.gender,
            medical_conditions=db_model.medical_conditions or [],
            medications=db_model.medications or [],
            allergies=db_model.allergies or [],
            created_at=db_model.created_at,
            updated_at=db_model.updated_at
        )