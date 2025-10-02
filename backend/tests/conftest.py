"""
Test configuration and fixtures for MedMatch AI backend.
"""
import pytest
import asyncio
from typing import Generator
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["CEREBRAS_API_KEY"] = "test-key"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

# Import after setting environment variables
from src.api.main import app
from src.utils.auth import get_current_user, User


def override_get_current_user():
    """Override authentication for testing."""
    return User(
        id="test-user-123",
        email="test@example.com",
        role="patient",
        full_name="Test User"
    )


# Override the dependency for testing
app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture
def client():
    """Test client with authentication disabled."""
    return TestClient(app)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "fixtures" / "data"


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing."""
    return {
        "age": 45,
        "gender": "Female",
        "conditions": ["Type 2 Diabetes Mellitus"],
        "medications": ["Metformin", "Lisinopril"],
        "medical_history": ["Hypertension", "Obesity"],
        "lab_values": {
            "hba1c": 8.2,
            "blood_pressure": "140/90",
            "bmi": 32.1
        },
        "location": {
            "city": "Boston",
            "state": "Massachusetts",
            "zip_code": "02101"
        }
    }


@pytest.fixture
def sample_trial_data():
    """Sample clinical trial data for testing."""
    return {
        "nct_id": "NCT04567890",
        "brief_title": "Study of New Diabetes Treatment",
        "official_title": "A Phase 3 Randomized Study of Novel Glucose Control in Type 2 Diabetes",
        "status": "Recruiting",
        "phase": "Phase 3",
        "study_type": "Interventional",
        "conditions": ["Type 2 Diabetes Mellitus"],
        "eligibility_criteria": {
            "inclusion": [
                "Ages 18-75 years",
                "Diagnosis of Type 2 Diabetes",
                "HbA1c between 7.0-11.0%",
                "Stable medication regimen for 3 months"
            ],
            "exclusion": [
                "Type 1 Diabetes",
                "Pregnancy or breastfeeding",
                "Severe kidney disease",
                "Active cancer treatment"
            ],
            "age_min": 18,
            "age_max": 75,
            "sex": "All"
        },
        "locations": [
            {
                "facility": "Boston Medical Center",
                "city": "Boston",
                "state": "Massachusetts",
                "country": "United States",
                "latitude": 42.3601,
                "longitude": -71.0589
            }
        ]
    }


@pytest.fixture
def mock_cerebras_reasoning_response():
    """Mock Cerebras API reasoning response."""
    return {
        "choices": [
            {
                "message": {
                    "content": """Based on the patient profile and trial criteria analysis:

COMPATIBILITY ASSESSMENT: 85% Match

STEP-BY-STEP REASONING:
1. Age Compatibility: ✓ PASS
   - Patient age: 45 years
   - Trial requirement: 18-75 years
   - Status: Within acceptable range

2. Condition Match: ✓ PASS
   - Patient condition: Type 2 Diabetes Mellitus
   - Trial target: Type 2 Diabetes Mellitus
   - Status: Exact match

3. Exclusion Criteria Check: ✓ PASS
   - No Type 1 Diabetes: Confirmed Type 2
   - No pregnancy indicators: Patient gender/age appropriate
   - No severe kidney disease: Not mentioned in history
   - No active cancer: Not mentioned in history

4. Inclusion Criteria Analysis:
   - Age range: ✓ Met (45 within 18-75)
   - T2D diagnosis: ✓ Met
   - HbA1c level: ✓ Met (8.2% within 7.0-11.0% range)
   - Medication stability: ⚠️ NEEDS VERIFICATION

RECOMMENDATION: Strong candidate for this trial
NEXT STEPS: Verify medication regimen stability (3+ months)"""
                }
            }
        ],
        "usage": {
            "prompt_tokens": 245,
            "completion_tokens": 189,
            "total_tokens": 434
        }
    }