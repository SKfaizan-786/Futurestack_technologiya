"""
Unit tests for validation utilities.
"""
import pytest
from src.utils.validation import (
    validate_nct_id,
    validate_patient_data,
    sanitize_input,
    validate_email,
    validate_trial_criteria,
    validate_notification_preferences
)


class TestValidateNctId:
    """Test NCT ID validation."""
    
    def test_valid_nct_id(self):
        """Test valid NCT ID formats."""
        assert validate_nct_id("NCT12345678") is True
        assert validate_nct_id("nct12345678") is True  # Should handle lowercase
    
    def test_invalid_nct_id(self):
        """Test invalid NCT ID formats."""
        assert validate_nct_id("") is False
        assert validate_nct_id(None) is False
        assert validate_nct_id("NCT123") is False  # Too short
        assert validate_nct_id("NCT123456789") is False  # Too long
        assert validate_nct_id("ABC12345678") is False  # Wrong prefix


class TestValidateEmail:
    """Test email validation."""
    
    def test_valid_email(self):
        """Test valid email formats."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.org") is True
        assert validate_email("test+tag@example.co.uk") is True
    
    def test_invalid_email(self):
        """Test invalid email formats."""
        assert validate_email("") is False
        assert validate_email(None) is False
        assert validate_email("invalid-email") is False
        assert validate_email("@example.com") is False
        assert validate_email("test@") is False


class TestSanitizeInput:
    """Test input sanitization."""
    
    def test_sanitize_ssn(self):
        """Test SSN redaction."""
        result = sanitize_input("Patient SSN is 123-45-6789")
        assert "[SSN-REDACTED]" in result
        assert "123-45-6789" not in result
    
    def test_sanitize_phone(self):
        """Test phone number redaction."""
        result = sanitize_input("Call me at 555-123-4567")
        assert "[PHONE-REDACTED]" in result
        assert "555-123-4567" not in result
        
        result = sanitize_input("Phone: (555) 123-4567")
        assert "[PHONE-REDACTED]" in result
    
    def test_sanitize_email(self):
        """Test email redaction."""
        result = sanitize_input("Email me at test@example.com")
        assert "[EMAIL-REDACTED]" in result
        assert "test@example.com" not in result
    
    def test_sanitize_id_numbers(self):
        """Test ID number redaction."""
        result = sanitize_input("Patient ID 123456789")
        assert "[ID-REDACTED]" in result
        assert "123456789" not in result
    
    def test_sanitize_non_string(self):
        """Test sanitization of non-string input."""
        assert sanitize_input(123) == "123"
        assert sanitize_input(None) == "None"


class TestValidatePatientData:
    """Test patient data validation."""
    
    def test_valid_patient_data(self):
        """Test valid patient data."""
        patient_data = {
            "medical_history": "Diabetes, hypertension",
            "demographics": {"age": 45, "gender": "male"}
        }
        assert validate_patient_data(patient_data) is True
    
    def test_empty_patient_data(self):
        """Test empty patient data."""
        with pytest.raises(ValueError, match="Patient data cannot be empty"):
            validate_patient_data({})
        
        with pytest.raises(ValueError, match="Patient data cannot be empty"):
            validate_patient_data(None)
    
    def test_missing_required_fields(self):
        """Test patient data without required fields."""
        patient_data = {"other_field": "value"}
        with pytest.raises(ValueError, match="must contain at least one of"):
            validate_patient_data(patient_data)
    
    def test_invalid_demographics(self):
        """Test invalid demographics."""
        patient_data = {
            "medical_history": "Some history",
            "demographics": "not a dict"
        }
        with pytest.raises(ValueError, match="Demographics must be a dictionary"):
            validate_patient_data(patient_data)
    
    def test_invalid_age(self):
        """Test invalid age in demographics."""
        patient_data = {
            "medical_history": "Some history", 
            "demographics": {"age": -5}
        }
        with pytest.raises(ValueError, match="Age must be a number between 0 and 120"):
            validate_patient_data(patient_data)
        
        patient_data["demographics"]["age"] = 150
        with pytest.raises(ValueError, match="Age must be a number between 0 and 120"):
            validate_patient_data(patient_data)
    
    def test_invalid_gender(self):
        """Test invalid gender in demographics."""
        patient_data = {
            "medical_history": "Some history",
            "demographics": {"gender": "invalid"}
        }
        with pytest.raises(ValueError, match="Gender must be one of"):
            validate_patient_data(patient_data)
    
    def test_empty_medical_history_string(self):
        """Test empty medical history string."""
        patient_data = {"medical_history": "   "}
        with pytest.raises(ValueError, match="Medical history cannot be empty"):
            validate_patient_data(patient_data)
    
    def test_long_medical_history(self):
        """Test medical history that's too long."""
        patient_data = {"medical_history": "x" * 50001}
        with pytest.raises(ValueError, match="Medical history exceeds maximum length"):
            validate_patient_data(patient_data)
    
    def test_empty_medical_history_dict(self):
        """Test empty medical history dictionary."""
        # First add another required field so medical_history validation gets triggered
        patient_data = {
            "medical_history": {},
            "demographics": {"age": 45}  # Valid demographics to pass initial validation
        }
        with pytest.raises(ValueError, match="Medical history dictionary cannot be empty"):
            validate_patient_data(patient_data)
    
    def test_invalid_medical_history_type(self):
        """Test invalid medical history type."""
        patient_data = {"medical_history": 123}
        with pytest.raises(ValueError, match="Medical history must be a string or dictionary"):
            validate_patient_data(patient_data)


