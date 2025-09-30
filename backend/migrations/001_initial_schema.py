"""
Initial schema migration for MedMatch AI database.

Creates tables for Patient, Trial, EligibilityCriteria, and MatchResult models
with proper indexes and constraints for optimal performance.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite, postgresql, mysql


# revision identifiers, used by Alembic
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial database schema."""
    
    # Create patients table
    op.create_table(
        'patients',
        sa.Column('patient_id', sa.String(100), primary_key=True),
        sa.Column('age', sa.Integer, nullable=False),
        sa.Column('gender', sa.String(50), nullable=False),
        sa.Column('medical_conditions', sa.JSON, nullable=False, default=[]),
        sa.Column('medications', sa.JSON, nullable=False, default=[]),
        sa.Column('allergies', sa.JSON, nullable=False, default=[]),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('audit_log_id', sa.String(100), nullable=True),
        sa.Column('data_hash', sa.String(64), nullable=True),
        
        # Indexes for performance
        sa.Index('idx_patients_age', 'age'),
        sa.Index('idx_patients_gender', 'gender'),
        sa.Index('idx_patients_created_at', 'created_at'),
    )
    
    # Create trials table
    op.create_table(
        'trials',
        sa.Column('nct_id', sa.String(20), primary_key=True),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('brief_summary', sa.Text, nullable=False),
        sa.Column('detailed_description', sa.Text, nullable=True),
        sa.Column('primary_purpose', sa.String(100), nullable=False),
        sa.Column('phase', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('enrollment', sa.Integer, nullable=True),
        sa.Column('estimated_enrollment', sa.Integer, nullable=True),
        sa.Column('study_type', sa.String(50), nullable=False),
        sa.Column('sponsor', sa.String(500), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        
        # JSON fields for complex data
        sa.Column('conditions', sa.JSON, nullable=False, default=[]),
        sa.Column('interventions', sa.JSON, nullable=False, default=[]),
        sa.Column('eligibility_criteria', sa.JSON, nullable=True),
        sa.Column('locations', sa.JSON, nullable=True),
        sa.Column('primary_outcomes', sa.JSON, nullable=True),
        
        # Vector embedding for semantic search
        sa.Column('embedding', sa.JSON, nullable=True),
        sa.Column('embedding_model', sa.String(100), nullable=True),
        
        # Timeline fields
        sa.Column('start_date', sa.String(20), nullable=True),
        sa.Column('completion_date', sa.String(20), nullable=True),
        sa.Column('primary_completion_date', sa.String(20), nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('last_fetched', sa.DateTime, nullable=True),
        
        # Indexes for performance
        sa.Index('idx_trials_status', 'status'),
        sa.Index('idx_trials_phase', 'phase'),
        sa.Index('idx_trials_primary_purpose', 'primary_purpose'),
        sa.Index('idx_trials_study_type', 'study_type'),
        sa.Index('idx_trials_created_at', 'created_at'),
        sa.Index('idx_trials_last_fetched', 'last_fetched'),
    )
    
    # Create eligibility_criteria table
    op.create_table(
        'eligibility_criteria',
        sa.Column('criteria_id', sa.String(100), primary_key=True),
        sa.Column('trial_nct_id', sa.String(20), nullable=False),
        sa.Column('raw_text', sa.Text, nullable=False),
        
        # Structured criteria
        sa.Column('inclusion_criteria', sa.JSON, nullable=False, default=[]),
        sa.Column('exclusion_criteria', sa.JSON, nullable=False, default=[]),
        sa.Column('age_requirements', sa.JSON, nullable=True),
        sa.Column('gender_requirements', sa.String(50), nullable=True),
        
        # NLP processing results
        sa.Column('extracted_entities', sa.JSON, nullable=True),
        sa.Column('structured_requirements', sa.JSON, nullable=True),
        sa.Column('complexity_score', sa.Float, nullable=True),
        
        # Metadata
        sa.Column('version', sa.String(20), nullable=False, default='1.0'),
        sa.Column('processing_metadata', sa.JSON, nullable=True),
        sa.Column('locale', sa.String(10), nullable=False, default='en-US'),
        sa.Column('terminology_system', sa.String(50), nullable=False, default='SNOMED-CT'),
        
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now()),
        
        # Foreign key relationship
        sa.ForeignKeyConstraint(['trial_nct_id'], ['trials.nct_id'], ondelete='CASCADE'),
        
        # Indexes for performance
        sa.Index('idx_eligibility_trial_nct_id', 'trial_nct_id'),
        sa.Index('idx_eligibility_complexity_score', 'complexity_score'),
        sa.Index('idx_eligibility_created_at', 'created_at'),
    )
    
    # Create match_results table
    op.create_table(
        'match_results',
        sa.Column('match_id', sa.String(100), primary_key=True),
        sa.Column('patient_id', sa.String(100), nullable=False),
        sa.Column('trial_nct_id', sa.String(20), nullable=False),
        
        # Scores
        sa.Column('overall_score', sa.Float, nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('match_status', sa.String(50), nullable=False),
        
        # Reasoning and explanation
        sa.Column('reasoning_chain', sa.JSON, nullable=False, default=[]),
        sa.Column('explanation', sa.Text, nullable=True),
        sa.Column('next_steps', sa.JSON, nullable=True),
        
        # Confidence factors
        sa.Column('confidence_factors', sa.JSON, nullable=True),
        
        # Audit and metadata
        sa.Column('audit_metadata', sa.JSON, nullable=True),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('ai_model_version', sa.String(100), nullable=True),
        
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now()),
        
        # Foreign key relationships
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trial_nct_id'], ['trials.nct_id'], ondelete='CASCADE'),
        
        # Indexes for performance
        sa.Index('idx_match_results_patient_id', 'patient_id'),
        sa.Index('idx_match_results_trial_nct_id', 'trial_nct_id'),
        sa.Index('idx_match_results_match_status', 'match_status'),
        sa.Index('idx_match_results_overall_score', 'overall_score'),
        sa.Index('idx_match_results_created_at', 'created_at'),
        
        # Composite indexes for common queries
        sa.Index('idx_match_results_patient_trial', 'patient_id', 'trial_nct_id'),
        sa.Index('idx_match_results_status_score', 'match_status', 'overall_score'),
    )
    
    # Create audit_logs table for HIPAA compliance
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),  # patient, trial, match_result
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),  # create, read, update, delete
        sa.Column('timestamp', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6 compatible
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('data_hash', sa.String(64), nullable=True),
        
        # Indexes for audit queries
        sa.Index('idx_audit_logs_timestamp', 'timestamp'),
        sa.Index('idx_audit_logs_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_audit_logs_user_id', 'user_id'),
        sa.Index('idx_audit_logs_event_type', 'event_type'),
    )
    
    # Create patient_sessions table for session management
    op.create_table(
        'patient_sessions',
        sa.Column('session_id', sa.String(100), primary_key=True),
        sa.Column('patient_id', sa.String(100), nullable=True),  # Nullable for anonymous sessions
        sa.Column('session_data', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('last_activity', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        
        # Foreign key (nullable for anonymous sessions)
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        
        # Indexes for session management
        sa.Index('idx_patient_sessions_patient_id', 'patient_id'),
        sa.Index('idx_patient_sessions_expires_at', 'expires_at'),
        sa.Index('idx_patient_sessions_last_activity', 'last_activity'),
        sa.Index('idx_patient_sessions_is_active', 'is_active'),
    )


def downgrade():
    """Drop all tables in reverse order."""
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('patient_sessions')
    op.drop_table('audit_logs')
    op.drop_table('match_results')
    op.drop_table('eligibility_criteria')
    op.drop_table('trials')
    op.drop_table('patients')


def create_views():
    """Create useful database views for reporting and analysis."""
    
    # View for active trials with match statistics
    op.execute("""
        CREATE VIEW active_trials_summary AS
        SELECT 
            t.nct_id,
            t.title,
            t.status,
            t.phase,
            t.primary_purpose,
            t.enrollment,
            COUNT(mr.match_id) as total_matches,
            COUNT(CASE WHEN mr.match_status = 'eligible' THEN 1 END) as eligible_matches,
            AVG(mr.overall_score) as avg_match_score,
            AVG(mr.confidence_score) as avg_confidence_score,
            MAX(mr.created_at) as last_match_date
        FROM trials t
        LEFT JOIN match_results mr ON t.nct_id = mr.trial_nct_id
        WHERE t.status IN ('recruiting', 'not_yet_recruiting', 'enrolling_by_invitation')
        GROUP BY t.nct_id, t.title, t.status, t.phase, t.primary_purpose, t.enrollment
    """)
    
    # View for patient match summary
    op.execute("""
        CREATE VIEW patient_matches_summary AS
        SELECT 
            p.patient_id,
            p.age,
            p.gender,
            COUNT(mr.match_id) as total_matches,
            COUNT(CASE WHEN mr.match_status = 'eligible' THEN 1 END) as eligible_matches,
            AVG(mr.overall_score) as avg_match_score,
            MAX(mr.overall_score) as best_match_score,
            MAX(mr.created_at) as last_match_date
        FROM patients p
        LEFT JOIN match_results mr ON p.patient_id = mr.patient_id
        GROUP BY p.patient_id, p.age, p.gender
    """)


def drop_views():
    """Drop database views."""
    op.execute("DROP VIEW IF EXISTS patient_matches_summary")
    op.execute("DROP VIEW IF EXISTS active_trials_summary")


# Additional helper functions for data migration and cleanup

def create_initial_data():
    """Create initial data for system setup."""
    
    # Insert system configuration data
    op.execute("""
        INSERT INTO audit_logs (id, event_type, entity_type, entity_id, action, timestamp, details)
        VALUES (
            'AUDIT-INIT-001',
            'system_initialization',
            'system',
            'medmatch_ai',
            'create',
            CURRENT_TIMESTAMP,
            '{"message": "MedMatch AI database initialized", "version": "1.0.0"}'
        )
    """)


def cleanup_test_data():
    """Clean up any test data that might interfere with production."""
    
    # Remove any test patients
    op.execute("DELETE FROM patients WHERE patient_id LIKE 'TEST-%'")
    
    # Remove any test trials
    op.execute("DELETE FROM trials WHERE nct_id LIKE 'NCT00000%'")
    
    # Remove test match results
    op.execute("DELETE FROM match_results WHERE match_id LIKE 'MATCH-TEST-%'")


def verify_schema():
    """Verify that the schema was created correctly."""
    
    # This would typically include checks for:
    # - Table existence
    # - Index existence
    # - Foreign key constraints
    # - Column types and constraints
    
    pass  # Implementation would depend on database-specific queries


# Performance optimization functions

def optimize_for_production():
    """Apply production-specific optimizations."""
    
    # These optimizations would be database-specific
    # For PostgreSQL:
    # - VACUUM ANALYZE
    # - Update table statistics
    # - Set appropriate work_mem, shared_buffers
    
    # For MySQL:
    # - OPTIMIZE TABLE commands
    # - Update index statistics
    
    # For SQLite:
    # - VACUUM
    # - ANALYZE
    # - Set appropriate PRAGMA settings
    
    pass


def create_materialized_views():
    """Create materialized views for complex queries (PostgreSQL only)."""
    
    # Only for PostgreSQL databases
    # Create materialized views for expensive aggregate queries
    # that don't need real-time data
    
    pass