import requests
import json

def get_test_token():
    """Get a test JWT token from Supabase for API testing."""
    # For now, we'll test without auth to focus on CORS
    # In production, this would get a real JWT token
    return None

# Test the CORS and API functionality
def test_cors_and_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing MedMatch API CORS and functionality...")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"   ✅ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   📊 Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    # Test 2: CORS preflight request
    print("\n2. Testing CORS preflight...")
    headers = {
        'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type,Authorization'
    }
    
    try:
        response = requests.options(f"{base_url}/api/v1/match", headers=headers)
        print(f"   ✅ CORS preflight: {response.status_code}")
        
        # Check CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        print("   📋 CORS Headers:")
        for header, value in cors_headers.items():
            print(f"      {header}: {value}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ CORS preflight failed: {e}")
        return False
    
    # Test 3: CORS POST request (no auth required)
    print("\n3. Testing CORS POST request...")
    
    test_data = {
        "test": "CORS functionality", 
        "origin": "http://localhost:5173"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:5173'
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/test-cors",
            headers=headers,
            json=test_data
        )
        print(f"   📡 CORS POST test: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success! CORS is working properly")
            print(f"   📋 Response: {result.get('message', 'N/A')}")
        else:
            print(f"   ❌ Error response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ CORS POST test failed: {e}")
        
    # Test 4: Sample match request (with auth - expected to fail)
    print("\n4. Testing authenticated match endpoint...")
    
    # Create test patient data matching the backend PatientData model
    test_patient_data = {
        "medical_history": "45-year-old patient with stage 3 lung cancer, previously treated with chemotherapy",
        "demographics": {
            "age": 45,
            "gender": "male"
        }
    }
    
    match_request = {
        "patient_data": test_patient_data,
        "max_results": 3,
        "min_confidence": 0.7,
        "enable_advanced_reasoning": True
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:5173'
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/match",
            headers=headers,
            json=match_request
        )
        print(f"   📡 Match request: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success! Found {len(result.get('matches', []))} matches")
        elif response.status_code == 403:
            print(f"   ℹ️  Expected: Authentication required (this is correct)")
        else:
            print(f"   ❌ Unexpected response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Match request failed: {e}")
        return False
    
    print("\n🎉 CORS and API testing completed!")
    return True

if __name__ == "__main__":
    test_cors_and_api()