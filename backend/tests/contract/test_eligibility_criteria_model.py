"""
Contract tests for EligibilityCriteria model with NLP processing.

These tests define the expected behavior for eligibility criteria parsing
and natural language processing in the MedMatch AI system.
"""
import pytest
from typing import Dict, Any, List, Optional
from pydantic import ValidationError


class TestEligibilityCriteriaModelContract:
    """Contract tests for EligibilityCriteria model behavior."""
    
    def test_eligibility_criteria_basic_structure(self):
        """EligibilityCriteria must have proper basic structure."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        valid_criteria_data = {
            "criteria_id": "CRIT-2025-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "Inclusion Criteria: Adults 18-65 years with Type 2 diabetes. Exclusion Criteria: Pregnant women.",
            "inclusion_criteria": [
                "Adults aged 18-65 years",
                "Diagnosed with Type 2 diabetes",
                "HbA1c between 7-12%"
            ],
            "exclusion_criteria": [
                "Pregnant or nursing women",
                "History of cardiac disease",
                "Current use of insulin"
            ],
            "age_requirements": {
                "min_age": 18,
                "max_age": 65,
                "age_units": "years"
            },
            "gender_requirements": "all"
        }
        
        criteria = EligibilityCriteria(**valid_criteria_data)
        assert criteria.criteria_id == "CRIT-2025-001"
        assert criteria.trial_nct_id == "NCT12345678"
        assert len(criteria.inclusion_criteria) == 3
        assert len(criteria.exclusion_criteria) == 3
        assert criteria.age_requirements["min_age"] == 18
        
    def test_age_requirements_validation(self):
        """Age requirements must be properly validated."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        base_data = {
            "criteria_id": "CRIT-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "Age criteria test",
            "inclusion_criteria": [],
            "exclusion_criteria": []
        }
        
        # Valid age requirements
        valid_age_reqs = [
            {"min_age": 18, "max_age": 65, "age_units": "years"},
            {"min_age": 0, "max_age": 17, "age_units": "years"},  # Pediatric
            {"min_age": 65, "max_age": 120, "age_units": "years"},  # Geriatric
            {"min_age": None, "max_age": 65, "age_units": "years"},  # Only max
            {"min_age": 18, "max_age": None, "age_units": "years"}  # Only min
        ]
        
        for age_req in valid_age_reqs:
            criteria = EligibilityCriteria(**base_data, age_requirements=age_req)
            assert criteria.age_requirements["age_units"] == "years"
            
        # Invalid age requirements
        invalid_age_reqs = [
            {"min_age": -1, "max_age": 65, "age_units": "years"},  # Negative age
            {"min_age": 65, "max_age": 18, "age_units": "years"},  # Min > Max
            {"min_age": 18, "max_age": 200, "age_units": "years"}  # Unrealistic max
        ]
        
        for age_req in invalid_age_reqs:
            with pytest.raises(ValidationError):
                EligibilityCriteria(**base_data, age_requirements=age_req)
                
    def test_gender_requirements_validation(self):
        """Gender requirements must be from valid options."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        base_data = {
            "criteria_id": "CRIT-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "Gender criteria test",
            "inclusion_criteria": [],
            "exclusion_criteria": []
        }
        
        valid_genders = ["all", "male", "female", "other", "prefer_not_to_say"]
        
        for gender in valid_genders:
            criteria = EligibilityCriteria(**base_data, gender_requirements=gender)
            assert criteria.gender_requirements == gender
            
        # Invalid gender should raise ValidationError
        with pytest.raises(ValidationError):
            EligibilityCriteria(**base_data, gender_requirements="invalid_gender")
            
    def test_nlp_processing_capabilities(self):
        """EligibilityCriteria must support NLP processing."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        raw_criteria_text = """
        Inclusion Criteria:
        1. Adults aged 18-65 years
        2. Diagnosed with Type 2 diabetes mellitus for at least 6 months
        3. HbA1c between 7.0% and 12.0%
        4. BMI between 25-45 kg/m²
        
        Exclusion Criteria:
        1. Pregnant or nursing women
        2. History of myocardial infarction
        3. Current use of insulin therapy
        4. Severe kidney disease (eGFR < 30)
        """
        
        criteria_data = {
            "criteria_id": "CRIT-NLP-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": raw_criteria_text,
            "inclusion_criteria": [],
            "exclusion_criteria": []
        }
        
        criteria = EligibilityCriteria(**criteria_data)
        
        # Should support NLP processing methods
        assert hasattr(criteria, 'parse_raw_text'), "Must support raw text parsing"
        assert hasattr(criteria, 'extract_medical_entities'), "Must extract medical entities"
        assert hasattr(criteria, 'get_structured_criteria'), "Must provide structured output"
        
        # Parse raw text into structured format
        structured = criteria.get_structured_criteria()
        assert isinstance(structured, dict)
        assert "age_requirements" in structured
        assert "medical_conditions" in structured
        assert "exclusion_conditions" in structured
        
    def test_medical_entity_extraction(self):
        """EligibilityCriteria must extract medical entities."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        criteria_data = {
            "criteria_id": "CRIT-ENTITY-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "Patients with diabetes, hypertension, or asthma. Exclude those with cancer or heart disease.",
            "inclusion_criteria": ["Diabetes", "Hypertension", "Asthma"],
            "exclusion_criteria": ["Cancer", "Heart disease"]
        }
        
        criteria = EligibilityCriteria(**criteria_data)
        
        # Should extract medical entities
        entities = criteria.extract_medical_entities()
        assert isinstance(entities, dict)
        assert "conditions" in entities
        assert "medications" in entities or "drugs" in entities
        assert "procedures" in entities
        
        # Should identify condition entities
        conditions = entities["conditions"]
        expected_conditions = ["diabetes", "hypertension", "asthma", "cancer", "heart disease"]
        for condition in expected_conditions:
            assert any(condition in c.lower() for c in conditions)
            
    def test_criteria_matching_logic(self):
        """EligibilityCriteria must support patient matching logic."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        criteria_data = {
            "criteria_id": "CRIT-MATCH-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "Adults 18-65 with diabetes, no pregnancy",
            "inclusion_criteria": ["Adults aged 18-65", "Type 2 diabetes"],
            "exclusion_criteria": ["Pregnancy"],
            "age_requirements": {"min_age": 18, "max_age": 65, "age_units": "years"},
            "gender_requirements": "all"
        }
        
        criteria = EligibilityCriteria(**criteria_data)
        
        # Should support patient matching
        assert hasattr(criteria, 'check_patient_eligibility'), "Must check patient eligibility"
        assert hasattr(criteria, 'get_match_score'), "Must calculate match score"
        assert hasattr(criteria, 'get_failed_criteria'), "Must identify failed criteria"
        
        # Mock patient data for testing
        patient_data = {
            "age": 45,
            "gender": "female",
            "medical_conditions": ["diabetes"],
            "medications": ["metformin"],
            "allergies": []
        }
        
        eligibility_result = criteria.check_patient_eligibility(patient_data)
        assert isinstance(eligibility_result, dict)
        assert "overall_eligible" in eligibility_result
        assert "passed_criteria" in eligibility_result
        assert "failed_criteria" in eligibility_result
        
    def test_criteria_complexity_scoring(self):
        """EligibilityCriteria must assess complexity."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        # Simple criteria
        simple_criteria = EligibilityCriteria(
            criteria_id="CRIT-SIMPLE",
            trial_nct_id="NCT12345678",
            raw_text="Adults 18-65 years",
            inclusion_criteria=["Adults aged 18-65"],
            exclusion_criteria=[],
            age_requirements={"min_age": 18, "max_age": 65, "age_units": "years"}
        )
        
        # Complex criteria
        complex_criteria = EligibilityCriteria(
            criteria_id="CRIT-COMPLEX",
            trial_nct_id="NCT87654321",
            raw_text="Complex multi-condition study",
            inclusion_criteria=[
                "Type 2 diabetes with HbA1c 7-12%",
                "BMI 25-45 kg/m²",
                "Stable medications for 3 months",
                "Ability to provide informed consent"
            ],
            exclusion_criteria=[
                "Type 1 diabetes",
                "Pregnancy or nursing",
                "Severe kidney disease",
                "Recent cardiovascular events",
                "Active cancer treatment"
            ]
        )
        
        # Should assess complexity
        assert hasattr(simple_criteria, 'get_complexity_score'), "Must assess complexity"
        
        simple_score = simple_criteria.get_complexity_score()
        complex_score = complex_criteria.get_complexity_score()
        
        assert isinstance(simple_score, (int, float))
        assert isinstance(complex_score, (int, float))
        assert complex_score > simple_score, "Complex criteria should have higher score"
        
    def test_criteria_semantic_similarity(self):
        """EligibilityCriteria must support semantic similarity."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        criteria_data = {
            "criteria_id": "CRIT-SIM-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "Diabetes study criteria",
            "inclusion_criteria": ["Type 2 diabetes", "Adults"],
            "exclusion_criteria": ["Pregnancy"]
        }
        
        criteria = EligibilityCriteria(**criteria_data)
        
        # Should support semantic similarity
        assert hasattr(criteria, 'calculate_similarity'), "Must calculate semantic similarity"
        assert hasattr(criteria, 'get_embedding'), "Must generate embeddings"
        
        # Test similarity with patient text
        patient_text = "45-year-old female with diabetes mellitus type 2"
        similarity_score = criteria.calculate_similarity(patient_text)
        
        assert isinstance(similarity_score, (int, float))
        assert 0.0 <= similarity_score <= 1.0, "Similarity score must be between 0 and 1"
        
    def test_criteria_validation_rules(self):
        """EligibilityCriteria must validate business rules."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        # Should validate that criteria make medical sense
        valid_criteria = {
            "criteria_id": "CRIT-VALID-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "Valid diabetes study",
            "inclusion_criteria": ["Type 2 diabetes", "HbA1c > 7%"],
            "exclusion_criteria": ["Type 1 diabetes"],
            "age_requirements": {"min_age": 18, "max_age": 75, "age_units": "years"}
        }
        
        criteria = EligibilityCriteria(**valid_criteria)
        
        # Should validate internal consistency
        assert hasattr(criteria, 'validate_consistency'), "Must validate criteria consistency"
        validation_result = criteria.validate_consistency()
        
        assert isinstance(validation_result, dict)
        assert "is_consistent" in validation_result
        assert "warnings" in validation_result
        assert "conflicts" in validation_result
        
    def test_criteria_localization_support(self):
        """EligibilityCriteria must support multiple languages/formats."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        criteria_data = {
            "criteria_id": "CRIT-LOCALE-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "International study criteria",
            "inclusion_criteria": ["Diabetes mellitus type 2"],
            "exclusion_criteria": ["Pregnancy"],
            "locale": "en-US",
            "terminology_system": "SNOMED-CT"
        }
        
        criteria = EligibilityCriteria(**criteria_data)
        
        # Should support different medical terminologies
        assert hasattr(criteria, 'normalize_terminology'), "Must normalize medical terms"
        assert hasattr(criteria, 'get_icd_codes'), "Must map to ICD codes"
        assert hasattr(criteria, 'get_snomed_codes'), "Must map to SNOMED codes"
        
        # Normalize medical terminology
        normalized = criteria.normalize_terminology()
        assert isinstance(normalized, dict)
        assert "standardized_conditions" in normalized
        
    def test_criteria_audit_and_versioning(self):
        """EligibilityCriteria must support audit trail."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        criteria_data = {
            "criteria_id": "CRIT-AUDIT-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "Auditable criteria",
            "inclusion_criteria": ["Diabetes"],
            "exclusion_criteria": ["Pregnancy"],
            "version": "1.0",
            "created_at": "2025-09-30T10:00:00Z",
            "processing_metadata": {
                "nlp_model_version": "spacy-3.7",
                "extraction_confidence": 0.95,
                "manual_review_required": False
            }
        }
        
        criteria = EligibilityCriteria(**criteria_data)
        
        # Should track processing metadata
        assert hasattr(criteria, 'processing_metadata'), "Must track processing metadata"
        assert criteria.processing_metadata["nlp_model_version"] == "spacy-3.7"
        assert criteria.processing_metadata["extraction_confidence"] == 0.95
        
        # Should support versioning
        assert hasattr(criteria, 'version'), "Must support versioning"
        assert criteria.version == "1.0"
        
    def test_criteria_serialization(self):
        """EligibilityCriteria must serialize/deserialize correctly."""
        from src.models.eligibility_criteria import EligibilityCriteria
        
        original_data = {
            "criteria_id": "CRIT-SERIAL-001",
            "trial_nct_id": "NCT12345678",
            "raw_text": "Serialization test criteria",
            "inclusion_criteria": ["Diabetes", "Age 18-65"],
            "exclusion_criteria": ["Pregnancy", "Cancer"],
            "age_requirements": {"min_age": 18, "max_age": 65, "age_units": "years"},
            "gender_requirements": "all"
        }
        
        # Create, serialize, and deserialize
        criteria = EligibilityCriteria(**original_data)
        serialized = criteria.model_dump()
        deserialized = EligibilityCriteria(**serialized)
        
        assert deserialized.criteria_id == criteria.criteria_id
        assert deserialized.trial_nct_id == criteria.trial_nct_id
        assert deserialized.inclusion_criteria == criteria.inclusion_criteria
        assert deserialized.exclusion_criteria == criteria.exclusion_criteria
        assert deserialized.age_requirements == criteria.age_requirements
