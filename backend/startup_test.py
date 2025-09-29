"""
Quick startup script to test the MedMatch AI application.
Run this in your medmatch virtual environment.
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.api.main import app
    print("✅ FastAPI application imported successfully!")
    
    # Test basic app creation
    print(f"✅ App title: {app.title}")
    print(f"✅ App version: {app.version}")
    print("✅ Core infrastructure setup complete!")
    
    print("\n🚀 To start the development server:")
    print("   conda activate medmatch")
    print("   cd C:\\Users\\faizan\\Desktop\\medmatch-spec\\backend")
    print("   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000")
    
    print("\n📖 API Documentation will be available at:")
    print("   http://localhost:8000/api/v1/docs")
    
    print("\n🏥 Health check endpoints:")
    print("   http://localhost:8000/api/v1/health/")
    print("   http://localhost:8000/api/v1/health/ready")
    print("   http://localhost:8000/api/v1/health/live")
    print("   http://localhost:8000/api/v1/health/metrics")
    
except ImportError as e:
    print(f"❌ Error importing application: {e}")
    print("\n💡 Make sure you're in the medmatch virtual environment:")
    print("   conda activate medmatch")
    print("   pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error creating application: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)