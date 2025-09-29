"""
Configuration management using Pydantic settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "MedMatch AI"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = "/api/v1"
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./medmatch.db",
        env="DATABASE_URL"
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Cerebras API
    cerebras_api_key: str = Field(env="CEREBRAS_API_KEY")
    cerebras_base_url: str = Field(
        default="https://api.cerebras.ai/v1",
        env="CEREBRAS_BASE_URL"
    )
    cerebras_model: str = Field(
        default="llama3.1-8b",
        env="CEREBRAS_MODEL"
    )
    cerebras_max_tokens: int = Field(default=1000, env="CEREBRAS_MAX_TOKENS")
    cerebras_timeout: int = Field(default=30, env="CEREBRAS_TIMEOUT")
    
    # ClinicalTrials.gov API
    clinicaltrials_base_url: str = Field(
        default="https://clinicaltrials.gov/api/v2",
        env="CLINICALTRIALS_BASE_URL"
    )
    clinicaltrials_rate_limit: int = Field(
        default=100,  # requests per minute
        env="CLINICALTRIALS_RATE_LIMIT"
    )
    
    # Redis Cache
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Security
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "json"
    
    # AI/ML Settings
    spacy_model: str = Field(default="en_core_web_sm", env="SPACY_MODEL")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    vector_dimension: int = 384
    similarity_threshold: float = 0.7
    
    # Trial Ingestion
    trial_batch_size: int = Field(default=100, env="TRIAL_BATCH_SIZE")
    trial_sync_interval_hours: int = Field(default=24, env="TRIAL_SYNC_INTERVAL")
    
    # HIPAA Compliance
    hipaa_safe_logging: bool = Field(default=True, env="HIPAA_SAFE_LOGGING")
    data_retention_days: int = Field(default=90, env="DATA_RETENTION_DAYS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()