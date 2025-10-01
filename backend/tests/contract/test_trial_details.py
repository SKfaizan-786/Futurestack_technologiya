"""
Contract tests for the trial details endpoint.
Tests GET /api/v1/trials/{id} functionality.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.models.trial import Trial

client = TestClient(app)

@pytest.fixture
def sample_trial_id():
    return "NCT04444444"  # Use existing mock trial ID for breast cancer study

def test_get_trial_details_success(sample_trial_id):
    """Test successful retrieval of trial details."""
    trial_id = sample_trial_id
    response = client.get(f"/api/v1/trials/{trial_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate trial data structure
    assert "trial_id" in data
    assert "title" in data
    assert "description" in data
    assert "eligibility_criteria" in data
    assert "status" in data
    assert "locations" in data
    assert "contact_info" in data
    assert "last_updated" in data
    
    # Validate specific trial data
    assert data["trial_id"] == trial_id
    assert isinstance(data["eligibility_criteria"], dict)
    assert isinstance(data["locations"], list)
    
def test_get_trial_details_invalid_id():
    """Test error handling for invalid trial ID."""
    response = client.get("/api/v1/trials/invalid_id")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    
def test_get_trial_details_not_found():
    """Test handling of non-existent trial ID."""
    response = client.get("/api/v1/trials/NCT00000000")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    
def test_get_trial_details_with_medical_terms(sample_trial_id):
    """Test that medical terms in eligibility criteria are properly processed."""
    trial_id = sample_trial_id
    response = client.get(f"/api/v1/trials/{trial_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that eligibility criteria contains processed medical terms
    assert "processed_criteria" in data
    assert "inclusion_criteria" in data["processed_criteria"]
    assert "exclusion_criteria" in data["processed_criteria"]
    
    # Verify medical term annotations
    for criterion in data["processed_criteria"]["inclusion_criteria"]:
        assert "medical_terms" in criterion
        assert isinstance(criterion["medical_terms"], list)
        
def test_get_trial_details_performance(sample_trial_id):
    """Test response time meets performance requirements."""
    import time
    
    trial_id = sample_trial_id
    start_time = time.time()
    response = client.get(f"/api/v1/trials/{trial_id}")
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Ensure response within 1000ms

def test_llama_3_3_70b_trial_summarization(sample_trial_id):
    """Test Llama 3.3-70B generates intelligent trial summaries."""
    trial_id = sample_trial_id
    response = client.get(f"/api/v1/trials/{trial_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # AI-generated summaries using Llama 3.3-70B
    assert "ai_generated_summary" in data
    assert "patient_friendly_description" in data
    assert "key_insights" in data
    
    # Verify summary quality
    summary = data["ai_generated_summary"]
    assert len(summary) > 50
    assert "trial" in summary.lower()
    
    # Patient-friendly description should be accessible
    friendly_desc = data["patient_friendly_description"]
    assert len(friendly_desc) > 30
    # Should avoid complex medical jargon
    assert "efficacy" not in friendly_desc.lower() or "effective" in friendly_desc.lower()

def test_cerebras_powered_eligibility_analysis(sample_trial_id):
    """Test Cerebras API powers advanced eligibility analysis."""
    trial_id = sample_trial_id
    response = client.get(f"/api/v1/trials/{trial_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Cerebras-powered analysis
    assert "eligibility_analysis" in data
    analysis = data["eligibility_analysis"]
    
    assert "complexity_score" in analysis
    assert "common_patient_types" in analysis
    assert "potential_barriers" in analysis
    assert "biomarker_requirements" in analysis
    
    # Verify analysis depth (Llama 3.3-70B should provide detailed insights)
    assert isinstance(analysis["common_patient_types"], list)
    assert len(analysis["common_patient_types"]) > 0
    
    # Complexity score should be reasonable
    assert 0 <= analysis["complexity_score"] <= 10

def test_medical_ontology_integration(sample_trial_id):
    """Test integration with medical ontologies for award-winning accuracy."""
    trial_id = sample_trial_id
    response = client.get(f"/api/v1/trials/{trial_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Medical term standardization
    assert "standardized_terms" in data
    terms = data["standardized_terms"]
    
    assert "icd10_codes" in terms
    assert "snomed_concepts" in terms
    assert "drug_mappings" in terms
    
    # Verify proper medical coding
    if terms["icd10_codes"]:
        for code in terms["icd10_codes"]:
            assert "code" in code
            assert "description" in code
            # ICD-10 codes should match pattern
            assert len(code["code"]) >= 3
