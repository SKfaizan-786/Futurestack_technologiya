"""
MedMatch AI - Prometheus Metrics Service
Healthcare-specific metrics for Docker MCP Gateway showcase
"""

import time
import asyncio
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Info, 
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create custom registry for healthcare metrics
healthcare_registry = CollectorRegistry()

# Healthcare-specific metrics
TRIAL_MATCHES = Counter(
    'medmatch_trial_matches_total',
    'Total number of clinical trial matches performed',
    ['cancer_type', 'location_type', 'match_quality'],
    registry=healthcare_registry
)

TRIAL_MATCH_DURATION = Histogram(
    'medmatch_trial_match_duration_seconds',
    'Time spent matching clinical trials',
    ['cancer_type', 'ai_model'],
    registry=healthcare_registry
)

AI_MODEL_REQUESTS = Counter(
    'medmatch_ai_model_requests_total',
    'Total requests to AI models',
    ['model_name', 'operation_type'],
    registry=healthcare_registry
)

AI_MODEL_LATENCY = Histogram(
    'medmatch_ai_model_latency_seconds',
    'AI model response latency',
    ['model_name', 'operation_type'],
    registry=healthcare_registry
)

PATIENT_SEARCHES = Counter(
    'medmatch_patient_searches_total',
    'Total patient searches performed',
    ['search_type', 'user_type'],
    registry=healthcare_registry
)

SAVED_TRIALS = Gauge(
    'medmatch_saved_trials_count',
    'Current number of saved trials',
    ['user_id'],
    registry=healthcare_registry
)

CLINICAL_TRIALS_API_REQUESTS = Counter(
    'medmatch_clinicaltrials_api_requests_total',
    'Requests to ClinicalTrials.gov API',
    ['endpoint', 'status'],
    registry=healthcare_registry
)

CLINICAL_TRIALS_API_LATENCY = Histogram(
    'medmatch_clinicaltrials_api_latency_seconds',
    'ClinicalTrials.gov API response time',
    ['endpoint'],
    registry=healthcare_registry
)

DATABASE_OPERATIONS = Counter(
    'medmatch_database_operations_total',
    'Database operations performed',
    ['operation', 'table', 'status'],
    registry=healthcare_registry
)

DATABASE_CONNECTION_POOL = Gauge(
    'medmatch_database_connections_active',
    'Active database connections',
    registry=healthcare_registry
)

CACHE_OPERATIONS = Counter(
    'medmatch_cache_operations_total',
    'Cache operations (Redis)',
    ['operation', 'cache_type', 'hit_miss'],
    registry=healthcare_registry
)

HEALTHCARE_COMPLIANCE_EVENTS = Counter(
    'medmatch_compliance_events_total',
    'HIPAA and healthcare compliance events',
    ['event_type', 'severity'],
    registry=healthcare_registry
)

# Application info
APPLICATION_INFO = Info(
    'medmatch_application_info',
    'MedMatch AI application information',
    registry=healthcare_registry
)

# Set application info
APPLICATION_INFO.info({
    'version': '1.0.0',
    'deployment': 'docker',
    'compliance': 'hipaa_ready',
    'ai_models': 'llama3.3-70b,spacy',
    'data_source': 'clinicaltrials.gov'
})

