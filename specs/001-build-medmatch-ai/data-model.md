# Data Model: MedMatch AI

## Core Entities

### Patient
**Purpose**: Represents an individual seeking clinical trial opportunities

**Fields**:
- `id`: UUID - Unique patient identifier
- `medical_data`: JSON - Structured medical information
  - `diagnosis`: String - Primary cancer diagnosis (ICD-10 code)
  - `stage`: String - Cancer stage (I-IV, TNM notation)
  - `biomarkers`: Array[Object] - Molecular markers and test results
    - `name`: String - Biomarker name (e.g., "EGFR", "BRCA1")
    - `value`: String - Test result value
    - `test_date`: DateTime - When test was performed
  - `treatment_history`: Array[Object] - Previous treatments
    - `treatment_type`: String - Treatment category
    - `drug_name`: String - Specific medication/therapy
    - `start_date`: DateTime
    - `end_date`: DateTime (nullable)
    - `response`: String - Treatment response/outcome
  - `demographics`: Object - Basic demographic information
    - `age`: Integer
    - `gender`: String
    - `location`: String - ZIP code or general location
- `created_at`: DateTime - Record creation timestamp
- `updated_at`: DateTime - Last modification timestamp
- `consent_status`: String - HIPAA consent status (active, withdrawn, expired)

**Validation Rules**:
- Age must be 18+ (adult clinical trials)
- Diagnosis must be valid ICD-10 cancer code
- Location required for proximity-based trial matching
- Medical data must include at minimum: diagnosis, stage, age

**Relationships**:
- One-to-many with MatchResult (patient can have multiple trial matches)
- Many-to-many with Trial through MatchResult (many patients can match many trials)

### Trial
**Purpose**: Represents an active clinical research study

**Fields**:
- `id`: UUID - Unique trial identifier
- `nct_id`: String - ClinicalTrials.gov NCT number
- `title`: String - Official trial title
- `brief_summary`: Text - Study description
- `eligibility_criteria`: JSON - Structured eligibility requirements
  - `inclusion_criteria`: Array[String] - Must-have requirements
  - `exclusion_criteria`: Array[String] - Disqualifying conditions
  - `age_range`: Object - Age requirements
    - `min_age`: Integer
    - `max_age`: Integer (nullable)
  - `gender`: String - Gender requirements (all, male, female)
  - `required_biomarkers`: Array[Object] - Molecular requirements
    - `biomarker`: String - Required biomarker name
    - `operator`: String - Comparison operator (equals, greater_than, etc.)
    - `value`: String - Required value/threshold
- `phase`: String - Trial phase (Phase I, Phase II, Phase III, Phase IV)
- `study_type`: String - Type of study (interventional, observational)
- `condition`: String - Primary condition being studied
- `intervention`: Array[String] - Treatments being tested
- `locations`: Array[Object] - Trial sites
  - `facility`: String - Hospital/clinic name
  - `city`: String
  - `state`: String
  - `zip_code`: String
  - `status`: String - Site recruitment status
- `overall_status`: String - Trial status (recruiting, active, completed, etc.)
- `enrollment_count`: Integer - Target enrollment number
- `sponsor`: String - Study sponsor organization
- `embeddings`: Vector(768) - Semantic embeddings for similarity search
- `last_updated`: DateTime - When trial data was last refreshed
- `created_at`: DateTime - Record creation timestamp

**Validation Rules**:
- NCT ID must be unique and follow NCT format
- Phase must be valid clinical trial phase
- At least one location must be specified for recruiting trials
- Eligibility criteria must contain both inclusion and exclusion criteria

**Relationships**:
- One-to-many with MatchResult (trial can match multiple patients)
- Many-to-many with Patient through MatchResult

### EligibilityCriteria
**Purpose**: Represents processed and structured eligibility requirements

**Fields**:
- `id`: UUID - Unique criteria identifier
- `trial_id`: UUID - Foreign key to Trial
- `criteria_type`: String - Type (inclusion, exclusion)
- `raw_text`: Text - Original criteria text from trial protocol
- `structured_criteria`: JSON - NLP-processed structured representation
  - `medical_concepts`: Array[Object] - Extracted medical concepts
    - `concept`: String - Medical concept (standardized)
    - `code`: String - ICD-10/SNOMED code
    - `operator`: String - Logical operator (requires, excludes, etc.)
  - `numeric_thresholds`: Array[Object] - Quantitative requirements
    - `parameter`: String - Measured parameter
    - `operator`: String - Comparison operator
    - `value`: Float - Threshold value
    - `unit`: String - Unit of measurement
