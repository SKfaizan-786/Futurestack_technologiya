import asyncio
import httpx

async def test_clinicaltrials_api():
    """Test direct access to ClinicalTrials.gov API"""
    base_url = "https://clinicaltrials.gov/api/v2"
    
    # Test 1: Simple health check
    print("🧪 Testing ClinicalTrials.gov API...")
    
    async with httpx.AsyncClient() as client:
        # Test basic endpoint
        try:
            response = await client.get(f"{base_url}/studies?format=json&pageSize=1")
            print(f"✅ Basic API test: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Total studies: {data.get('totalCount', 'N/A')}")
                studies = data.get('studies', [])
                if studies:
                    print(f"🔬 First study: {studies[0].get('protocolSection', {}).get('identificationModule', {}).get('briefTitle', 'N/A')}")
            else:
                print(f"❌ API error: {response.text}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
        
        # Test 2: Search with condition (like our backend does)
        try:
            print("\n🔍 Testing condition search...")
            params = {
                "format": "json",
                "pageSize": 5,
                "query.cond": 'AREA[ConditionSearch] "lung cancer"'
            }
            
            response = await client.get(f"{base_url}/studies", params=params)
            print(f"📡 Condition search: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Lung cancer studies: {data.get('totalCount', 'N/A')}")
            else:
                print(f"❌ Search error: {response.text}")
                
        except Exception as e:
            print(f"❌ Search error: {e}")

if __name__ == "__main__":
    asyncio.run(test_clinicaltrials_api())