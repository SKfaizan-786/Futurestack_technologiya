"""
HIPAA-compliant structured logging configuration for MedMatch AI.

Provides secure logging without patient data exposure,
request tracking, and performance monitoring.
"""
import sys
import os
from typing import Any, Dict, Optional
from datetime import datetime
import structlog
from structlog.typing import FilteringBoundLogger
import logging.config

from .config import settings


def remove_pii_processor(logger: FilteringBoundLogger, name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processor to remove potential PII from log messages.
    
    Args:
        logger: The logger instance
        name: The name of the logger
        event_dict: The event dictionary to process
        
    Returns:
        Cleaned event dictionary
    """
    if not settings.hipaa_safe_logging:
        return event_dict
    
    # Fields that should never appear in logs
    pii_fields = {
        'name', 'first_name', 'last_name', 'full_name',
        'email', 'phone', 'telephone', 'mobile',
        'ssn', 'social_security', 'mrn', 'medical_record_number',
        'dob', 'date_of_birth', 'birthday',
        'address', 'street', 'home_address', 'zip', 'zipcode', 'postal_code',
        'insurance_id', 'policy_number', 'member_id',
        'emergency_contact', 'next_of_kin',
        'credit_card', 'payment_info', 'billing_info'
    }
    
    def clean_value(value: Any) -> Any:
        """Recursively clean values of PII."""
        if isinstance(value, dict):
            return {k: clean_value(v) for k, v in value.items() 
                   if k.lower() not in pii_fields}
        elif isinstance(value, list):
            return [clean_value(item) for item in value]
        elif isinstance(value, str):
            # Check if the string looks like potential PII
            lower_value = value.lower()
            if any(field in lower_value for field in ['@', 'ssn', 'social']):
                return "[REDACTED]"
            return value
        else:
            return value
    
    # Clean the entire event dictionary
    cleaned_event = {}
    for key, value in event_dict.items():
        if key.lower() in pii_fields:
            cleaned_event[key] = "[REDACTED]"
        else:
            cleaned_event[key] = clean_value(value)
    
    return cleaned_event


def add_request_context_processor(
    logger: FilteringBoundLogger, name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add request context to log messages when available.
    
    Args:
        logger: The logger instance
        name: The name of the logger
        event_dict: The event dictionary to process
        
    Returns:
        Event dictionary with request context
    """
    # Try to get request context from various sources
    request_id = None
    
    # Check if request_id is already in the event
    if 'request_id' in event_dict:
        return event_dict
    
    # Try to get from structlog context
    try:
        bound_logger = logger.bind()
        if hasattr(bound_logger, '_context') and 'request_id' in bound_logger._context:
            request_id = bound_logger._context['request_id']
    except Exception:
        pass
    
    # Try to get from thread-local storage (if using threading)
    try:
        import threading
        current_thread = threading.current_thread()
        if hasattr(current_thread, 'request_id'):
            request_id = current_thread.request_id
    except Exception:
        pass
    
    if request_id:
        event_dict['request_id'] = request_id
    
    return event_dict


def add_application_context_processor(
    logger: FilteringBoundLogger, name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add application context to all log messages.
    
    Args:
        logger: The logger instance
        name: The name of the logger
        event_dict: The event dictionary to process
        
    Returns:
        Event dictionary with application context
    """
    event_dict.update({
        'app_name': settings.app_name,
        'app_version': settings.app_version,
        'environment': settings.environment,
        'service': 'medmatch-api'
    })
    
    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging for the application.
    
    Sets up HIPAA-compliant logging with appropriate processors
    and formatters based on environment.
    """
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure processors based on environment
    processors = [
        # Built-in processors
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        
        # Custom processors
        remove_pii_processor,
        add_request_context_processor,
        add_application_context_processor,
        
        # Timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        
        # Exception handling
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        
        # String processing
        structlog.processors.UnicodeDecoder(),
        
        # Final formatter
        structlog.processors.JSONRenderer() if settings.log_format == "json" 
        else structlog.dev.ConsoleRenderer(colors=settings.environment == "development")
    ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'format': '%(message)s'
            },
            'console': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'json' if settings.log_format == "json" else 'console',
                'stream': sys.stdout
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
            'uvicorn': {
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
            'uvicorn.access': {
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
            'sqlalchemy': {
                'handlers': ['console'],
                'level': logging.WARNING if not settings.database_echo else logging.INFO,
                'propagate': False
            },
            'httpx': {
                'handlers': ['console'],
                'level': logging.WARNING,
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_patient_access(
    session_id: str,
    action: str,
    description: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log patient data access for HIPAA compliance.
    
    Args:
        session_id: Patient session identifier
        action: Action performed (view, create, update, delete)
        description: Description of the action
        request_id: Request identifier for tracing
        user_id: User performing the action (if authenticated)
        additional_context: Additional context information
    """
    logger = get_logger("audit")
    
    audit_data = {
        'event_type': 'patient_access',
        'action': action,
        'description': description,
        'session_id': session_id,
        'timestamp': datetime.now().isoformat()
    }
    
    if request_id:
        audit_data['request_id'] = request_id
    
    if user_id:
        audit_data['user_id'] = user_id
    
    if additional_context:
        # Ensure no PII in additional context
        audit_data['context'] = remove_pii_processor(
            logger, 'audit', additional_context
        )
    
    logger.info("Patient data accessed", **audit_data)


def log_api_call(
    service: str,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    request_id: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """
    Log external API calls for monitoring and debugging.
    
    Args:
        service: Service name (cerebras, clinicaltrials)
        endpoint: API endpoint called
        method: HTTP method
        status_code: Response status code
        response_time_ms: Response time in milliseconds
        request_id: Request identifier for tracing
        error: Error message if call failed
    """
    logger = get_logger("api_calls")
    
    log_data = {
        'event_type': 'api_call',
        'service': service,
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'response_time_ms': response_time_ms,
        'timestamp': datetime.now().isoformat()
    }
    
    if request_id:
        log_data['request_id'] = request_id
    
    if error:
        log_data['error'] = error
        logger.error("API call failed", **log_data)
    else:
        logger.info("API call completed", **log_data)


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str,
    tags: Optional[Dict[str, str]] = None,
    request_id: Optional[str] = None
) -> None:
    """
    Log performance metrics for monitoring.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        tags: Additional tags for categorization
        request_id: Request identifier for tracing
    """
    logger = get_logger("metrics")
    
    metric_data = {
        'event_type': 'performance_metric',
        'metric_name': metric_name,
        'value': value,
        'unit': unit,
        'timestamp': datetime.now().isoformat()
    }
    
    if tags:
        metric_data['tags'] = tags
    
    if request_id:
        metric_data['request_id'] = request_id
    
    logger.info("Performance metric recorded", **metric_data)


# Initialize logging when module is imported
configure_logging()