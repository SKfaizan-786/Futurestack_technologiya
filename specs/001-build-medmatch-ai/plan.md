
# Implementation Plan: MedMatch AI - Clinical Trial Matching Platform

**Branch**: `001-build-medmatch-ai` | **Date**: September 29, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-build-medmatch-ai/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
AI-powered clinical trial matching platform that connects cancer patients to eligible trials using Llama 3.2 models via Cerebras API. System processes patient medical data (structured JSON or natural language) and returns top 3 relevant trials with explanations and confidence scores within 100ms. Technical approach leverages FastAPI backend, hybrid search architecture, and containerized deployment with Kubernetes orchestration.

## Technical Context
**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Pydantic v2, spaCy, transformers, SQLAlchemy  
**Storage**: SQLite (development) → PostgreSQL (production)  
**Testing**: pytest, FastAPI TestClient, contract testing  
**Target Platform**: Linux containers (Docker), Kubernetes orchestration  
**Project Type**: web (FastAPI backend + optional Streamlit frontend)  
**Performance Goals**: <50ms inference latency, 100+ concurrent requests, 99.9% uptime  
**Constraints**: HIPAA compliance, real-time processing, 90%+ accuracy requirements  
**Scale/Scope**: 20+ cancer types, national trial database integration, explainable AI outputs

**LLM Integration**: Cerebras Inference API with Llama 3.2 models (1B/3B/11B/90B variants)  
**Data Sources**: ClinicalTrials.gov API v2.0, medical ontologies (ICD-10, SNOMED)  
**AI Pipeline**: Medical NLP → Hybrid search → LLM reasoning → Scoring → Explanation generation

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Patient Privacy & HIPAA Compliance**: ✅ PASS
- Plan includes explicit encryption at rest/transit requirements
- Data minimization principles incorporated in design
- Audit trail requirements specified
- De-identification for AI processing planned

**II. Open-Source Development & Reproducibility**: ✅ PASS  
- All components designed as open-source (FastAPI, spaCy, PostgreSQL)
- Docker containerization ensures reproducible deployments
- Version control and dependency management specified
- Transparent AI decision-making with explainable outputs

**III. Real-Time Performance Requirements**: ✅ PASS
- Sub-50ms inference latency target specified (<100ms requirement)
- Performance monitoring and auto-scaling planned
- Cerebras API provides 20x speed advantage for Llama models

**IV. Modular Architecture & LLM Provider Flexibility**: ✅ PASS
- Modular AI pipeline design (NLP → Search → LLM → Scoring)
- LLM provider abstraction planned (Cerebras as primary, extensible)
- Independent component deployment via Kubernetes
- Standardized interfaces between components

**V. Transparent AI Decision-Making**: ✅ PASS
- Explainable AI outputs with reasoning chains required
- Confidence scores for all recommendations specified
- Chain-of-thought reasoning implemented via Llama 3.2
- Auditable decision logic design

**VI. Scalable Deployment Architecture**: ✅ PASS
- Infrastructure-as-code with Kubernetes manifests
- Auto-scaling and load balancing planned
- Local development (Docker Compose) to production (Kubernetes) parity
- CI/CD pipeline with GitHub Actions specified

**Initial Gate Result**: ✅ ALL CHECKS PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/          # Data models (Patient, Trial, MatchResult)
│   ├── services/        # Business logic (matching, NLP processing)
│   ├── api/             # FastAPI endpoints and routers
│   ├── integrations/    # External API clients (ClinicalTrials.gov, Cerebras)
│   ├── ai/              # LLM pipeline and reasoning components
│   └── utils/           # Shared utilities and configuration
├── tests/
│   ├── contract/        # API contract tests
│   ├── integration/     # End-to-end scenarios
│   └── unit/            # Component unit tests
├── migrations/          # Database schema migrations
└── config/              # Configuration files and schemas

frontend/                # Optional Streamlit demo UI
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Application pages/screens
│   └── services/        # API client and data services
└── tests/

kubernetes/              # Deployment manifests
├── base/               # Base Kubernetes resources
├── overlays/           # Environment-specific configurations
└── secrets/            # Secret templates (not committed)

