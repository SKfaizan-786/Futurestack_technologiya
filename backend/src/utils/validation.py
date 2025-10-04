"""
Input validation utilities for HIPAA-compliant data processing.
"""
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def validate_nct_id(trial_id: str) -> bool:
    """
    Validate NCT ID format.
    
    Args:
        trial_id: Trial identifier to validate
        
    Returns:
        True if valid NCT ID format, False otherwise
    """
    if not trial_id:
        return False
    
    # NCT ID format: NCT followed by 8 digits
    pattern = r'^NCT\d{8}$'
    return bool(re.match(pattern, trial_id.upper()))


def validate_patient_data(patient_data: Dict[str, Any]) -> bool:
    """
    Validate patient data for required fields and HIPAA compliance.
    
    Args:
        patient_data: Patient data dictionary
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    if not patient_data:
        raise ValueError("Patient data cannot be empty")
    
    # Check for required fields (at least one of these must be present)
    required_fields = [
        "medical_history", 
        "medical_query",    # Add support for natural language queries
        "clinical_notes", 
        "demographics", 
        "current_medications"
    ]
    
    has_required_field = any(
        field in patient_data and patient_data[field] 
        for field in required_fields
    )
    
    if not has_required_field:
        raise ValueError(
            f"Patient data must contain at least one of: {', '.join(required_fields)}"
        )
    
    # Validate specific fields if present
    if "demographics" in patient_data:
        _validate_demographics(patient_data["demographics"])
    
    if "medical_history" in patient_data:
        _validate_medical_history(patient_data["medical_history"])
    
    return True


def sanitize_input(input_string: str) -> str:
    """
    Sanitize input string to remove potential PHI and harmful content.
    
    Args:
        input_string: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not isinstance(input_string, str):
        return str(input_string)
    
    # Remove potential SSN patterns
    sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN-REDACTED]', input_string)
    sanitized = re.sub(r'\b\d{9}\b', '[ID-REDACTED]', sanitized)
    
    # Remove potential phone numbers
    sanitized = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE-REDACTED]', sanitized)
    sanitized = re.sub(r'\(\d{3}\)\s*\d{3}-\d{4}', '[PHONE-REDACTED]', sanitized)
    
    # Remove potential email addresses (basic pattern)
    sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL-REDACTED]', sanitized)
    
    # Trim and normalize whitespace
    sanitized = ' '.join(sanitized.split())
    
    return sanitized


def _validate_demographics(demographics: Dict[str, Any]) -> None:
    """Validate demographics data."""
    if not isinstance(demographics, dict):
        raise ValueError("Demographics must be a dictionary")
    
    # Validate age if present
    if "age" in demographics:
        age = demographics["age"]
        if not isinstance(age, (int, float)) or age < 0 or age > 120:
            raise ValueError("Age must be a number between 0 and 120")
    
    # Validate gender if present
    if "gender" in demographics:
        valid_genders = ["male", "female", "other", "unknown", "prefer_not_to_say"]
        if demographics["gender"].lower() not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")


def _validate_medical_history(medical_history: Any) -> None:
    """Validate medical history data."""
    if isinstance(medical_history, str):
        if len(medical_history.strip()) == 0:
            raise ValueError("Medical history cannot be empty")
        if len(medical_history) > 50000:  # Reasonable limit
            raise ValueError("Medical history exceeds maximum length")
    
    elif isinstance(medical_history, dict):
        # Validate structured medical history
        if not medical_history:
            raise ValueError("Medical history dictionary cannot be empty")
    
    else:
        raise ValueError("Medical history must be a string or dictionary")


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    if not email:
        return False
    
    # Basic email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_trial_criteria(criteria: Dict[str, Any]) -> bool:
    """
    Validate trial search criteria.
    
    Args:
        criteria: Trial criteria dictionary
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    if not isinstance(criteria, dict):
        raise ValueError("Trial criteria must be a dictionary")
    
    # Validate radius if present
    if "radius" in criteria:
        radius = criteria["radius"]
        if not isinstance(radius, (int, float)) or radius < 0 or radius > 5000:
            raise ValueError("Radius must be a number between 0 and 5000 miles")
    
    # Validate condition if present
    if "condition" in criteria:
        condition = criteria["condition"]
        if not isinstance(condition, str) or len(condition.strip()) == 0:
            raise ValueError("Condition must be a non-empty string")
    
    # Validate conditions list if present (for multiple conditions)
    if "conditions" in criteria:
        conditions = criteria["conditions"]
        if not isinstance(conditions, list):
            raise ValueError("Conditions must be a list")
        if len(conditions) > 20:  # Reasonable limit
            raise ValueError("Too many conditions specified (maximum 20)")
        if len(conditions) == 0:
            raise ValueError("Conditions list cannot be empty")
        for condition in conditions:
            if not isinstance(condition, str) or len(condition.strip()) == 0:
                raise ValueError("Each condition must be a non-empty string")
    
    return True


def validate_notification_preferences(preferences: Dict[str, Any]) -> bool:
    """
    Validate notification preferences.
    
    Args:
        preferences: Notification preferences dictionary
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    if not isinstance(preferences, dict):
        raise ValueError("Notification preferences must be a dictionary")
    
    # Validate frequency if present
    if "frequency" in preferences:
        valid_frequencies = ["daily", "weekly", "monthly", "immediate"]
        if preferences["frequency"] not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {', '.join(valid_frequencies)}")
    
    # Validate notify_on if present
    if "notify_on" in preferences:
        notify_on = preferences["notify_on"]
        if not isinstance(notify_on, list):
            raise ValueError("notify_on must be a list")
        
        valid_events = ["new_trials", "status_changes", "enrollment_updates", "results_posted"]
        for event in notify_on:
            if event not in valid_events:
                raise ValueError(f"Invalid notification event: {event}")
    
    # Validate max_distance if present
    if "max_distance" in preferences:
        max_distance = preferences["max_distance"]
        if not isinstance(max_distance, (int, float)) or max_distance < 0:
            raise ValueError("max_distance must be a positive number")
    
    return True