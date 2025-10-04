# MedMatch AI Docker Deployment Guide
# Creative Docker MCP Gateway Showcase for Hackathon

## 🏥 Healthcare AI Platform Architecture

This repository demonstrates creative use of Docker MCP Gateway through a comprehensive healthcare AI platform that matches cancer patients with clinical trials using real-time data from ClinicalTrials.gov.

### 🎯 Docker MCP Gateway Creative Features

1. **Multi-Stage Healthcare-Optimized Builds**
   - Specialized layers for AI model preparation
   - HIPAA-compliant security configurations
   - Healthcare-specific dependency management

2. **Intelligent Service Orchestration**
   - AI model cache warming on startup
   - Health monitoring with medical-grade reliability
   - Auto-scaling based on patient load

3. **Healthcare Compliance Infrastructure**
   - PHI (Protected Health Information) isolation
   - Audit logging containers
   - Secure inter-service communication

## 🚀 Quick Start

### Prerequisites
- Docker Desktop or Docker Engine 20.10+
- Docker Compose v2.0+
- 8GB+ RAM (for AI model containers)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd medmatch-spec
cp docker/.env.example docker/.env
```

### 2. Configure Environment
Edit `docker/.env` with your credentials:
```bash
# Required: Supabase credentials
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Required: Cerebras API for Llama 3.3-70b
CEREBRAS_API_KEY=your_cerebras_api_key_here
```

### 3. Launch the Platform
```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### 4. Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

## 🏗️ Architecture Overview

### Service Mesh
```
┌─────────────────┐    ┌─────────────────┐
│   React Frontend │────│  FastAPI Backend │
│   (nginx + SPA)  │    │  (AI Pipeline)   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐    ┌──────▼──────┐    ┌───▼───┐
│ Redis │    │ PostgreSQL  │    │ Health│
│Cache  │    │  Database   │    │Monitor│
└───────┘    └─────────────┘    └───────┘
         │
    ┌────▼─────────────────────────────┐
    │  Prometheus + Grafana Monitoring │
    └──────────────────────────────────┘
```

### Container Features

#### Backend Container (`medmatch-backend`)
- **Multi-stage build** with AI model pre-loading
- **spaCy models** baked into container layers
- **Health checks** with medical-grade SLAs
- **Security hardening** for healthcare compliance
- **Auto-restart** policies for high availability

#### Frontend Container (`medmatch-frontend`)
- **React SPA** with nginx reverse proxy
- **Security headers** for healthcare applications
- **SSL-ready** configuration
- **Static asset optimization**

#### Database Containers
- **PostgreSQL** with healthcare schema
- **Redis** for AI model result caching
- **Data persistence** with proper backup strategies

#### Monitoring Stack
- **Prometheus** metrics collection
- **Grafana** dashboards for healthcare KPIs
- **Custom health monitor** service
- **Alert management** for critical systems

## 🎨 Docker MCP Gateway Creativity

### 1. Healthcare-Specific Optimizations
```dockerfile
# AI Model layer optimization
FROM python-deps AS spacy-models
RUN python -m spacy download en_core_web_sm
RUN python -c "import spacy; nlp = spacy.load('en_core_web_sm')"
```

### 2. Intelligent Dependency Management
```dockerfile
# Healthcare compliance layer
FROM runtime AS production
COPY --from=deps-installer /opt/venv /opt/venv
RUN groupadd -r medmatch && useradd -r -g medmatch medmatch
USER medmatch
```

### 3. Dynamic Service Discovery
```yaml
# Model cache warmer service
model-cache-warmer:
  build:
    context: ../
    dockerfile: docker/backend.Dockerfile
    target: development
  command: python -c "from backend.services.ai_service import warm_cache; warm_cache()"
```

### 4. Healthcare Monitoring
```python
# Custom health monitoring with medical-grade checks
async def check_ai_models():
    """Verify AI models are loaded and responding"""
    
async def check_clinical_trials_api():
    """Verify ClinicalTrials.gov API connectivity"""
    
async def check_patient_data_pipeline():
    """Verify patient data processing pipeline"""
```

## 🏥 Healthcare Compliance Features

### HIPAA Compliance
- **Data encryption** at rest and in transit
- **Audit logging** for all patient interactions
- **Access controls** with role-based permissions
- **Data retention** policies (7-year requirement)

### Security Hardening
- **Non-root containers** for all services
- **Security headers** for web applications
- **Network isolation** between services
- **Secrets management** via environment variables

### High Availability
- **Health checks** with automatic restarts
- **Load balancing** ready configuration
- **Database replication** support
- **Backup strategies** for critical data

## 🔄 Development Workflow

### Local Development
```bash
# Start in development mode
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up

# Hot reload enabled for both frontend and backend
# Volume mounts for live code changes
```

### Testing
```bash
# Run test suite in containers
docker-compose exec backend pytest tests/ -v

# Frontend tests
docker-compose exec frontend npm test
```

### Production Deployment
```bash
# Production build
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d

# Health check all services
docker-compose ps
```

## 📊 Monitoring and Observability

### Prometheus Metrics
- **Request latency** for API endpoints
- **AI model performance** metrics
- **Database connection** health
- **Memory and CPU** usage per service

### Grafana Dashboards
- **Clinical Trial Matching** performance
- **Patient Search** analytics
- **System Health** overview
- **Healthcare KPIs** tracking

### Custom Health Checks
- **Deep health monitoring** beyond basic HTTP checks
- **AI model readiness** verification
- **External API connectivity** (ClinicalTrials.gov)
- **Database query performance** monitoring

## 🚀 Scaling and Performance

### Horizontal Scaling
```yaml
# Auto-scaling configuration
deploy:
  replicas: 3
  update_config:
    parallelism: 1
    delay: 10s
  restart_policy:
    condition: on-failure
```

### Performance Optimization
- **Redis caching** for AI model results
- **Database indexing** for fast patient queries
- **CDN-ready** static asset serving
- **Connection pooling** for database connections

## 🏆 Hackathon Innovation

This project showcases Docker MCP Gateway through:

1. **Healthcare Innovation**: Real clinical trial matching with AI
2. **Technical Excellence**: Multi-stage builds, microservices, monitoring
3. **Compliance Focus**: HIPAA-ready infrastructure
4. **Scalability**: Production-ready container orchestration
5. **Developer Experience**: Easy setup, comprehensive documentation

The platform demonstrates how Docker containerization can make advanced healthcare AI accessible while maintaining enterprise-grade reliability and compliance standards.

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test in Docker containers
4. Submit a pull request

---

**Built for the Docker MCP Gateway Hackathon** 🏥🐳