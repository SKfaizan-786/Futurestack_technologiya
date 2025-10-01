"""
Contract tests for MatchResult model with reasoning chain.

These tests define the expected behavior for patient-trial matching results
and AI reasoning chain tracking in the MedMatch AI system.
"""
import pytest
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import ValidationError


class TestMatchResultModelContract:
    """Contract tests for MatchResult model behavior."""
    
    def test_match_result_basic_structure(self):
        """MatchResult must have proper basic structure."""
        from src.models.match_result import MatchResult
        
        valid_match_data = {
            "match_id": "MATCH-2025-001",
            "patient_id": "PAT-2025-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.85,
            "confidence_score": 0.92,
            "match_status": "eligible",
            "reasoning_chain": [
                {
                    "step": 1,
                    "category": "age_check",
                    "result": "pass",
                    "details": "Patient age 45 is within trial range 18-65",
                    "score": 1.0
                }
            ],
            "created_at": "2025-09-30T10:00:00Z"
        }
        
        match_result = MatchResult(**valid_match_data)
        assert match_result.match_id == "MATCH-2025-001"
        assert match_result.patient_id == "PAT-2025-001"
        assert match_result.trial_nct_id == "NCT12345678"
        assert match_result.overall_score == 0.85
        assert match_result.confidence_score == 0.92
        assert match_result.match_status == "eligible"
        
    def test_match_result_score_validation(self):
        """Match scores must be within valid range [0.0, 1.0]."""
        from src.models.match_result import MatchResult
        
        base_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "match_status": "eligible",
            "reasoning_chain": []
        }
        
        # Valid scores
        valid_scores = [0.0, 0.25, 0.5, 0.75, 1.0]
        for score in valid_scores:
            match_result = MatchResult(
                **base_data,
                overall_score=score,
                confidence_score=score
            )
            assert match_result.overall_score == score
            assert match_result.confidence_score == score
            
        # Invalid scores should raise ValidationError
        invalid_scores = [-0.1, 1.1, -1.0, 2.0]
        for score in invalid_scores:
            with pytest.raises(ValidationError):
                MatchResult(**base_data, overall_score=score, confidence_score=0.5)
            with pytest.raises(ValidationError):
                MatchResult(**base_data, overall_score=0.5, confidence_score=score)
                
    def test_match_status_validation(self):
        """Match status must be from valid options."""
        from src.models.match_result import MatchResult
        
        base_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.5,
            "confidence_score": 0.5,
            "reasoning_chain": []
        }
        
        valid_statuses = [
            "eligible",
            "ineligible",
            "potentially_eligible",
            "requires_review",
            "insufficient_data"
        ]
        
        for status in valid_statuses:
            match_result = MatchResult(**base_data, match_status=status)
            assert match_result.match_status == status
            
        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            MatchResult(**base_data, match_status="invalid_status")
            
    def test_reasoning_chain_structure(self):
        """Reasoning chain must have proper structure."""
        from src.models.match_result import MatchResult
        
        base_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.85,
            "confidence_score": 0.90,
            "match_status": "eligible"
        }
        
        valid_reasoning_chain = [
            {
                "step": 1,
                "category": "age_check",
                "result": "pass",
                "details": "Patient age 45 is within trial range 18-65",
                "score": 1.0,
                "weight": 0.2
            },
            {
                "step": 2,
                "category": "condition_match",
                "result": "pass",
                "details": "Patient has diabetes, trial targets diabetes",
                "score": 0.95,
                "weight": 0.4
            },
            {
                "step": 3,
                "category": "exclusion_check",
                "result": "pass",
                "details": "No exclusion criteria violations found",
                "score": 1.0,
                "weight": 0.3
            }
        ]
        
        match_result = MatchResult(
            **base_data,
            reasoning_chain=valid_reasoning_chain
        )
        
        assert len(match_result.reasoning_chain) == 3
        assert match_result.reasoning_chain[0]["step"] == 1
        assert match_result.reasoning_chain[0]["category"] == "age_check"
        assert match_result.reasoning_chain[1]["score"] == 0.95
        
    def test_reasoning_step_validation(self):
        """Each reasoning step must have required fields."""
        from src.models.match_result import MatchResult
        
        base_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.85,
            "confidence_score": 0.90,
            "match_status": "eligible"
        }
        
        # Valid reasoning step
        valid_step = {
            "step": 1,
            "category": "age_check",
            "result": "pass",
            "details": "Age verification passed",
            "score": 1.0
        }
        
        match_result = MatchResult(
            **base_data,
            reasoning_chain=[valid_step]
        )
        assert len(match_result.reasoning_chain) == 1
        
        # Step with missing required fields should raise ValidationError
        invalid_steps = [
            {"step": 1, "result": "pass"},  # Missing category and details
            {"category": "age_check", "result": "pass"},  # Missing step
            {"step": 1, "category": "age_check"}  # Missing result
        ]
        
        for invalid_step in invalid_steps:
            with pytest.raises(ValidationError):
                MatchResult(**base_data, reasoning_chain=[invalid_step])
                
    def test_reasoning_categories(self):
        """Reasoning categories must be from valid options."""
        from src.models.match_result import MatchResult
        
        base_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.85,
            "confidence_score": 0.90,
            "match_status": "eligible"
        }
        
        valid_categories = [
            "age_check",
            "gender_check",
            "condition_match",
            "medication_compatibility",
            "allergy_check",
            "exclusion_check",
            "inclusion_check",
            "location_proximity",
            "trial_status_check"
        ]
        
        for category in valid_categories:
            step = {
                "step": 1,
                "category": category,
                "result": "pass",
                "details": f"Testing {category}",
                "score": 1.0
            }
            match_result = MatchResult(
                **base_data,
                reasoning_chain=[step]
            )
            assert match_result.reasoning_chain[0]["category"] == category
            
    def test_reasoning_result_validation(self):
        """Reasoning step results must be from valid options."""
        from src.models.match_result import MatchResult
        
        base_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.85,
            "confidence_score": 0.90,
            "match_status": "eligible"
        }
        
        valid_results = [
            "pass",
            "fail",
            "partial",
            "unknown",
            "requires_review"
        ]
        
        for result in valid_results:
            step = {
                "step": 1,
                "category": "age_check",
                "result": result,
                "details": f"Testing {result}",
                "score": 0.5
            }
            match_result = MatchResult(
                **base_data,
                reasoning_chain=[step]
            )
            assert match_result.reasoning_chain[0]["result"] == result
            
    def test_match_result_eligibility_summary(self):
        """MatchResult must provide eligibility summary."""
        from src.models.match_result import MatchResult
        
        reasoning_chain = [
            {
                "step": 1,
                "category": "age_check",
                "result": "pass",
                "details": "Age requirement met",
                "score": 1.0
            },
            {
                "step": 2,
                "category": "condition_match",
                "result": "pass",
                "details": "Medical condition matches",
                "score": 0.9
            },
            {
                "step": 3,
                "category": "exclusion_check",
                "result": "fail",
                "details": "Has excluded medication",
                "score": 0.0
            }
        ]
        
        match_result = MatchResult(
            match_id="MATCH-001",
            patient_id="PAT-001",
            trial_nct_id="NCT12345678",
            overall_score=0.6,
            confidence_score=0.8,
            match_status="ineligible",
            reasoning_chain=reasoning_chain
        )
        
        # MatchResult should provide summary methods
        assert hasattr(match_result, 'get_eligibility_summary'), "Must provide eligibility summary"
        assert hasattr(match_result, 'get_failed_criteria'), "Must identify failed criteria"
        assert hasattr(match_result, 'get_passed_criteria'), "Must identify passed criteria"
        
        summary = match_result.get_eligibility_summary()
        assert isinstance(summary, dict)
        assert "passed_checks" in summary
        assert "failed_checks" in summary
        
        failed_criteria = match_result.get_failed_criteria()
        assert isinstance(failed_criteria, list)
        assert any(step["category"] == "exclusion_check" for step in failed_criteria)
        
    def test_match_result_explanation_generation(self):
        """MatchResult must generate human-readable explanations."""
        from src.models.match_result import MatchResult
        
        reasoning_chain = [
            {
                "step": 1,
                "category": "age_check",
                "result": "pass",
                "details": "Patient age 45 falls within required range 18-65",
                "score": 1.0
            },
            {
                "step": 2,
                "category": "condition_match",
                "result": "pass",
                "details": "Patient has diabetes, trial studies diabetes treatment",
                "score": 0.95
            }
        ]
        
        match_result = MatchResult(
            match_id="MATCH-001",
            patient_id="PAT-001",
            trial_nct_id="NCT12345678",
            overall_score=0.95,
            confidence_score=0.90,
            match_status="eligible",
            reasoning_chain=reasoning_chain
        )
        
        # Should generate human-readable explanation
        assert hasattr(match_result, 'get_explanation'), "Must generate explanation"
        explanation = match_result.get_explanation()
        assert isinstance(explanation, str)
        assert "eligible" in explanation.lower()
        assert "diabetes" in explanation.lower()
        
    def test_match_result_confidence_factors(self):
        """MatchResult must track confidence factors."""
        from src.models.match_result import MatchResult
        
        match_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.85,
            "confidence_score": 0.75,
            "match_status": "potentially_eligible",
            "confidence_factors": {
                "data_completeness": 0.8,
                "criteria_clarity": 0.9,
                "llm_confidence": 0.7,
                "similarity_score": 0.85
            },
            "reasoning_chain": []
        }
        
        match_result = MatchResult(**match_data)
        assert hasattr(match_result, 'confidence_factors'), "Must track confidence factors"
        assert match_result.confidence_factors["data_completeness"] == 0.8
        assert match_result.confidence_factors["llm_confidence"] == 0.7
        
    def test_match_result_next_steps(self):
        """MatchResult must suggest next steps for patients."""
        from src.models.match_result import MatchResult
        
        match_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.85,
            "confidence_score": 0.90,
            "match_status": "eligible",
            "next_steps": [
                "Contact study coordinator at 617-555-0123",
                "Schedule screening appointment",
                "Prepare recent medical records"
            ],
            "reasoning_chain": []
        }
        
        match_result = MatchResult(**match_data)
        assert hasattr(match_result, 'next_steps'), "Must provide next steps"
        assert len(match_result.next_steps) == 3
        assert "Contact study coordinator" in match_result.next_steps[0]
        
    def test_match_result_audit_trail(self):
        """MatchResult must support audit trail for HIPAA compliance."""
        from src.models.match_result import MatchResult
        
        match_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.85,
            "confidence_score": 0.90,
            "match_status": "eligible",
            "reasoning_chain": [],
            "audit_metadata": {
                "ai_model_version": "llama-3.2-70b",
                "processing_time_ms": 1250,
                "data_sources": ["patient_input", "clinicaltrials_gov"],
                "privacy_level": "anonymized"
            }
        }
        
        match_result = MatchResult(**match_data)
        assert hasattr(match_result, 'audit_metadata'), "Must support audit metadata"
        assert match_result.audit_metadata["ai_model_version"] == "llama-3.2-70b"
        assert match_result.audit_metadata["privacy_level"] == "anonymized"
        
    def test_match_result_serialization(self):
        """MatchResult must serialize/deserialize correctly."""
        from src.models.match_result import MatchResult
        
        original_data = {
            "match_id": "MATCH-001",
            "patient_id": "PAT-001",
            "trial_nct_id": "NCT12345678",
            "overall_score": 0.85,
            "confidence_score": 0.90,
            "match_status": "eligible",
            "reasoning_chain": [
                {
                    "step": 1,
                    "category": "age_check",
                    "result": "pass",
                    "details": "Age check passed",
                    "score": 1.0
                }
            ]
        }
        
        # Create, serialize, and deserialize
        match_result = MatchResult(**original_data)
        serialized = match_result.model_dump()
        deserialized = MatchResult(**serialized)
        
        assert deserialized.match_id == match_result.match_id
        assert deserialized.overall_score == match_result.overall_score
        assert len(deserialized.reasoning_chain) == len(match_result.reasoning_chain)
        assert deserialized.reasoning_chain[0]["category"] == "age_check"
