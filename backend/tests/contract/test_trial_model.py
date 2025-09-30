"""
Contract tests for Trial model with embeddings support.

These tests define the expected behavior for clinical trial data handling
and vector embedding integration in the MedMatch AI system.
"""
import pytest
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from pydantic import ValidationError
import numpy as np


class TestTrialModelContract:
    """Contract tests for Trial model behavior."""
    
    def test_trial_basic_information_validation(self):
        """Trial must validate basic trial information."""
        from backend.src.models.trial import Trial
        
        valid_trial_data = {
            "nct_id": "NCT12345678",
            "title": "A Study of Drug X in Patients with Condition Y",
            "brief_summary": "This study evaluates the safety and efficacy of Drug X...",
            "detailed_description": "Detailed protocol information...",
            "primary_purpose": "treatment",
            "phase": "Phase 2",
            "status": "recruiting",
            "enrollment": 100,
            "study_type": "interventional",
            "sponsor": "University Medical Center",
            "location": "Boston, MA, USA",
            "conditions": ["diabetes", "hypertension"],
            "interventions": ["Drug X", "placebo"],
            "eligibility_criteria": {
                "min_age": 18,
                "max_age": 65,
                "gender": "all",
                "inclusion_criteria": ["Diagnosed with Type 2 diabetes"],
                "exclusion_criteria": ["Pregnant women"]
            }
        }
        
        trial = Trial(**valid_trial_data)
        assert trial.nct_id == "NCT12345678"
        assert trial.title.startswith("A Study of Drug X")
        assert trial.phase == "Phase 2"
        assert trial.status == "recruiting"
        assert trial.enrollment == 100
        
    def test_trial_nct_id_validation(self):
        """NCT ID must follow ClinicalTrials.gov format."""
        from backend.src.models.trial import Trial
        
        base_data = {
            "title": "Test Study",
            "brief_summary": "Test summary",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional"
        }
        
        # Valid NCT ID formats
        valid_nct_ids = [
            "NCT12345678",
            "NCT00000001",
            "NCT99999999"
        ]
        
        for nct_id in valid_nct_ids:
            trial = Trial(**base_data, nct_id=nct_id)
            assert trial.nct_id == nct_id
            
        # Invalid NCT IDs should raise ValidationError
        invalid_nct_ids = [
            "12345678",  # Missing NCT prefix
            "NCT1234567",  # Too short
            "NCT123456789",  # Too long
            "nct12345678",  # Lowercase
            "NCT1234567A"  # Contains letter
        ]
        
        for nct_id in invalid_nct_ids:
            with pytest.raises(ValidationError):
                Trial(**base_data, nct_id=nct_id)
                
    def test_trial_status_validation(self):
        """Trial status must be from valid ClinicalTrials.gov options."""
        from backend.src.models.trial import Trial
        
        base_data = {
            "nct_id": "NCT12345678",
            "title": "Test Study",
            "brief_summary": "Test summary",
            "primary_purpose": "treatment",
            "study_type": "interventional"
        }
        
        valid_statuses = [
            "recruiting",
            "not_yet_recruiting",
            "active_not_recruiting",
            "completed",
            "suspended",
            "terminated",
            "withdrawn"
        ]
        
        for status in valid_statuses:
            trial = Trial(**base_data, status=status)
            assert trial.status == status
            
        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            Trial(**base_data, status="invalid_status")
            
    def test_trial_phase_validation(self):
        """Trial phase must be from valid options."""
        from backend.src.models.trial import Trial
        
        base_data = {
            "nct_id": "NCT12345678",
            "title": "Test Study",
            "brief_summary": "Test summary",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional"
        }
        
        valid_phases = [
            "Early Phase 1",
            "Phase 1",
            "Phase 1/Phase 2",
            "Phase 2",
            "Phase 2/Phase 3",
            "Phase 3",
            "Phase 4",
            "Not Applicable"
        ]
        
        for phase in valid_phases:
            trial = Trial(**base_data, phase=phase)
            assert trial.phase == phase
            
    def test_trial_eligibility_criteria_structure(self):
        """Eligibility criteria must have proper structure."""
        from backend.src.models.trial import Trial
        
        base_data = {
            "nct_id": "NCT12345678",
            "title": "Test Study",
            "brief_summary": "Test summary",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional"
        }
        
        valid_eligibility = {
            "min_age": 18,
            "max_age": 65,
            "gender": "all",
            "inclusion_criteria": [
                "Adults aged 18-65 years",
                "Diagnosed with Type 2 diabetes"
            ],
            "exclusion_criteria": [
                "Pregnant or nursing women",
                "History of cardiac disease"
            ]
        }
        
        trial = Trial(**base_data, eligibility_criteria=valid_eligibility)
        assert trial.eligibility_criteria["min_age"] == 18
        assert trial.eligibility_criteria["max_age"] == 65
        assert trial.eligibility_criteria["gender"] == "all"
        assert len(trial.eligibility_criteria["inclusion_criteria"]) == 2
        assert len(trial.eligibility_criteria["exclusion_criteria"]) == 2
        
    def test_trial_vector_embedding_support(self):
        """Trial must support vector embeddings for semantic search."""
        from backend.src.models.trial import Trial
        
        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Diabetes Treatment Study",
            "brief_summary": "Testing new diabetes medication",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional",
            "conditions": ["diabetes"],
            "interventions": ["metformin analog"]
        }
        
        trial = Trial(**trial_data)
        
        # Trial should support embedding generation
        assert hasattr(trial, 'generate_embedding'), "Trial must support embedding generation"
        assert hasattr(trial, 'embedding'), "Trial must store embedding vector"
        assert hasattr(trial, 'get_embedding_text'), "Trial must provide text for embedding"
        
        # Embedding text should combine key fields
        embedding_text = trial.get_embedding_text()
        assert isinstance(embedding_text, str)
        assert "diabetes" in embedding_text.lower()
        assert "treatment" in embedding_text.lower()
        
    def test_trial_embedding_vector_format(self):
        """Trial embedding must be proper vector format."""
        from backend.src.models.trial import Trial
        
        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Test Study",
            "brief_summary": "Test summary",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional"
        }
        
        trial = Trial(**trial_data)
        
        # Set mock embedding (real implementation will use AI service)
        mock_embedding = np.random.rand(768).tolist()  # 768-dim vector
        trial.embedding = mock_embedding
        
        assert trial.embedding is not None
        assert isinstance(trial.embedding, list)
        assert len(trial.embedding) == 768
        assert all(isinstance(x, (int, float)) for x in trial.embedding)
        
    def test_trial_search_compatibility(self):
        """Trial must be compatible with hybrid search engine."""
        from backend.src.models.trial import Trial
        
        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Novel Cancer Immunotherapy Study",
            "brief_summary": "Testing CAR-T cell therapy for lymphoma",
            "conditions": ["lymphoma", "cancer"],
            "interventions": ["CAR-T cells"],
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional"
        }
        
        trial = Trial(**trial_data)
        
        # Trial should provide search-ready data
        assert hasattr(trial, 'get_search_keywords'), "Trial must provide search keywords"
        assert hasattr(trial, 'get_lexical_search_text'), "Trial must provide lexical search text"
        
        keywords = trial.get_search_keywords()
        assert isinstance(keywords, list)
        assert "lymphoma" in [k.lower() for k in keywords]
        assert "cancer" in [k.lower() for k in keywords]
        
        lexical_text = trial.get_lexical_search_text()
        assert isinstance(lexical_text, str)
        assert "car-t" in lexical_text.lower() or "immunotherapy" in lexical_text.lower()
        
    def test_trial_eligibility_matching_data(self):
        """Trial must provide data for eligibility matching."""
        from backend.src.models.trial import Trial
        
        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Diabetes Study",
            "brief_summary": "Testing diabetes treatment",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional",
            "eligibility_criteria": {
                "min_age": 18,
                "max_age": 65,
                "gender": "all",
                "inclusion_criteria": ["Type 2 diabetes", "HbA1c > 7%"],
                "exclusion_criteria": ["Pregnancy", "Kidney disease"]
            }
        }
        
        trial = Trial(**trial_data)
        
        # Trial should provide structured eligibility data
        assert hasattr(trial, 'get_eligibility_requirements'), "Trial must provide eligibility requirements"
        requirements = trial.get_eligibility_requirements()
        
        assert "age_range" in requirements
        assert "gender_requirements" in requirements
        assert "medical_conditions" in requirements
        assert "exclusion_conditions" in requirements
        
    def test_trial_location_and_contact_info(self):
        """Trial must handle location and contact information."""
        from backend.src.models.trial import Trial
        
        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Multi-center Study",
            "brief_summary": "Testing across multiple locations",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional",
            "locations": [
                {
                    "facility": "University Hospital",
                    "city": "Boston",
                    "state": "MA",
                    "country": "USA",
                    "zip_code": "02115",
                    "contact_phone": "617-555-0123",
                    "contact_email": "study@hospital.edu"
                },
                {
                    "facility": "Medical Center",
                    "city": "New York",
                    "state": "NY",
                    "country": "USA",
                    "zip_code": "10016"
                }
            ]
        }
        
        trial = Trial(**trial_data)
        assert hasattr(trial, 'locations'), "Trial must support multiple locations"
        assert len(trial.locations) == 2
        assert trial.locations[0]["city"] == "Boston"
        assert trial.locations[1]["city"] == "New York"
        
    def test_trial_enrollment_and_timeline(self):
        """Trial must track enrollment and timeline information."""
        from backend.src.models.trial import Trial
        
        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Timeline Study",
            "brief_summary": "Testing with specific timeline",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional",
            "enrollment": 200,
            "estimated_enrollment": 250,
            "start_date": "2025-01-01",
            "completion_date": "2026-12-31",
            "primary_completion_date": "2026-06-30"
        }
        
        trial = Trial(**trial_data)
        assert trial.enrollment == 200
        assert trial.estimated_enrollment == 250
        assert trial.start_date == "2025-01-01"
        assert trial.completion_date == "2026-12-31"
        
    def test_trial_primary_outcome_measures(self):
        """Trial must track primary outcome measures."""
        from backend.src.models.trial import Trial
        
        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Outcome Study",
            "brief_summary": "Testing specific outcomes",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional",
            "primary_outcomes": [
                {
                    "measure": "Change in HbA1c",
                    "time_frame": "12 weeks",
                    "description": "Change from baseline HbA1c at 12 weeks"
                },
                {
                    "measure": "Safety Assessment",
                    "time_frame": "Throughout study",
                    "description": "Number of adverse events"
                }
            ]
        }
        
        trial = Trial(**trial_data)
        assert hasattr(trial, 'primary_outcomes'), "Trial must track primary outcomes"
        assert len(trial.primary_outcomes) == 2
        assert trial.primary_outcomes[0]["measure"] == "Change in HbA1c"
        
    def test_trial_serialization_with_embeddings(self):
        """Trial must serialize/deserialize including embeddings."""
        from backend.src.models.trial import Trial
        
        original_data = {
            "nct_id": "NCT12345678",
            "title": "Serialization Test Study",
            "brief_summary": "Testing serialization",
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional",
            "conditions": ["diabetes"],
            "interventions": ["medication"]
        }
        
        # Create trial with embedding
        trial = Trial(**original_data)
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        trial.embedding = mock_embedding
        
        # Serialize and deserialize
        serialized = trial.model_dump()
        deserialized_trial = Trial(**serialized)
        
        assert deserialized_trial.nct_id == trial.nct_id
        assert deserialized_trial.title == trial.title
        assert deserialized_trial.embedding == trial.embedding