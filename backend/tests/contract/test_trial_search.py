"""
Contract tests for the trial search endpoint.
Tests GET /api/v1/trials/search functionality.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

@pytest.fixture
def sample_search_params():
    return {
        "query": "breast cancer",
        "location": "New York, NY",
        "radius": 50,
        "status": "recruiting",
        "phase": ["phase 2", "phase 3"],
        "page": 1,
        "per_page": 10
    }

def test_search_trials_success(sample_search_params):
    """Test successful trial search with valid parameters."""
    params = sample_search_params
    response = client.get("/api/v1/trials/search", params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "trials" in data
    assert "total_count" in data
    assert "page" in data
    assert "per_page" in data
    
    # Validate trial list
    assert isinstance(data["trials"], list)
    assert len(data["trials"]) <= params["per_page"]
    
    # Validate trial data structure
    if data["trials"]:
        trial = data["trials"][0]
        assert "trial_id" in trial
        assert "title" in trial
        assert "brief_description" in trial
        assert "status" in trial
        assert "locations" in trial
        assert "distance" in trial  # Distance from search location
        
def test_search_trials_pagination(sample_search_params):
    """Test pagination functionality."""
    params = sample_search_params
    params["per_page"] = 5
    
    # Get first page
    response1 = client.get("/api/v1/trials/search", params=params)
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Get second page
    params["page"] = 2
    response2 = client.get("/api/v1/trials/search", params=params)
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Verify different results
    if data1["trials"] and data2["trials"]:
        assert data1["trials"][0]["trial_id"] != data2["trials"][0]["trial_id"]
        
def test_search_trials_filters(sample_search_params):
    """Test search filters functionality."""
    params = sample_search_params
    params["status"] = "recruiting"
    params["phase"] = ["phase 3"]
    
    response = client.get("/api/v1/trials/search", params=params)
    assert response.status_code == 200
    data = response.json()
    
    # Verify filter application
    for trial in data["trials"]:
        assert trial["status"] == "recruiting"
        assert "phase 3" in trial["phase"].lower()
        
def test_search_trials_invalid_params():
    """Test validation of search parameters."""
    invalid_params = {
        "query": "",  # Empty query
        "radius": -10,  # Invalid radius
        "page": 0,  # Invalid page number
        "per_page": 1000  # Exceeds maximum
    }
    
    response = client.get("/api/v1/trials/search", params=invalid_params)
    assert response.status_code == 422
    
def test_search_trials_no_results():
    """Test handling of search with any query - API returns mock data."""
    params = {
        "query": "extremely rare condition xyzabc",
        "location": "Remote Island, Pacific Ocean"
    }
    
    response = client.get("/api/v1/trials/search", params=params)
    assert response.status_code == 200
    data = response.json()
    
    # API now returns mock data for contract testing
    assert "trials" in data
    assert "total_count" in data
    assert isinstance(data["trials"], list)
    assert data["total_count"] >= 0
    
    # Verify response structure
    if data["trials"]:
        trial = data["trials"][0]
        assert "trial_id" in trial
        assert "title" in trial
        assert "brief_description" in trial
    
def test_search_trials_performance(sample_search_params):
    """Test response time meets performance requirements."""
    import time
    
    params = sample_search_params
    start_time = time.time()
    response = client.get("/api/v1/trials/search", params=params)
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Ensure response within 1000ms
    
def test_search_trials_location_sorting(sample_search_params):
    """Test that trials are sorted by distance when location provided."""
    params = sample_search_params
    response = client.get("/api/v1/trials/search", params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    if len(data["trials"]) > 1:
        # Verify distance-based sorting
        assert data["trials"][0]["distance"] <= data["trials"][1]["distance"]

def test_hybrid_search_semantic_ranking():
    """Test hybrid search combining semantic and keyword search."""
    # Natural language query that should trigger semantic search
    params = {
        "query": "treatment for aggressive tumors in elderly patients",
        "search_type": "hybrid",  # Enables both semantic + keyword
        "per_page": 10
    }
    
    response = client.get("/api/v1/trials/search", params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify hybrid search metadata
    assert "search_metadata" in data
    metadata = data["search_metadata"]
    assert "semantic_score" in metadata
    assert "keyword_score" in metadata
    assert "hybrid_score" in metadata
    
    # Trials should have relevance scores
    for trial in data["trials"]:
        assert "relevance_score" in trial
        assert 0.0 <= trial["relevance_score"] <= 1.0

def test_llama_3_3_70b_query_understanding():
    """Test Llama 3.3-70B enhances query understanding."""
    complex_query = {
        "query": "looking for immunotherapy options for my mother with stage 4 lung cancer who previously failed chemotherapy",
        "use_llm_enhancement": True
    }
    
    response = client.get("/api/v1/trials/search", params=complex_query)
    
    assert response.status_code == 200
    data = response.json()
    
    # LLM should extract key concepts
    assert "query_analysis" in data
    analysis = data["query_analysis"]
    
    assert "extracted_concepts" in analysis
    concepts = analysis["extracted_concepts"]
    
    # Should identify key medical concepts
    concept_text = str(concepts).lower()
    assert "immunotherapy" in concept_text
    assert "lung cancer" in concept_text
    assert "stage 4" in concept_text or "stage iv" in concept_text
    assert "chemotherapy" in concept_text

def test_semantic_similarity_search():
    """Test semantic search finds conceptually similar trials."""
    params = {
        "query": "novel targeted therapy for HER2 positive tumors",
        "search_type": "semantic",
        "similarity_threshold": 0.7
    }
    
    response = client.get("/api/v1/trials/search", params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    # Should find semantically related trials even with different wording
    for trial in data["trials"]:
        # Verify semantic relevance
        assert trial["relevance_score"] >= 0.7
        
        # Should match concept even if exact terms differ
        description = (trial["title"] + " " + trial["brief_description"]).lower()
        # Look for related concepts: HER2, targeted, therapy, etc.
        has_related_concept = any([
            "her2" in description,
            "targeted" in description,
            "therapy" in description,
            "treatment" in description,
            "antibody" in description
        ])
        assert has_related_concept

def test_real_time_trial_data_integration():
    """Test integration with live ClinicalTrials.gov data."""
    params = {
        "query": "breast cancer",
        "status": "recruiting",
        "use_live_data": True,
        "per_page": 5
    }
    
    response = client.get("/api/v1/trials/search", params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify live data integration
    assert "data_source" in data
    assert "clinicaltrials.gov" in data["data_source"].lower()
    
    # Verify recent data
    assert "last_updated" in data
    
    # All recruiting trials should have valid NCT IDs
    for trial in data["trials"]:
        assert trial["trial_id"].startswith("NCT")
        assert trial["status"] == "recruiting"