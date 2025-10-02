"""
Contract tests for the trial matching endpoint.
Tests POST /api/v1/match functionality.
"""
import pytest
from pydantic import BaseModel

from src.api.endpoints.match import MatchRequest, PatientData
from src.models.patient import Patient
from src.models.match_result import MatchResult

@pytest.fixture
def sample_patient_data():
    return {
        "medical_history": "65-year-old female with stage 2 breast cancer, ER+/PR+, HER2-",
        "current_medications": ["anastrozole", "calcium supplements"],
        "allergies": ["penicillin"],
        "vital_signs": {
            "blood_pressure": "120/80",
            "heart_rate": 72,
            "temperature": 98.6
        },
        "lab_results": {
            "white_blood_cell_count": 7.5,
            "hemoglobin": 12.8,
            "platelet_count": 250
        }
    }

def test_match_endpoint_successful_response(client, sample_patient_data):
    """Test successful trial matching with valid patient data."""
    request_data = MatchRequest(
        patient_data=PatientData(**sample_patient_data),
        max_results=3,
        min_confidence=0.7
    )
    
    response = client.post("/api/v1/match", json=request_data.model_dump())
    
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert len(data["matches"]) <= 3
    
    # Validate match result structure
    for match in data["matches"]:
        assert "trial_id" in match
        assert "confidence_score" in match
        assert match["confidence_score"] >= 0.7
        assert "reasoning" in match
        assert isinstance(match["reasoning"], dict)  # Reasoning is now a structured dict
        
def test_match_endpoint_invalid_patient_data(client):
    """Test error handling for invalid patient data."""
    invalid_data = {
        "patient_data": {},  # Empty patient data
        "max_results": 3
    }
    
    response = client.post("/api/v1/match", json=invalid_data)
    assert response.status_code == 422
    
def test_match_endpoint_invalid_request_params(client, sample_patient_data):
    """Test validation of request parameters."""
    patient_data = PatientData(**sample_patient_data)
    invalid_params = {
        "patient_data": patient_data.model_dump(),
        "max_results": 0,  # Invalid: must be positive
        "min_confidence": 1.5  # Invalid: must be between 0 and 1
    }
    
    response = client.post("/api/v1/match", json=invalid_params)
    assert response.status_code == 422

def test_match_endpoint_no_matches(client):
    """Test handling of no matching trials found."""
    patient_data = PatientData(
        medical_history="Healthy individual with no conditions",
        current_medications=[],
        vital_signs={
            "blood_pressure": "120/80",
            "heart_rate": 70,
            "temperature": 98.6
        }
    )
    
    request_data = MatchRequest(
        patient_data=patient_data,
        min_confidence=0.9
    )
    
    response = client.post("/api/v1/match", json=request_data.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["matches"] == []
    assert "message" in data

def test_match_endpoint_performance_metadata(client, sample_patient_data):
    """Test response time meets performance requirements."""
    import time
    
    patient_data = PatientData(**sample_patient_data)
    request_data = MatchRequest(
        patient_data=patient_data
    )
    
    start_time = time.time()
    response = client.post("/api/v1/match", json=request_data.model_dump())
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Ensure response within 1000ms

def test_llama_3_3_70b_reasoning_chain(client, sample_patient_data):
    """Test that Llama 3.3-70B provides detailed medical reasoning chains."""
    patient_data = PatientData(**sample_patient_data)
    request_data = MatchRequest(
        patient_data=patient_data
    )
    
    response = client.post("/api/v1/match", json=request_data.model_dump())
    
    assert response.status_code == 200
    data = response.json()
    
    for match in data["matches"]:
        reasoning = match["reasoning"]
        
        # Verify Llama 3.3-70B reasoning structure
        assert "chain_of_thought" in reasoning
        assert "medical_analysis" in reasoning
        assert "eligibility_assessment" in reasoning
        assert "contraindication_check" in reasoning
        
        # Verify reasoning quality (Llama 3.3-70B should provide detailed analysis)
        cot = reasoning["chain_of_thought"]
        assert len(cot) >= 3  # Multiple reasoning steps
        assert any("cancer" in step.lower() for step in cot)
        assert any("eligibility" in step.lower() for step in cot)

def test_cerebras_api_integration(client):
    """Test integration with Cerebras API for award-winning performance."""
    patient_data = PatientData(
        medical_history="67-year-old male with metastatic lung cancer, EGFR mutation positive",
        current_medications=["osimertinib", "dexamethasone"],
        performance_status={"ECOG": 1},  # Convert to dict
        biomarkers={"EGFR": "L858R mutation", "PD_L1": "60% expression"}
    )
    
    request_data = MatchRequest(patient_data=patient_data)
    
    response = client.post("/api/v1/match", json=request_data.model_dump())
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify Cerebras-powered features
    assert "processing_metadata" in data
    metadata = data["processing_metadata"]
    assert "model_used" in metadata
    assert "llama3.3-70b" in metadata["model_used"].lower()
    assert "inference_time_ms" in metadata
    
    # Should be fast due to Cerebras optimization
    assert metadata["inference_time_ms"] < 500

def test_medical_entity_extraction_with_llm(client):
    """Test advanced medical entity extraction using Llama 3.3-70B."""
    patient_data = PatientData(
        clinical_notes="""
        62-year-old female presents with newly diagnosed triple-negative breast cancer.
        Tumor size 4.2cm, grade 3, with 2/15 positive lymph nodes.
        BRCA1/2 negative. PD-L1 expression 15%.
        Patient has diabetes mellitus type 2 on metformin.
        Creatinine clearance 45 ml/min.
        Interested in immunotherapy trials.
        """
    )
    
    request_data = MatchRequest(patient_data=patient_data)
    response = client.post("/api/v1/match", json=request_data.model_dump())
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify LLM extracted entities correctly
    assert "extracted_entities" in data
    entities = data["extracted_entities"]
    
    assert "triple-negative breast cancer" in str(entities).lower()
    assert "diabetes" in str(entities).lower()
    assert "pd-l1" in str(entities).lower()
    assert "immunotherapy" in str(entities).lower()
