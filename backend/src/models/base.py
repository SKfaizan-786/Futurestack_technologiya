"""
Database base configuration and models for MedMatch AI.

Provides SQLAlchemy async engine, session management,
and base model classes with HIPAA-compliant design.
"""
import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional
import structlog
from sqlalchemy import create_engine, MetaData, String, DateTime, Text, JSON, Boolean, Float, Integer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.sql import func

from ..utils.config import settings

logger = structlog.get_logger(__name__)

# SQLAlchemy metadata for migrations
metadata = MetaData()


class Base(DeclarativeBase):
    """
    Base class for all database models.
    
    Provides common fields and HIPAA-compliant design patterns.
    """
    metadata = metadata
    
    # Common timestamp fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for JSON serialization."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class PatientSession(Base):
    """
    Patient session data for trial matching.
    
    Stores anonymized patient data temporarily for matching analysis.
    Automatically expires based on HIPAA retention policies.
    
    Note: No PII is stored - only medical data needed for matching.
    """
    __tablename__ = "patient_sessions"
    
    # Primary key
    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    
    # Patient demographics (no PII)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Medical information (JSON for flexibility)
    conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    medications: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    medical_history: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    lab_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    allergies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Location (city/state only - no addresses)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location_country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Session metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Analytics (non-PII)
    total_matches_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class ClinicalTrial(Base):
    """
    Clinical trial information cached from ClinicalTrials.gov.
    
    Stores normalized trial data for faster matching and search.
    """
    __tablename__ = "clinical_trials"
    
    # Primary key
    nct_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    
    # Basic trial information
    title: Mapped[str] = mapped_column(Text, nullable=False)
    brief_title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    phase: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    study_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Medical conditions (JSON array)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Eligibility criteria (structured JSON)
    eligibility_criteria: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Location information (JSON array of locations)
    locations: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Additional metadata
    sponsor: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Search and matching fields
    search_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For full-text search
    embedding_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of floats
    
    # Data freshness tracking
    last_updated_clinicaltrials: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_synced: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    match_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class MatchResult(Base):
    """
    Results from patient-trial matching analysis.
    
    Stores AI-generated compatibility analysis and reasoning.
    Linked to patient sessions but contains no PII.
    """
    __tablename__ = "match_results"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    nct_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Matching analysis results
    compatibility_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False)  # high/medium/low
    
    # AI reasoning and analysis
    reasoning_text: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility_analysis: Mapped[dict] = mapped_column(JSON, nullable=False)  # Detailed breakdown
    
    # Risk factors and considerations
    exclusion_criteria_met: Mapped[dict] = mapped_column(JSON, nullable=True)
    inclusion_criteria_met: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Recommendations
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)  # recommend/consider/not_suitable
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # AI model metadata
    model_used: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Performance metrics
    analysis_duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    token_usage: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class AuditLog(Base):
    """
    HIPAA-compliant audit log for all system activities.
    
    Tracks all access to patient data and system operations
    without storing actual patient information.
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Event information
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_action: Mapped[str] = mapped_column(String(100), nullable=False)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Session/request context
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    # User context (future - for authenticated users)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    user_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Network information
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # System information
    endpoint: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    http_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Error information (if applicable)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Data access tracking (no actual data, just metadata)
    data_accessed: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Types of data accessed
    data_modified: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Types of data modified
    
    # Timestamp (already provided by Base class)


# Database engine and session management
class DatabaseManager:
    """
    Manages database connections and sessions.
    
    Provides async session management with proper cleanup
    and connection pooling.
    """
    
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database engine and session maker."""
        if self._initialized:
            return
        
        # Create async engine
        self.engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections every hour
        )
        
        # Create session maker
        self.async_session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self._initialized = True
        logger.info("Database manager initialized",
                   database_url=settings.database_url.split("://")[0] + "://***")
    
    async def create_tables(self):
        """Create all database tables."""
        if not self._initialized:
            await self.initialize()
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session with automatic cleanup.
        
        Yields:
            AsyncSession: Database session
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database engine and cleanup connections."""
        if self.engine:
            await self.engine.dispose()
        self._initialized = False
        logger.info("Database manager closed")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI endpoints
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Yields:
        AsyncSession: Database session for request handling
    """
    if not db_manager._initialized:
        await db_manager.initialize()
    
    async with db_manager.async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Database initialization function
async def init_database():
    """Initialize database for application startup."""
    await db_manager.initialize()
    await db_manager.create_tables()
    logger.info("Database initialization completed")