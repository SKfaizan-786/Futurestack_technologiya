"""
Quick startup script to test the MedMatch AI application.
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
    
    print("\n🚀 To start the development server, run:")
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
    print("Make sure all dependencies are installed:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error creating application: {e}")
    sys.exit(1)