docker/                 # Container definitions
├── backend.Dockerfile
├── frontend.Dockerfile
└── docker-compose.yml

docs/                   # Documentation
├── api/                # API documentation
├── deployment/         # Deployment guides  
└── development/        # Development setup
```

**Structure Decision**: Web application structure selected due to FastAPI backend + optional Streamlit frontend. Backend-focused design with containerized deployment. Kubernetes-native architecture for production scalability.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base structure
- Generate implementation tasks from Phase 1 design artifacts
- Create TDD workflow: contract tests → data models → API implementation → integration tests

**Contract-Based Task Generation**:
- Each API endpoint in contracts/api-spec.yaml → contract test task [P]
- Each contract test → corresponding API implementation task
- Each data entity in data-model.md → model creation task [P]
- Each user story from feature spec → integration test task

**Specific Task Categories Expected**:
1. **Database Setup Tasks** (5-6 tasks)
   - Database initialization and migration system
   - Core entity models (Patient, Trial, MatchResult, EligibilityCriteria)
   - Database indexes and performance optimizations

2. **External Integration Tasks** (4-5 tasks)
   - Cerebras API client with Llama 3.2 integration
   - ClinicalTrials.gov API client with rate limiting
   - Medical NLP pipeline with spaCy configuration
   - Caching layer implementation (Redis/in-memory)

3. **Core AI Pipeline Tasks** (6-8 tasks)
   - Medical data normalization and NER processing
   - Hybrid search implementation (semantic + lexical)
   - LLM-based eligibility reasoning with chain-of-thought
   - Match scoring and ranking algorithm
   - Explanation generation system

4. **API Implementation Tasks** (8-10 tasks)
   - FastAPI application structure and middleware
   - Trial matching endpoint (/api/v1/match)
   - Trial details endpoint (/api/v1/trials/{id})
   - Trial search endpoint (/api/v1/trials/search)
   - Notification subscription endpoint
   - Health check and monitoring endpoints

5. **Security & Compliance Tasks** (4-5 tasks)
   - HIPAA-compliant data encryption
   - Audit logging implementation
   - API authentication and authorization
   - Input validation and sanitization

6. **Testing & Quality Tasks** (6-7 tasks)
   - Contract test implementation (already failing tests ready)
   - Integration test scenarios from user stories
   - Performance testing and optimization
   - Security testing and vulnerability assessment

7. **Deployment & Infrastructure Tasks** (5-6 tasks)
   - Docker containerization with multi-stage builds
   - Docker Compose development environment
   - Kubernetes deployment manifests
   - Monitoring and logging configuration
   - CI/CD pipeline setup

**Ordering Strategy**:
- **Phase 2a**: Foundation (database, models, basic API structure) 
- **Phase 2b**: External integrations (APIs, NLP pipeline)
- **Phase 2c**: Core AI functionality (matching, reasoning, scoring)
- **Phase 2d**: API endpoints implementation
- **Phase 2e**: Security, testing, deployment

**Parallel Execution Opportunities** [P]:
- Database models can be implemented in parallel
- External API clients can be developed independently  
- Contract tests are already written and can run in parallel
- Docker configurations can be prepared alongside code development

**Estimated Task Breakdown**:
- **Total tasks**: 38-42 numbered, ordered tasks
- **Parallel tasks**: ~15 tasks marked [P] for independent execution
- **Critical path**: Database → Core models → API framework → AI pipeline → Endpoints
- **Estimated effort**: 2-3 weeks for MVP implementation

**Quality Gates**:
- All contract tests must pass before endpoint implementation
- Performance benchmarks (<100ms) must be met before deployment
- Security audit must pass before production deployment
- Integration tests must validate complete user workflows

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS  
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

**Generated Artifacts**:
- [x] research.md - Technical research and decisions
- [x] data-model.md - Entity designs and database schema
- [x] contracts/api-spec.yaml - OpenAPI specification
- [x] contracts/test_api_contracts.py - Contract test suite
- [x] quickstart.md - Setup and validation guide
- [x] .github/copilot-instructions.md - Agent context updated

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