class MetricsService:
    """Healthcare metrics collection and monitoring service"""
    
    def __init__(self):
        self.start_time = time.time()
        self._uptime_task = None
        self._setup_system_metrics()
    
    def _setup_system_metrics(self):
        """Setup system-level metrics"""
        self.system_uptime = Gauge(
            'medmatch_system_uptime_seconds',
            'System uptime in seconds',
            registry=healthcare_registry
        )
    
    async def start_background_tasks(self):
        """Start background tasks (call this after event loop is running)"""
        if self._uptime_task is None:
            self._uptime_task = asyncio.create_task(self._update_uptime_metric())
    
    async def stop_background_tasks(self):
        """Stop background tasks"""
        if self._uptime_task:
            self._uptime_task.cancel()
            try:
                await self._uptime_task
            except asyncio.CancelledError:
                pass
            self._uptime_task = None
    
    async def _update_uptime_metric(self):
        """Update system uptime metric"""
        while True:
            uptime = time.time() - self.start_time
            self.system_uptime.set(uptime)
            await asyncio.sleep(30)  # Update every 30 seconds
    
    @staticmethod
    def track_trial_match(cancer_type: str, location_type: str, match_quality: str):
        """Track clinical trial matching metrics"""
        TRIAL_MATCHES.labels(
            cancer_type=cancer_type,
            location_type=location_type,
            match_quality=match_quality
        ).inc()
    
    @staticmethod
    def track_patient_search(search_type: str, user_type: str = "patient"):
        """Track patient search metrics"""
        PATIENT_SEARCHES.labels(
            search_type=search_type,
            user_type=user_type
        ).inc()
    
    @staticmethod
    def track_saved_trials(user_id: str, count: int):
        """Track saved trials count for user"""
        SAVED_TRIALS.labels(user_id=user_id).set(count)
    
    @staticmethod
    def track_clinical_trials_api(endpoint: str, status: str, latency: float):
        """Track ClinicalTrials.gov API metrics"""
        CLINICAL_TRIALS_API_REQUESTS.labels(
            endpoint=endpoint,
            status=status
        ).inc()
        
        CLINICAL_TRIALS_API_LATENCY.labels(endpoint=endpoint).observe(latency)
    
    @staticmethod
    def track_database_operation(operation: str, table: str, status: str):
        """Track database operation metrics"""
        DATABASE_OPERATIONS.labels(
            operation=operation,
            table=table,
            status=status
        ).inc()
    
    @staticmethod
    def track_cache_operation(operation: str, cache_type: str, hit_miss: str):
        """Track cache operation metrics"""
        CACHE_OPERATIONS.labels(
            operation=operation,
            cache_type=cache_type,
            hit_miss=hit_miss
        ).inc()
    
    @staticmethod
    def track_compliance_event(event_type: str, severity: str):
        """Track healthcare compliance events"""
        HEALTHCARE_COMPLIANCE_EVENTS.labels(
            event_type=event_type,
            severity=severity
        ).inc()
    
    @staticmethod
    def update_database_connections(count: int):
        """Update active database connections gauge"""
        DATABASE_CONNECTION_POOL.set(count)
    
    @staticmethod
    def get_metrics() -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest(healthcare_registry)
    
    @staticmethod
    def get_content_type() -> str:
        """Get Prometheus content type"""
        return CONTENT_TYPE_LATEST

# Decorators for automatic metrics tracking

def track_ai_model_request(model_name: str, operation_type: str):
    """Decorator to track AI model requests and latency"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Track request
                AI_MODEL_REQUESTS.labels(
                    model_name=model_name,
                    operation_type=operation_type
                ).inc()
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Track successful latency
                latency = time.time() - start_time
                AI_MODEL_LATENCY.labels(
                    model_name=model_name,
                    operation_type=operation_type
                ).observe(latency)
                
                return result
                
            except Exception as e:
                # Track error latency
                latency = time.time() - start_time
                AI_MODEL_LATENCY.labels(
                    model_name=f"{model_name}_error",
                    operation_type=operation_type
                ).observe(latency)
                raise
        
        return wrapper
    return decorator

def track_trial_matching(cancer_type: str):
    """Decorator to track trial matching duration"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Track successful matching
                duration = time.time() - start_time
                TRIAL_MATCH_DURATION.labels(
                    cancer_type=cancer_type,
                    ai_model="llama3.3-70b"
                ).observe(duration)
                
                # Determine match quality based on result count
                if isinstance(result, dict) and 'trials' in result:
                    trial_count = len(result.get('trials', []))
                    if trial_count >= 10:
                        quality = "high"
                    elif trial_count >= 5:
                        quality = "medium"
                    else:
                        quality = "low"
                    
                    MetricsService.track_trial_match(
                        cancer_type=cancer_type,
                        location_type="auto_detected",
                        match_quality=quality
                    )
                
                return result
                
            except Exception as e:
                # Track failed matching
                duration = time.time() - start_time
                TRIAL_MATCH_DURATION.labels(
                    cancer_type=f"{cancer_type}_error",
                    ai_model="llama3.3-70b"
                ).observe(duration)
                raise
        
        return wrapper
    return decorator

# Global metrics service instance
metrics_service = MetricsService()

# Export commonly used functions
track_trial_match = MetricsService.track_trial_match
track_patient_search = MetricsService.track_patient_search
track_saved_trials = MetricsService.track_saved_trials
track_clinical_trials_api = MetricsService.track_clinical_trials_api
track_database_operation = MetricsService.track_database_operation
track_cache_operation = MetricsService.track_cache_operation
track_compliance_event = MetricsService.track_compliance_event
update_database_connections = MetricsService.update_database_connections
get_metrics = MetricsService.get_metrics
get_content_type = MetricsService.get_content_type