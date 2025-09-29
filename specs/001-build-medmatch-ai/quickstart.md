# MedMatch AI - Quickstart Guide

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git
- 4GB+ available memory
- Internet connection for API access

## Quick Setup (5 minutes)

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/medmatch-ai/medmatch-ai.git
cd medmatch-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:
```bash
# Cerebras API configuration
CEREBRAS_API_KEY=your_cerebras_api_key_here
CEREBRAS_BASE_URL=https://api.cerebras.ai/v1

# Database configuration (SQLite for dev)
DATABASE_URL=sqlite:///./medmatch.db

# Application settings
APP_ENV=development
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here

# Optional: ClinicalTrials.gov API rate limiting
TRIALS_API_RATE_LIMIT=1000
```

### 3. Quick Start with Docker

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
docker-compose logs -f backend

# Verify health
curl http://localhost:8000/api/v1/health
```

### 4. Alternative: Local Development

```bash
# Initialize database
python -m src.database.init_db

# Start the development server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing the API (2 minutes)

### Test 1: Basic Health Check

```bash
curl -X GET "http://localhost:8000/api/v1/health" \
  -H "accept: application/json"
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-29T10:30:00Z",
  "services": {
    "database": {"status": "healthy", "response_time_ms": 5},
    "llm_api": {"status": "healthy", "response_time_ms": 120},
    "trials_api": {"status": "healthy", "response_time_ms": 200}
  }
}
```

### Test 2: Simple Trial Matching

```bash
curl -X POST "http://localhost:8000/api/v1/match" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "patient_data": {
      "data_type": "structured",
      "medical_data": {
        "diagnosis": "C78.00",
        "stage": "Stage IIIA",
        "age": 52,
        "gender": "female",
        "location": "90210"
      }
    },
    "preferences": {
      "max_distance_miles": 50,
      "include_phase_1": false
    }
  }'
```

Expected response (truncated):
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "matches": [
    {
      "trial_id": "550e8400-e29b-41d4-a716-446655440000",
      "nct_id": "NCT04567890",
      "title": "A Study of Drug X in Stage III Lung Cancer",
      "confidence_score": 0.87,
      "recommendation": "likely_eligible",
      "explanation": "Patient meets primary inclusion criteria including stage IIIA diagnosis and age requirements..."
    }
  ],
  "processing_time_ms": 45
}
```

### Test 3: Natural Language Input

```bash
curl -X POST "http://localhost:8000/api/v1/match" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "patient_data": {
      "data_type": "unstructured",
      "text": "52-year-old female with stage IIIA lung adenocarcinoma, EGFR mutation positive, completed first-line carboplatin/pemetrexed with partial response. Located in Beverly Hills, CA."
    }
  }'
```

## Validation Tests (3 minutes)

### Run Contract Tests

```bash
# Run API contract tests
pytest tests/contract/test_api_contracts.py -v

# Run integration tests
pytest tests/integration/ -v

# Run all tests with coverage
pytest --cov=src tests/ --cov-report=html
```

### Performance Validation

```bash
# Test response time requirements
python scripts/performance_test.py --target-latency 100

# Load testing (optional)
python scripts/load_test.py --concurrent-users 10 --duration 60
```

### Expected Test Results

All tests should pass with these characteristics:
- ✅ API contract tests: 100% pass rate
- ✅ Integration tests: 100% pass rate  
- ✅ Average response time: <50ms (target), <100ms (requirement)
- ✅ Success rate: >99% for valid requests
- ✅ Memory usage: <512MB per request

## Demo Interface (Optional)

### Start Streamlit Demo

```bash
# Navigate to frontend directory
cd frontend

# Install frontend dependencies
pip install -r requirements.txt

# Start Streamlit app
streamlit run src/app.py --server.port 8501
```

Access demo at: http://localhost:8501

### Demo Workflow

1. **Patient Information**: Enter medical details in natural language or structured format
2. **Trial Matching**: Click "Find Matching Trials" 
3. **Results Review**: View top 3 matches with explanations
4. **Detail Exploration**: Click trial titles for full eligibility criteria
5. **Contact Information**: Access coordinator contact details

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'src'`
```bash
# Solution: Ensure you're in the project root and virtual environment is activated
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

**Issue**: `ConnectionError: Cerebras API unavailable`
```bash
# Solution: Check API key and network connectivity
curl -H "Authorization: Bearer $CEREBRAS_API_KEY" https://api.cerebras.ai/v1/models
```

**Issue**: `Database connection failed`
```bash
# Solution: Initialize database
python -c "from src.database.init_db import create_tables; create_tables()"
```

**Issue**: `Slow response times (>100ms)`
```bash
# Solution: Check Cerebras API performance and local resource usage
docker stats
htop
```

### Performance Optimization

```bash
# Enable Redis caching for trial data
docker run -d --name redis -p 6379:6379 redis:alpine

# Update .env
echo "REDIS_URL=redis://localhost:6379" >> .env

# Restart backend with caching enabled
docker-compose restart backend
```

### Debug Mode

```bash
# Start with debug logging
export LOG_LEVEL=DEBUG
uvicorn src.api.main:app --reload --log-level debug

# Check detailed logs
tail -f logs/medmatch-api.log
```

## Next Steps

### Development Workflow

1. **Feature Development**: Create feature branch from `main`
2. **Implementation**: Follow TDD with contract tests first
3. **Testing**: Run full test suite before committing
4. **Documentation**: Update API docs and this quickstart
5. **Deployment**: Use GitHub Actions for CI/CD

### Advanced Configuration

```bash
# Production deployment with Kubernetes
kubectl apply -f kubernetes/

# Monitoring setup
docker-compose -f docker-compose.monitoring.yml up -d

# Security hardening
./scripts/security_audit.sh
```

### API Documentation

- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json
- Health metrics: http://localhost:8000/metrics

## Success Criteria Validation

After completing this quickstart, verify these capabilities:

- [ ] **API Responsiveness**: <100ms average response time
- [ ] **Accuracy**: AI provides relevant trial matches with explanations
- [ ] **Reliability**: Health check shows all services healthy
- [ ] **Usability**: Demo interface works for both data input types
- [ ] **Compliance**: Audit logs show proper data handling
- [ ] **Scalability**: Docker services start and stop cleanly

**Estimated total setup time**: 10 minutes
**Estimated validation time**: 5 minutes
**Total quickstart time**: 15 minutes

For issues or questions, see: https://github.com/medmatch-ai/medmatch-ai/issues