class TestValidateTrialCriteria:
    """Test trial criteria validation."""
    
    def test_valid_trial_criteria(self):
        """Test valid trial criteria."""
        criteria = {
            "condition": "diabetes",
            "radius": 50
        }
        assert validate_trial_criteria(criteria) is True
    
    def test_invalid_criteria_type(self):
        """Test invalid criteria type."""
        with pytest.raises(ValueError, match="Trial criteria must be a dictionary"):
            validate_trial_criteria("not a dict")
    
    def test_invalid_radius(self):
        """Test invalid radius."""
        criteria = {"radius": -1}
        with pytest.raises(ValueError, match="Radius must be a number between 0 and 5000"):
            validate_trial_criteria(criteria)
        
        criteria = {"radius": 10000}
        with pytest.raises(ValueError, match="Radius must be a number between 0 and 5000"):
            validate_trial_criteria(criteria)
    
    def test_invalid_condition(self):
        """Test invalid condition."""
        criteria = {"condition": ""}
        with pytest.raises(ValueError, match="Condition must be a non-empty string"):
            validate_trial_criteria(criteria)
        
        criteria = {"condition": 123}
        with pytest.raises(ValueError, match="Condition must be a non-empty string"):
            validate_trial_criteria(criteria)
    
    def test_invalid_conditions_list(self):
        """Test invalid conditions list."""
        criteria = {"conditions": "not a list"}
        with pytest.raises(ValueError, match="Conditions must be a list"):
            validate_trial_criteria(criteria)
        
        criteria = {"conditions": []}
        with pytest.raises(ValueError, match="Conditions list cannot be empty"):
            validate_trial_criteria(criteria)
        
        criteria = {"conditions": ["valid"] * 21}
        with pytest.raises(ValueError, match="Too many conditions specified"):
            validate_trial_criteria(criteria)
        
        criteria = {"conditions": ["valid", ""]}
        with pytest.raises(ValueError, match="Each condition must be a non-empty string"):
            validate_trial_criteria(criteria)


class TestValidateNotificationPreferences:
    """Test notification preferences validation."""
    
    def test_valid_preferences(self):
        """Test valid notification preferences."""
        preferences = {
            "frequency": "weekly",
            "notify_on": ["new_trials"],
            "max_distance": 100
        }
        assert validate_notification_preferences(preferences) is True
    
    def test_invalid_preferences_type(self):
        """Test invalid preferences type."""
        with pytest.raises(ValueError, match="Notification preferences must be a dictionary"):
            validate_notification_preferences("not a dict")
    
    def test_invalid_frequency(self):
        """Test invalid frequency."""
        preferences = {"frequency": "invalid"}
        with pytest.raises(ValueError, match="Frequency must be one of"):
            validate_notification_preferences(preferences)
    
    def test_invalid_notify_on_type(self):
        """Test invalid notify_on type."""
        preferences = {"notify_on": "not a list"}
        with pytest.raises(ValueError, match="notify_on must be a list"):
            validate_notification_preferences(preferences)
    
    def test_invalid_notify_on_event(self):
        """Test invalid notify_on event."""
        preferences = {"notify_on": ["invalid_event"]}
        with pytest.raises(ValueError, match="Invalid notification event"):
            validate_notification_preferences(preferences)
    
    def test_invalid_max_distance(self):
        """Test invalid max_distance."""
        preferences = {"max_distance": -10}
        with pytest.raises(ValueError, match="max_distance must be a positive number"):
            validate_notification_preferences(preferences)