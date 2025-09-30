"""
EligibilityCriteria model with NLP processing capabilities.

This model processes and structures clinical trial eligibility criteria
using natural language processing for AI-powered patient matching.
"""
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, Float
from sqlalchemy.orm import declarative_base
import re
import json
import hashlib

Base = declarative_base()


class EligibilityCriteriaDB(Base):
    """SQLAlchemy EligibilityCriteria model for database persistence."""
    
    __tablename__ = "eligibility_criteria"
    
    criteria_id = Column(String(100), primary_key=True)
    trial_nct_id = Column(String(20), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    
    # Structured criteria
    inclusion_criteria = Column(JSON, nullable=False, default=[])
    exclusion_criteria = Column(JSON, nullable=False, default=[])
    age_requirements = Column(JSON, nullable=True)
    gender_requirements = Column(String(50), nullable=True)
    
    # NLP processing results
    extracted_entities = Column(JSON, nullable=True)
    structured_requirements = Column(JSON, nullable=True)
    complexity_score = Column(Float, nullable=True)
    
    # Metadata
    version = Column(String(20), default="1.0")
    processing_metadata = Column(JSON, nullable=True)
    locale = Column(String(10), default="en-US")
    terminology_system = Column(String(50), default="SNOMED-CT")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EligibilityCriteria(BaseModel):
    """
    Eligibility criteria model with NLP processing and patient matching.
    
    Processes raw eligibility text into structured data for AI matching,
    with support for medical entity extraction and semantic analysis.
    """
    
    criteria_id: str = Field(..., description="Unique criteria identifier")
    trial_nct_id: str = Field(..., description="Associated trial NCT ID")
    raw_text: str = Field(..., description="Original eligibility criteria text")
    
    # Structured criteria lists
    inclusion_criteria: List[str] = Field(
        default_factory=list,
        description="List of inclusion criteria"
    )
    exclusion_criteria: List[str] = Field(
        default_factory=list,
        description="List of exclusion criteria"
    )
    
    # Structured requirements
    age_requirements: Optional[Dict[str, Any]] = Field(
        None,
        description="Age requirements (min_age, max_age, units)"
    )
    gender_requirements: Optional[str] = Field(
        "all",
        description="Gender requirements"
    )
    
    # NLP processing results
    extracted_entities: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Extracted medical entities"
    )
    structured_requirements: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured requirements for matching"
    )
    complexity_score: Optional[float] = Field(
        None,
        description="Criteria complexity score"
    )
    
    # Metadata
    version: str = Field(default="1.0", description="Criteria version")
    processing_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="NLP processing metadata"
    )
    locale: str = Field(default="en-US", description="Language locale")
    terminology_system: str = Field(
        default="SNOMED-CT",
        description="Medical terminology system"
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
                "criteria_id": "CRIT-2025-001",
                "trial_nct_id": "NCT12345678",
                "raw_text": "Inclusion: Adults 18-65 with diabetes. Exclusion: Pregnant women.",
                "inclusion_criteria": ["Adults aged 18-65 years", "Diagnosed with diabetes"],
                "exclusion_criteria": ["Pregnant or nursing women"],
                "age_requirements": {"min_age": 18, "max_age": 65, "age_units": "years"},
                "gender_requirements": "all"
            }
        }
    )
    
    @field_validator('criteria_id')
    @classmethod
    def validate_criteria_id(cls, v):
        """Validate criteria ID format."""
        if not v or not v.strip():
            raise ValueError("Criteria ID cannot be empty")
        return v.strip()
    
    @field_validator('trial_nct_id')
    @classmethod
    def validate_trial_nct_id(cls, v):
        """Validate NCT ID format."""
        pattern = r'^NCT\d{8}$'
        if not re.match(pattern, v):
            raise ValueError("NCT ID must be in format NCT12345678")
        return v
    
    @field_validator('age_requirements')
    @classmethod
    def validate_age_requirements(cls, v):
        """Validate age requirements structure."""
        if v is None:
            return v
        
        min_age = v.get('min_age')
        max_age = v.get('max_age')
        
        # Validate age values
        if min_age is not None:
            if not isinstance(min_age, int) or min_age < 0:
                raise ValueError("min_age must be a non-negative integer")
            if min_age > 120:
                raise ValueError("min_age must be realistic (≤120 years)")
        
        if max_age is not None:
            if not isinstance(max_age, int) or max_age < 0:
                raise ValueError("max_age must be a non-negative integer")
            if max_age > 120:
                raise ValueError("max_age must be realistic (≤120 years)")
        
        # Validate age range consistency
        if min_age is not None and max_age is not None:
            if min_age > max_age:
                raise ValueError("min_age cannot be greater than max_age")
        
        return v
    
    @field_validator('gender_requirements')
    @classmethod
    def validate_gender_requirements(cls, v):
        """Validate gender requirements."""
        if v is None:
            return "all"
        
        valid_genders = ["all", "male", "female", "other", "prefer_not_to_say"]
        if v.lower() not in valid_genders:
            raise ValueError(f"Gender requirements must be one of: {', '.join(valid_genders)}")
        
        return v.lower()
    
    @field_validator('complexity_score')
    @classmethod
    def validate_complexity_score(cls, v):
        """Validate complexity score range."""
        if v is not None:
            if not isinstance(v, (int, float)) or v < 0:
                raise ValueError("Complexity score must be non-negative")
        return v
    
    def parse_raw_text(self) -> Dict[str, Any]:
        """
        Parse raw eligibility text into structured components.
        
        Uses NLP techniques to extract inclusion/exclusion criteria,
        age requirements, and other structured data.
        """
        parsing_result = {
            "inclusion_criteria": [],
            "exclusion_criteria": [],
            "age_requirements": {},
            "gender_requirements": "all",
            "parsed_entities": {}
        }
        
        text = self.raw_text.lower()
        
        # Extract inclusion criteria
        inclusion_patterns = [
            r'inclusion criteria?[:\s]*(.*?)(?=exclusion|$)',
            r'inclusion[:\s]*(.*?)(?=exclusion|$)',
            r'include[:\s]*(.*?)(?=exclude|$)'
        ]
        
        for pattern in inclusion_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                inclusion_text = matches[0].strip()
                # Split by common delimiters
                criteria = self._split_criteria_text(inclusion_text)
                parsing_result["inclusion_criteria"].extend(criteria)
                break
        
        # Extract exclusion criteria
        exclusion_patterns = [
            r'exclusion criteria?[:\s]*(.*?)(?=inclusion|$)',
            r'exclusion[:\s]*(.*?)(?=inclusion|$)',
            r'exclude[:\s]*(.*?)(?=include|$)'
        ]
        
        for pattern in exclusion_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                exclusion_text = matches[0].strip()
                criteria = self._split_criteria_text(exclusion_text)
                parsing_result["exclusion_criteria"].extend(criteria)
                break
        
        # Extract age requirements
        age_patterns = [
            r'(?:aged?|age)\s+(\d+)\s*[-–to]\s*(\d+)\s*years?',
            r'(\d+)\s*[-–to]\s*(\d+)\s*years?\s+of\s+age',
            r'ages?\s+(\d+)\s*[-–to]\s*(\d+)',
            r'minimum\s+age[:\s]*(\d+)',
            r'maximum\s+age[:\s]*(\d+)'
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if len(matches[0]) == 2:  # Range pattern
                    min_age, max_age = matches[0]
                    parsing_result["age_requirements"] = {
                        "min_age": int(min_age),
                        "max_age": int(max_age),
                        "age_units": "years"
                    }
                    break
        
        # Extract gender requirements
        if re.search(r'\\bmale\\b.*only|only.*\\bmale\\b', text):
            parsing_result["gender_requirements"] = "male"
        elif re.search(r'\\bfemale\\b.*only|only.*\\bfemale\\b', text):
            parsing_result["gender_requirements"] = "female"
        elif re.search(r'women.*child.*bearing|pregnant|nursing', text):
            # Often indicates female-specific considerations
            parsing_result["gender_requirements"] = "all"  # But note special considerations
        
        return parsing_result
    
    def _split_criteria_text(self, text: str) -> List[str]:
        """Split criteria text into individual criteria items."""
        # Remove common numbering patterns
        text = re.sub(r'^\\s*\\d+\\.?\\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\\s*[a-z]\\.?\\s*', '', text, flags=re.MULTILINE)
        
        # Split by common delimiters
        criteria = []
        
        # Try different splitting patterns
        splits = re.split(r'[;\\n]|\\d+\\.|[a-z]\\.|•|\\*', text)
        
        for item in splits:
            item = item.strip()
            if len(item) > 10:  # Filter out very short items
                criteria.append(item)
        
        return criteria
    
    def extract_medical_entities(self) -> Dict[str, List[str]]:
        """
        Extract medical entities from criteria text.
        
        Uses pattern matching and medical dictionaries to identify
        conditions, medications, procedures, and other medical concepts.
        """
        entities = {
            "conditions": [],
            "excluded_conditions": [],
            "medications": [],
            "procedures": [],
            "lab_values": [],
            "demographics": []
        }
        
        text = self.raw_text.lower()
        inclusion_text = " ".join(self.inclusion_criteria).lower()
        exclusion_text = " ".join(self.exclusion_criteria).lower()
        full_text = f"{text} {inclusion_text} {exclusion_text}".lower()
        
        # Medical condition patterns
        condition_patterns = [
            r'\b(?:diabetes|hypertension|cancer|asthma|copd|heart disease|kidney disease)\b',
            r'\b(?:type [12] diabetes|diabetes mellitus)\b',
            r'\b(?:myocardial infarction|stroke|cardiovascular disease)\b',
            r'\b(?:depression|anxiety|psychiatric)\b'
        ]
        
        # Extract conditions from inclusion criteria (included conditions)
        for pattern in condition_patterns:
            matches = re.findall(pattern, f"{text} {inclusion_text}")
            entities["conditions"].extend(matches)
        
        # Extract conditions from exclusion criteria (excluded conditions)
        for pattern in condition_patterns:
            matches = re.findall(pattern, exclusion_text)
            entities["excluded_conditions"].extend(matches)
        
        # Medication patterns
        medication_patterns = [
            r'\b(?:metformin|insulin|lisinopril|atorvastatin|aspirin)\b',
            r'\b(?:chemotherapy|immunotherapy|radiation)\b',
            r'\b[a-z]+(?:mab|nib|pril|statin|cillin)\b'  # Common drug suffixes
        ]
        
        for pattern in medication_patterns:
            matches = re.findall(pattern, full_text)
            entities["medications"].extend(matches)
        
        # Lab value patterns
        lab_patterns = [
            r'\\bhba1c\\s*[><=≥≤]?\\s*\\d+\\.?\\d*%?\\b',
            r'\\bcreatinine\\s*[><=≥≤]?\\s*\\d+\\.?\\d*\\b',
            r'\\bbmi\\s*[><=≥≤]?\\s*\\d+\\.?\\d*\\b',
            r'\\begfr\\s*[><=≥≤]?\\s*\\d+\\b'
        ]
        
        for pattern in lab_patterns:
            matches = re.findall(pattern, full_text)
            entities["lab_values"].extend(matches)
        
        # Demographic patterns
        demographic_patterns = [
            r'\b(?:pregnant|nursing|childbearing|postmenopausal)\b',
            r'\b(?:adult|pediatric|geriatric|elderly)\b'
        ]
        
        for pattern in demographic_patterns:
            matches = re.findall(pattern, full_text)
            entities["demographics"].extend(matches)
        
        # Remove duplicates and clean up
        for category in entities:
            entities[category] = list(set(entities[category]))
        
        self.extracted_entities = entities
        return entities
    
    def get_structured_criteria(self) -> Dict[str, Any]:
        """
        Convert criteria to structured format for AI matching.
        
        Returns organized data optimized for algorithmic processing.
        """
        if self.structured_requirements:
            return self.structured_requirements
        
        # Parse raw text if not already done
        if not self.inclusion_criteria and not self.exclusion_criteria:
            parsed = self.parse_raw_text()
            self.inclusion_criteria = parsed["inclusion_criteria"]
            self.exclusion_criteria = parsed["exclusion_criteria"]
            if not self.age_requirements:
                self.age_requirements = parsed.get("age_requirements")
            if self.gender_requirements == "all":
                self.gender_requirements = parsed.get("gender_requirements", "all")
        
        # Extract medical entities if not already done
        if not self.extracted_entities:
            self.extract_medical_entities()
        
        structured = {
            "age_requirements": self.age_requirements or {},
            "gender_requirements": self.gender_requirements,
            "medical_conditions": self.extracted_entities.get("conditions", []),
            "exclusion_conditions": self.extracted_entities.get("excluded_conditions", []),
            "required_medications": [],
            "excluded_medications": self.extracted_entities.get("medications", []),
            "required_procedures": [],
            "excluded_procedures": [],
            "lab_requirements": self.extracted_entities.get("lab_values", []),
            "demographic_requirements": self.extracted_entities.get("demographics", []),
            "inclusion_criteria": self.inclusion_criteria,
            "exclusion_criteria": self.exclusion_criteria,
            "special_populations": self._identify_special_populations()
        }
        
        self.structured_requirements = structured
        return structured
    
    def _identify_special_populations(self) -> List[str]:
        """Identify special population considerations."""
        special_pops = []
        full_text = f"{self.raw_text} {' '.join(self.inclusion_criteria + self.exclusion_criteria)}".lower()
        
        population_indicators = {
            "pediatric": ["child", "children", "pediatric", "under 18"],
            "geriatric": ["elderly", "geriatric", "over 65", "senior"],
            "pregnant": ["pregnant", "pregnancy", "expecting"],
            "nursing": ["nursing", "breastfeeding", "lactating"],
            "renal_impairment": ["kidney disease", "renal", "dialysis", "egfr"],
            "hepatic_impairment": ["liver disease", "hepatic", "cirrhosis"],
            "cognitive_impairment": ["dementia", "alzheimer", "cognitive"],
            "immunocompromised": ["immunocompromised", "immunosuppressed", "hiv"]
        }
        
        for population, indicators in population_indicators.items():
            if any(indicator in full_text for indicator in indicators):
                special_pops.append(population)
        
        return special_pops
    
    def check_patient_eligibility(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check patient eligibility against criteria.
        
        Args:
            patient_data: Patient information dict
            
        Returns:
            Eligibility assessment with detailed results
        """
        result = {
            "overall_eligible": True,
            "passed_criteria": [],
            "failed_criteria": [],
            "warnings": [],
            "confidence_score": 1.0
        }
        
        structured = self.get_structured_criteria()
        
        # Check age requirements
        if structured.get("age_requirements"):
            age_result = self._check_age_eligibility(patient_data, structured["age_requirements"])
            if age_result["passed"]:
                result["passed_criteria"].append(age_result)
            else:
                result["failed_criteria"].append(age_result)
                result["overall_eligible"] = False
        
        # Check gender requirements
        if structured.get("gender_requirements") != "all":
            gender_result = self._check_gender_eligibility(patient_data, structured["gender_requirements"])
            if gender_result["passed"]:
                result["passed_criteria"].append(gender_result)
            else:
                result["failed_criteria"].append(gender_result)
                result["overall_eligible"] = False
        
        # Check medical conditions
        condition_result = self._check_condition_eligibility(patient_data, structured)
        result["passed_criteria"].extend(condition_result["passed"])
        result["failed_criteria"].extend(condition_result["failed"])
        if condition_result["failed"]:
            result["overall_eligible"] = False
        
        # Calculate confidence score
        total_checks = len(result["passed_criteria"]) + len(result["failed_criteria"])
        if total_checks > 0:
            result["confidence_score"] = len(result["passed_criteria"]) / total_checks
        
        return result
    
    def _check_age_eligibility(self, patient_data: Dict[str, Any], age_req: Dict[str, Any]) -> Dict[str, Any]:
        """Check age eligibility."""
        patient_age = patient_data.get("age")
        if patient_age is None:
            return {
                "category": "age_check",
                "passed": False,
                "details": "Patient age not provided",
                "confidence": 0.0
            }
        
        min_age = age_req.get("min_age")
        max_age = age_req.get("max_age")
        
        passed = True
        details = []
        
        if min_age is not None and patient_age < min_age:
            passed = False
            details.append(f"Patient age {patient_age} below minimum {min_age}")
        
        if max_age is not None and patient_age > max_age:
            passed = False
            details.append(f"Patient age {patient_age} above maximum {max_age}")
        
        if passed:
            details.append(f"Patient age {patient_age} meets requirements")
        
        return {
            "category": "age_check",
            "passed": passed,
            "details": "; ".join(details),
            "confidence": 1.0
        }
    
    def _check_gender_eligibility(self, patient_data: Dict[str, Any], gender_req: str) -> Dict[str, Any]:
        """Check gender eligibility."""
        patient_gender = patient_data.get("gender", "").lower()
        
        if not patient_gender:
            return {
                "category": "gender_check",
                "passed": False,
                "details": "Patient gender not provided",
                "confidence": 0.0
            }
        
        passed = patient_gender == gender_req or gender_req == "all"
        details = f"Patient gender {patient_gender} {'meets' if passed else 'does not meet'} requirement {gender_req}"
        
        return {
            "category": "gender_check",
            "passed": passed,
            "details": details,
            "confidence": 1.0
        }
    
    def _check_condition_eligibility(self, patient_data: Dict[str, Any], structured: Dict[str, Any]) -> Dict[str, Any]:
        """Check medical condition eligibility."""
        patient_conditions = [c.lower() for c in patient_data.get("medical_conditions", [])]
        patient_medications = [m.lower() for m in patient_data.get("medications", [])]
        patient_allergies = [a.lower() for a in patient_data.get("allergies", [])]
        
        passed = []
        failed = []
        
        # Check required conditions (from inclusion criteria)
        required_conditions = [c.lower() for c in structured.get("medical_conditions", [])]
        for req_condition in required_conditions:
            has_condition = any(req_condition in pc for pc in patient_conditions)
            result = {
                "category": "condition_match",
                "passed": has_condition,
                "details": f"Required condition '{req_condition}' {'found' if has_condition else 'not found'}",
                "confidence": 0.8
            }
            
            if has_condition:
                passed.append(result)
            else:
                failed.append(result)
        
        # Check exclusion criteria
        for exclusion in self.exclusion_criteria:
            exclusion_lower = exclusion.lower()
            violated = False
            violation_details = []
            
            # Check for condition exclusions
            for condition in patient_conditions:
                if condition in exclusion_lower or any(word in exclusion_lower for word in condition.split()):
                    violated = True
                    violation_details.append(f"Patient has excluded condition: {condition}")
            
            # Check for medication exclusions
            for medication in patient_medications:
                if medication in exclusion_lower:
                    violated = True
                    violation_details.append(f"Patient takes excluded medication: {medication}")
            
            result = {
                "category": "exclusion_check",
                "passed": not violated,
                "details": "; ".join(violation_details) if violation_details else f"No exclusion violations for: {exclusion}",
                "confidence": 0.9
            }
            
            if not violated:
                passed.append(result)
            else:
                failed.append(result)
        
        return {"passed": passed, "failed": failed}
    
    def get_match_score(self, patient_data: Dict[str, Any]) -> float:
        """
        Calculate overall match score for patient.
        
        Returns score between 0.0 and 1.0 indicating compatibility.
        """
        eligibility = self.check_patient_eligibility(patient_data)
        
        if not eligibility["overall_eligible"]:
            return 0.0
        
        return eligibility["confidence_score"]
    
    def get_failed_criteria(self, patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of failed eligibility criteria for patient."""
        eligibility = self.check_patient_eligibility(patient_data)
        return eligibility["failed_criteria"]
    
    def calculate_similarity(self, patient_text: str) -> float:
        """
        Calculate semantic similarity with patient description.
        
        Args:
            patient_text: Text description of patient
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Simple similarity based on keyword overlap
        # In production, use actual semantic similarity (embeddings)
        
        criteria_text = f"{self.raw_text} {' '.join(self.inclusion_criteria + self.exclusion_criteria)}".lower()
        patient_text_lower = patient_text.lower()
        
        # Extract key medical terms
        medical_terms = set()
        for entity_list in self.extracted_entities.values() if self.extracted_entities else []:
            medical_terms.update([term.lower() for term in entity_list])
        
        # Count overlapping terms
        patient_words = set(re.findall(r'\\b\\w+\\b', patient_text_lower))
        overlap = len(medical_terms.intersection(patient_words))
        
        if len(medical_terms) == 0:
            return 0.5  # Neutral similarity if no terms extracted
        
        return min(1.0, overlap / len(medical_terms))
    
    def get_embedding(self) -> List[float]:
        """Generate embedding vector for semantic search."""
        # Placeholder implementation - use actual embedding service in production
        text = f"{self.raw_text} {' '.join(self.inclusion_criteria + self.exclusion_criteria)}"
        
        # Simple hash-based pseudo-embedding
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        embedding = []
        for i in range(0, len(hash_bytes), 2):
            if i + 1 < len(hash_bytes):
                value = (hash_bytes[i] + hash_bytes[i + 1]) / 512.0  # Normalize to [0, 1]
                embedding.append(value)
        
        # Pad to standard size
        while len(embedding) < 768:
            embedding.append(0.0)
        
        return embedding[:768]
    
    def get_complexity_score(self) -> float:
        """
        Calculate complexity score for criteria.
        
        Returns higher scores for more complex eligibility requirements.
        """
        if self.complexity_score is not None:
            return self.complexity_score
        
        score = 0.0
        
        # Count inclusion/exclusion criteria
        score += len(self.inclusion_criteria) * 0.5
        score += len(self.exclusion_criteria) * 0.7  # Exclusions are more complex
        
        # Add complexity for age requirements
        if self.age_requirements:
            score += 1.0
        
        # Add complexity for gender restrictions
        if self.gender_requirements and self.gender_requirements != "all":
            score += 1.0
        
        # Add complexity for extracted entities
        if self.extracted_entities:
            for entity_type, entities in self.extracted_entities.items():
                score += len(entities) * 0.3
        
        # Add complexity for special populations
        structured = self.get_structured_criteria()
        special_pops = structured.get("special_populations", [])
        score += len(special_pops) * 1.5
        
        self.complexity_score = score
        return score
    
    def validate_consistency(self) -> Dict[str, Any]:
        """
        Validate internal consistency of criteria.
        
        Checks for logical conflicts and potential issues.
        """
        validation = {
            "is_consistent": True,
            "warnings": [],
            "conflicts": []
        }
        
        # Check age consistency
        if self.age_requirements:
            min_age = self.age_requirements.get("min_age")
            max_age = self.age_requirements.get("max_age")
            
            if min_age is not None and max_age is not None:
                if min_age > max_age:
                    validation["is_consistent"] = False
                    validation["conflicts"].append("Minimum age greater than maximum age")
                
                if min_age == max_age:
                    validation["warnings"].append("Age range is a single value")
        
        # Check for contradictory inclusion/exclusion
        inclusion_text = " ".join(self.inclusion_criteria).lower()
        exclusion_text = " ".join(self.exclusion_criteria).lower()
        
        # Look for overlapping conditions
        if self.extracted_entities:
            inclusion_conditions = set()
            exclusion_conditions = set()
            
            # Simple overlap check
            common_words = set(inclusion_text.split()).intersection(set(exclusion_text.split()))
            medical_words = [word for word in common_words if len(word) > 4]  # Filter short words
            
            if medical_words:
                validation["warnings"].append(f"Potential overlap in criteria: {', '.join(medical_words)}")
        
        return validation
    
    def normalize_terminology(self) -> Dict[str, Any]:
        """
        Normalize medical terminology to standard codes.
        
        Maps extracted terms to standardized medical vocabularies.
        """
        normalized = {
            "standardized_conditions": {},
            "icd_codes": {},
            "snomed_codes": {},
            "unmapped_terms": []
        }
        
        if not self.extracted_entities:
            self.extract_medical_entities()
        
        # Simple mapping - in production, use actual medical ontologies
        condition_mappings = {
            "diabetes": {"icd10": "E11", "snomed": "44054006"},
            "hypertension": {"icd10": "I10", "snomed": "38341003"},
            "cancer": {"icd10": "C80", "snomed": "363346000"},
            "asthma": {"icd10": "J45", "snomed": "195967001"}
        }
        
        for condition in self.extracted_entities.get("conditions", []):
            condition_lower = condition.lower()
            mapped = False
            
            for standard_term, codes in condition_mappings.items():
                if standard_term in condition_lower:
                    normalized["standardized_conditions"][condition] = standard_term
                    normalized["icd_codes"][condition] = codes["icd10"]
                    normalized["snomed_codes"][condition] = codes["snomed"]
                    mapped = True
                    break
            
            if not mapped:
                normalized["unmapped_terms"].append(condition)
        
        return normalized
    
    def get_icd_codes(self) -> List[str]:
        """Get ICD-10 codes for conditions."""
        normalized = self.normalize_terminology()
        return list(normalized["icd_codes"].values())
    
    def get_snomed_codes(self) -> List[str]:
        """Get SNOMED-CT codes for conditions."""
        normalized = self.normalize_terminology()
        return list(normalized["snomed_codes"].values())
    
    def to_database_model(self) -> EligibilityCriteriaDB:
        """Convert to SQLAlchemy model for database persistence."""
        return EligibilityCriteriaDB(
            criteria_id=self.criteria_id,
            trial_nct_id=self.trial_nct_id,
            raw_text=self.raw_text,
            inclusion_criteria=self.inclusion_criteria,
            exclusion_criteria=self.exclusion_criteria,
            age_requirements=self.age_requirements,
            gender_requirements=self.gender_requirements,
            extracted_entities=self.extracted_entities,
            structured_requirements=self.structured_requirements,
            complexity_score=self.complexity_score,
            version=self.version,
            processing_metadata=self.processing_metadata,
            locale=self.locale,
            terminology_system=self.terminology_system,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_database_model(cls, db_model: EligibilityCriteriaDB) -> "EligibilityCriteria":
        """Create EligibilityCriteria from SQLAlchemy model."""
        return cls(
            criteria_id=db_model.criteria_id,
            trial_nct_id=db_model.trial_nct_id,
            raw_text=db_model.raw_text,
            inclusion_criteria=db_model.inclusion_criteria or [],
            exclusion_criteria=db_model.exclusion_criteria or [],
            age_requirements=db_model.age_requirements,
            gender_requirements=db_model.gender_requirements,
            extracted_entities=db_model.extracted_entities,
            structured_requirements=db_model.structured_requirements,
            complexity_score=db_model.complexity_score,
            version=db_model.version,
            processing_metadata=db_model.processing_metadata,
            locale=db_model.locale,
            terminology_system=db_model.terminology_system,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at
        )