"""
Contract tests for Patient model validation.

These tests define the expected behavior and data validation rules
for patient data handling in the MedMatch AI system.
"""
import pytest
from typing import Dict, Any, List
from datetime import date
from pydantic import ValidationError


class TestPatientModelContract:
    """Contract tests for Patient model behavior."""
    
    def test_patient_basic_demographics_validation(self):
        """Patient must validate basic demographic data."""
        # This test will pass once Patient model is implemented
        from backend.src.models.patient import Patient
        
        valid_patient_data = {
            "patient_id": "PAT-2025-001",
            "age": 45,
            "gender": "female",
            "medical_conditions": ["diabetes", "hypertension"],
            "medications": ["metformin", "lisinopril"],
            "allergies": ["penicillin"],
            "created_at": "2025-09-30T10:00:00Z"
        }
        
        patient = Patient(**valid_patient_data)
        assert patient.patient_id == "PAT-2025-001"
        assert patient.age == 45
        assert patient.gender == "female"
        assert len(patient.medical_conditions) == 2
        
    def test_patient_age_validation(self):
        """Patient age must be within valid range."""
        from backend.src.models.patient import Patient
        
        # Valid ages
        valid_ages = [18, 25, 65, 100]
        for age in valid_ages:
            patient_data = {
                "patient_id": f"PAT-{age}",
                "age": age,
                "gender": "male",
                "medical_conditions": [],
                "medications": [],
                "allergies": []
            }
            patient = Patient(**patient_data)
            assert patient.age == age
            
        # Invalid ages should raise ValidationError
        invalid_ages = [-1, 0, 17, 101, 150]
        for age in invalid_ages:
            with pytest.raises(ValidationError):
                Patient(patient_id="INVALID", age=age, gender="male")
                
    def test_patient_gender_validation(self):
        """Patient gender must be from valid options."""
        from backend.src.models.patient import Patient
        
        valid_genders = ["male", "female", "other", "prefer_not_to_say"]
        base_data = {
            "patient_id": "PAT-001",
            "age": 30,
            "medical_conditions": [],
            "medications": [],
            "allergies": []
        }
        
        for gender in valid_genders:
            patient = Patient(**base_data, gender=gender)
            assert patient.gender == gender
            
        # Invalid gender should raise ValidationError
        with pytest.raises(ValidationError):
            Patient(**base_data, gender="invalid_gender")
            
    def test_patient_medical_conditions_format(self):
        """Medical conditions must be properly formatted."""
        from backend.src.models.patient import Patient
        
        base_data = {
            "patient_id": "PAT-001",
            "age": 30,
            "gender": "male",
            "medications": [],
            "allergies": []
        }
        
        # Valid medical conditions formats
        valid_conditions = [
            [],  # No conditions
            ["diabetes"],  # Single condition
            ["diabetes", "hypertension", "asthma"],  # Multiple conditions
            ["Type 2 Diabetes Mellitus", "Essential Hypertension"]  # Detailed names
        ]
        
        for conditions in valid_conditions:
            patient = Patient(**base_data, medical_conditions=conditions)
            assert patient.medical_conditions == conditions
            
    def test_patient_medication_validation(self):
        """Medications must be properly validated."""
        from backend.src.models.patient import Patient
        
        base_data = {
            "patient_id": "PAT-001",
            "age": 30,
            "gender": "female",
            "medical_conditions": [],
            "allergies": []
        }
        
        valid_medications = [
            [],  # No medications
            ["aspirin"],  # Single medication
            ["metformin", "insulin", "lisinopril"],  # Multiple medications
            ["Metformin HCl 500mg", "Lisinopril 10mg"]  # Detailed prescriptions
        ]
        
        for medications in valid_medications:
            patient = Patient(**base_data, medications=medications)
            assert patient.medications == medications
            
    def test_patient_allergy_tracking(self):
        """Patient allergies must be properly tracked."""
        from backend.src.models.patient import Patient
        
        base_data = {
            "patient_id": "PAT-001",
            "age": 30,
            "gender": "male",
            "medical_conditions": [],
            "medications": []
        }
        
        valid_allergies = [
            [],  # No allergies
            ["penicillin"],  # Single allergy
            ["penicillin", "shellfish", "latex"],  # Multiple allergies
            ["Penicillin G", "Tree nuts", "Latex gloves"]  # Detailed allergies
        ]
        
        for allergies in valid_allergies:
            patient = Patient(**base_data, allergies=allergies)
            assert patient.allergies == allergies
            
    def test_patient_id_format_validation(self):
        """Patient ID must follow expected format."""
        from backend.src.models.patient import Patient
        
        base_data = {
            "age": 30,
            "gender": "male",
            "medical_conditions": [],
            "medications": [],
            "allergies": []
        }
        
        # Valid patient ID formats
        valid_ids = [
            "PAT-2025-001",
            "PAT-001",
            "PATIENT-12345",
            "P001",
            "patient_123"
        ]
        
        for patient_id in valid_ids:
            patient = Patient(**base_data, patient_id=patient_id)
            assert patient.patient_id == patient_id
            
        # Invalid IDs should raise ValidationError
        invalid_ids = ["", "   ", None]
        for patient_id in invalid_ids:
            with pytest.raises(ValidationError):
                Patient(**base_data, patient_id=patient_id)
                
    def test_patient_privacy_compliance(self):
        """Patient model must support HIPAA privacy requirements."""
        from backend.src.models.patient import Patient
        
        patient_data = {
            "patient_id": "PAT-2025-001",
            "age": 45,
            "gender": "female",
            "medical_conditions": ["diabetes"],
            "medications": ["metformin"],
            "allergies": ["penicillin"]
        }
        
        patient = Patient(**patient_data)
        
        # Patient should have methods for data protection
        assert hasattr(patient, 'get_anonymized_data'), "Patient must support data anonymization"
        assert hasattr(patient, 'get_audit_log'), "Patient must support audit logging"
        
        # Anonymized data should not contain patient_id
        anonymized = patient.get_anonymized_data()
        assert "patient_id" not in anonymized or anonymized["patient_id"] != patient.patient_id
        
    def test_patient_search_compatibility(self):
        """Patient data must be compatible with AI search pipeline."""
        from backend.src.models.patient import Patient
        
        patient_data = {
            "patient_id": "PAT-2025-001",
            "age": 45,
            "gender": "female",
            "medical_conditions": ["Type 2 Diabetes", "Hypertension"],
            "medications": ["Metformin", "Lisinopril"],
            "allergies": ["Penicillin"]
        }
        
        patient = Patient(**patient_data)
        
        # Patient should provide search-ready text representation
        assert hasattr(patient, 'get_search_text'), "Patient must provide search text"
        search_text = patient.get_search_text()
        assert isinstance(search_text, str)
        assert "diabetes" in search_text.lower()
        assert "hypertension" in search_text.lower()
        
    def test_patient_eligibility_data_extraction(self):
        """Patient must provide data for eligibility checking."""
        from backend.src.models.patient import Patient
        
        patient_data = {
            "patient_id": "PAT-2025-001",
            "age": 45,
            "gender": "female",
            "medical_conditions": ["diabetes", "hypertension"],
            "medications": ["metformin"],
            "allergies": ["penicillin"]
        }
        
        patient = Patient(**patient_data)
        
        # Patient should provide eligibility criteria data
        assert hasattr(patient, 'get_eligibility_data'), "Patient must provide eligibility data"
        eligibility_data = patient.get_eligibility_data()
        
        # Must include key eligibility fields
        required_fields = ["age", "gender", "medical_conditions", "medications", "allergies"]
        for field in required_fields:
            assert field in eligibility_data, f"Missing eligibility field: {field}"
            
    def test_patient_serialization_deserialization(self):
        """Patient data must serialize/deserialize correctly."""
        from backend.src.models.patient import Patient
        
        original_data = {
            "patient_id": "PAT-2025-001",
            "age": 45,
            "gender": "female",
            "medical_conditions": ["diabetes", "hypertension"],
            "medications": ["metformin", "lisinopril"],
            "allergies": ["penicillin"]
        }
        
        # Create patient and serialize
        patient = Patient(**original_data)
        serialized = patient.model_dump()
        
        # Deserialize and verify
        deserialized_patient = Patient(**serialized)
        assert deserialized_patient.patient_id == patient.patient_id
        assert deserialized_patient.age == patient.age
        assert deserialized_patient.medical_conditions == patient.medical_conditions