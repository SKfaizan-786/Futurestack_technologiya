"""
Contract tests for the notifications subscription endpoint.
Tests POST /api/v1/notifications/subscribe functionality.
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from src.api.main import app

client = TestClient(app)

class SubscriptionRequest(BaseModel):
    email: str
    trial_criteria: dict
    notification_preferences: dict

@pytest.fixture(autouse=True)
def clear_subscriptions_db():
    """Clear the subscriptions database before each test."""
    from src.api.endpoints.notifications import subscriptions_db
    subscriptions_db.clear()
    yield
    subscriptions_db.clear()

@pytest.fixture
def sample_subscription_data():
    return {
        "email": "patient@example.com",
        "trial_criteria": {
            "condition": "breast cancer",
            "location": "New York, NY",
            "radius": 50,
            "phase": ["phase 2", "phase 3"],
            "status": "not_yet_recruiting"
        },
        "notification_preferences": {
            "frequency": "daily",
            "notify_on": ["new_trials", "status_changes"],
            "max_distance": 100
        }
    }

def test_subscribe_notifications_success(sample_subscription_data):
    """Test successful subscription with valid data."""
    request_data = sample_subscription_data
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    
    assert response.status_code == 201
    data = response.json()
    
    # Validate subscription response
    assert "subscription_id" in data
    assert "email" in data
    assert data["email"] == request_data["email"]
    assert "created_at" in data
    assert "status" in data
    assert data["status"] == "active"
    
def test_subscribe_notifications_invalid_email(sample_subscription_data):
    """Test validation of email address."""
    request_data = sample_subscription_data.copy()
    request_data["email"] = "invalid-email"
    
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    assert response.status_code == 422
    
def test_subscribe_notifications_duplicate_subscription(sample_subscription_data):
    """Test handling of duplicate subscription attempts."""
    request_data = sample_subscription_data
    
    # First subscription
    response1 = client.post("/api/v1/notifications/subscribe", json=request_data)
    assert response1.status_code == 201
    
    # Duplicate subscription
    response2 = client.post("/api/v1/notifications/subscribe", json=request_data)
    assert response2.status_code == 409
    data = response2.json()
    assert "detail" in data
    assert "already subscribed" in data["detail"].lower()
    
def test_subscribe_notifications_invalid_criteria(sample_subscription_data):
    """Test validation of trial criteria."""
    request_data = sample_subscription_data.copy()
    request_data["trial_criteria"]["radius"] = -10  # Invalid radius
    
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    assert response.status_code == 422
    
def test_subscribe_notifications_invalid_preferences(sample_subscription_data):
    """Test validation of notification preferences."""
    request_data = sample_subscription_data.copy()
    request_data["notification_preferences"]["frequency"] = "invalid"
    
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    assert response.status_code == 422
    
def test_subscribe_notifications_performance(sample_subscription_data):
    """Test response time meets performance requirements."""
    import time
    
    request_data = sample_subscription_data
    start_time = time.time()
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    end_time = time.time()
    
    assert response.status_code == 201
    assert (end_time - start_time) < 1.0  # Ensure response within 1000ms
    
def test_subscribe_notifications_missing_fields():
    """Test handling of missing required fields."""
    incomplete_data = {
        "email": "patient@example.com"
        # Missing trial_criteria and notification_preferences
    }
    
    response = client.post("/api/v1/notifications/subscribe", json=incomplete_data)
    assert response.status_code == 422
    
def test_subscribe_notifications_max_criteria(sample_subscription_data):
    """Test handling of maximum allowed trial criteria."""
    request_data = sample_subscription_data.copy()
    # Add excessive criteria to test limits
    request_data["trial_criteria"]["conditions"] = ["condition" + str(i) for i in range(50)]
    
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    assert response.status_code == 422

def test_ai_powered_subscription_enhancement(sample_subscription_data):
    """Test AI enhancement of subscription criteria using Llama 3.3-70B."""
    request_data = sample_subscription_data.copy()
    request_data["enable_ai_enhancement"] = True
    request_data["natural_language_criteria"] = """
    Looking for breakthrough treatments for triple-negative breast cancer 
    that my oncologist might not know about yet. Prefer trials near major 
    cancer centers with promising early results.
    """
    
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    
    assert response.status_code == 201
    data = response.json()
    
    # AI should enhance the criteria
    assert "ai_enhanced_criteria" in data
    enhanced = data["ai_enhanced_criteria"]
    
    assert "extracted_concepts" in enhanced
    concepts = enhanced["extracted_concepts"]
    
    # Should identify key concepts
    concept_text = str(concepts).lower()
    assert "triple-negative" in concept_text
    assert "breast cancer" in concept_text
    assert "breakthrough" in concept_text or "novel" in concept_text

def test_intelligent_notification_timing(sample_subscription_data):
    """Test AI-powered notification timing optimization."""
    request_data = sample_subscription_data.copy()
    request_data["notification_preferences"]["intelligent_timing"] = True
    request_data["notification_preferences"]["urgency_analysis"] = True
    
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    
    assert response.status_code == 201
    data = response.json()
    
    # Should include AI timing analysis
    assert "notification_strategy" in data
    strategy = data["notification_strategy"]
    
    assert "urgency_factors" in strategy
    assert "optimal_timing" in strategy
    assert "personalization_score" in strategy

def test_subscription_with_patient_context(sample_subscription_data):
    """Test subscription enhanced with patient medical context."""
    request_data = sample_subscription_data.copy()
    request_data["patient_context"] = {
        "medical_history": "Stage II breast cancer, ER+/PR+, HER2-",
        "previous_treatments": ["surgery", "chemotherapy", "radiation"],
        "current_status": "completed treatment, in follow-up",
        "risk_factors": ["family history", "BRCA negative"]
    }
    
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    
    assert response.status_code == 201
    data = response.json()
    
    # Should provide personalized matching
    assert "personalization_insights" in data
    insights = data["personalization_insights"]
    
    assert "relevant_trial_types" in insights
    assert "exclusion_predictions" in insights
    assert "priority_biomarkers" in insights

def test_semantic_trial_matching_subscription(sample_subscription_data):
    """Test subscription with semantic trial matching capabilities."""
    request_data = sample_subscription_data.copy()
    request_data["matching_preferences"] = {
        "use_semantic_matching": True,
        "similarity_threshold": 0.8,
        "include_emerging_therapies": True,
        "consider_combination_trials": True
    }
    
    response = client.post("/api/v1/notifications/subscribe", json=request_data)
    
    assert response.status_code == 201
    data = response.json()
    
    # Should configure semantic matching
    assert "matching_configuration" in data
    config = data["matching_configuration"]
    
    assert "semantic_enabled" in config
    assert config["semantic_enabled"] is True
    assert "embedding_model" in config
    assert "similarity_threshold" in config
    assert config["similarity_threshold"] == 0.8