- `confidence_score`: Float - NLP extraction confidence (0.0-1.0)
- `processed_at`: DateTime - When criteria were processed

**Validation Rules**:
- Confidence score must be between 0.0 and 1.0
- Trial ID must reference existing trial
- At least one medical concept must be extracted

**Relationships**:
- Many-to-one with Trial (trial has multiple criteria)
- One-to-many with MatchResult (criteria used in multiple matches)

### MatchResult
**Purpose**: Represents the outcome of patient-trial eligibility analysis

**Fields**:
- `id`: UUID - Unique match identifier
- `patient_id`: UUID - Foreign key to Patient
- `trial_id`: UUID - Foreign key to Trial
- `overall_confidence`: Float - Overall match confidence (0.0-1.0)
- `match_score`: Float - Numerical match score for ranking
- `reasoning_chain`: JSON - AI reasoning breakdown
  - `inclusion_matches`: Array[Object] - Inclusion criteria analysis
    - `criteria_text`: String - Original criteria text
    - `patient_data_match`: String - Relevant patient data
    - `match_status`: String - met, not_met, uncertain
    - `confidence`: Float - Individual criteria confidence
    - `reasoning`: String - AI explanation for this match
  - `exclusion_matches`: Array[Object] - Exclusion criteria analysis
    - `criteria_text`: String
    - `patient_data_match`: String
    - `match_status`: String
    - `confidence`: Float
    - `reasoning`: String
  - `biomarker_matches`: Array[Object] - Biomarker requirement analysis
  - `demographic_matches`: Object - Age, gender, location analysis
- `explanation`: Text - Human-readable explanation of match
- `recommendation`: String - Final recommendation (eligible, likely_eligible, unlikely_eligible, ineligible)
- `proximity_score`: Float - Geographic proximity factor (0.0-1.0)
- `created_at`: DateTime - When match was computed
- `llm_model_version`: String - LLM model used for analysis

**Validation Rules**:
- Confidence and scores must be between 0.0 and 1.0
- Patient ID and Trial ID must reference existing records
- Recommendation must be valid enum value
- Reasoning chain must contain analysis for all criteria types

**Relationships**:
- Many-to-one with Patient (patient can have multiple matches)
- Many-to-one with Trial (trial can match multiple patients)
- Creates many-to-many relationship between Patient and Trial

## Database Schema Considerations

### Indexing Strategy
```sql
-- Performance indexes for common queries
CREATE INDEX idx_patients_diagnosis ON patients(medical_data->>'diagnosis');
CREATE INDEX idx_patients_created_at ON patients(created_at);
CREATE INDEX idx_trials_condition ON trials(condition);
CREATE INDEX idx_trials_status ON trials(overall_status);
CREATE INDEX idx_trials_nct_id ON trials(nct_id);
CREATE INDEX idx_match_results_confidence ON match_results(overall_confidence DESC);
CREATE INDEX idx_match_results_patient_trial ON match_results(patient_id, trial_id);

-- Full-text search indexes
CREATE INDEX idx_trials_title_search ON trials USING gin(to_tsvector('english', title));
CREATE INDEX idx_trials_summary_search ON trials USING gin(to_tsvector('english', brief_summary));
```

### Data Partitioning
- Match results partitioned by creation date (monthly partitions)
- Trial data partitioned by study phase for optimized queries
- Patient data encrypted at column level for HIPAA compliance

### Migration Strategy
```python
# SQLAlchemy model definitions ensure smooth SQLite → PostgreSQL migration
class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medical_data = Column(JSON)  # SQLite: TEXT, PostgreSQL: JSONB
    created_at = Column(DateTime, default=datetime.utcnow)
    consent_status = Column(String(20), default='active')
    
    # Relationships
    match_results = relationship("MatchResult", back_populates="patient")
```

## Data Flow Architecture

### Input Processing
1. **Raw Patient Data** → Medical NLP Processing → **Structured Patient Record**
2. **ClinicalTrials.gov API** → Eligibility Parsing → **Structured Trial Record**
3. **Patient + Trials** → LLM Analysis → **Match Results with Explanations**

### Data Consistency
- Write-through caching for trial data (cache updates on database write)
- Event-driven updates when new trials are added or existing trials modified
- Eventual consistency acceptable for non-critical match history data

### HIPAA Compliance Features
- Patient medical data encrypted using separate encryption keys
- Audit trail table logging all patient data access
- Automatic data anonymization for analytics and model training
- Configurable data retention with automatic purging

**Next Phase**: Generate API contracts and integration tests based on data model