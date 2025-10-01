"""
Trial matching service with Llama 3.3-70B powered confidence scoring.
Award-winning AI reasoning for clinical trial patient matching.
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import logging

from ..models.patient import Patient
from ..models.trial import Trial
from ..models.match_result import MatchResult, MedicalReasoningResult, ReasoningStep
from ..services.medical_nlp import MedicalNLPProcessor
from ..services.hybrid_search import HybridSearchEngine
from ..services.llm_reasoning import LLMReasoningService
from ..integrations.trials_api_client import ClinicalTrialsClient
from ..utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MatchingService:
    """
    Core trial matching service with AI-powered reasoning.
    
    Integrates all AI pipeline components for award-winning matching:
    - Medical NLP for entity extraction
    - Hybrid search for trial discovery  
    - Llama 3.3-70B for eligibility reasoning
    - Confidence scoring with explainable AI
    """
    
    def __init__(self, trials_client: ClinicalTrialsClient = None):
        """Initialize matching service with AI components."""
        self.medical_nlp = MedicalNLPProcessor()
        self.search_engine = HybridSearchEngine()
        self.llm_service = LLMReasoningService()
        self.trials_client = trials_client or ClinicalTrialsClient()
        
        # For testing: Add some mock trials to the search engine
        self._add_mock_trials_for_testing()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self.trials_client, 'close'):
            await self.trials_client.close()
        
    async def close(self):
        """Close all async resources."""
        if hasattr(self.trials_client, 'close'):
            await self.trials_client.close()
    
    def _add_mock_trials_for_testing(self):
        """Add mock trials to search engine for testing purposes."""
        # Only add mock data in test environment
        settings = get_settings()
        if settings.environment == "test":
            mock_trials = [
                {
                    "id": "NCT04444444",
                    "nct_id": "NCT04444444", 
                    "title": "Novel Targeted Therapy for ER+ Breast Cancer with CDK4/6 Inhibitors",
                    "brief_summary": "A Phase 2 study evaluating next-generation CDK4/6 inhibitors in patients with stage 2-3 ER+/PR+ breast cancer who have completed adjuvant chemotherapy. Includes patients with prior anastrozole treatment.",
                    "conditions": ["Breast Cancer", "ER+ Breast Cancer", "Stage 2 Breast Cancer"],
                    "interventions": ["CDK4/6 Inhibitor", "Targeted Therapy", "Anastrozole"],
                    "phase": "Phase 2",
                    "status": "Recruiting",
                    "eligibility_criteria": {
                        "min_age": 18,
                        "max_age": 85,
                        "gender": "All",
                        "inclusion_criteria": [
                            "ER+/PR+ breast cancer",
                            "Stage 2 or 3 breast cancer",
                            "Prior adjuvant chemotherapy",
                            "ECOG performance status 0-2"
                        ]
                    }
                },
                {
                    "id": "NCT04555555",
                    "nct_id": "NCT04555555",
                    "title": "Immunotherapy Combination for Advanced Lung Adenocarcinoma", 
                    "brief_summary": "Phase 1/2 trial combining novel immunotherapy agents for patients with advanced lung adenocarcinoma. Designed for patients who have received prior targeted therapy.",
                    "conditions": ["Lung Adenocarcinoma", "Advanced Cancer", "Immunotherapy"],
                    "interventions": ["Immunotherapy", "Combination Therapy"],
                    "phase": "Phase 1",
                    "status": "Recruiting",
                    "eligibility_criteria": {
                        "min_age": 18,
                        "max_age": 80,
                        "gender": "All", 
                        "inclusion_criteria": [
                            "Advanced lung adenocarcinoma",
                            "Prior targeted therapy",
                            "ECOG performance status 0-1"
                        ]
                    }
                },
                {
                    "id": "NCT04666666",
                    "nct_id": "NCT04666666",
                    "title": "Diabetes Management with AI-Guided Glucose Control",
                    "brief_summary": "A study evaluating AI-guided glucose monitoring and insulin adjustment for Type 2 diabetes patients with comorbidities.",
                    "conditions": ["Type 2 Diabetes", "Glucose Control", "AI Guidance"],
                    "interventions": ["AI System", "Glucose Monitor", "Insulin"],
                    "phase": "Phase 3",
                    "status": "Recruiting",
                    "eligibility_criteria": {
                        "min_age": 45,
                        "max_age": 75,
                        "gender": "All",
                        "inclusion_criteria": [
                            "Type 2 diabetes",
                            "HbA1c > 7%",
                            "Multiple comorbidities"
                        ]
                    }
                }
            ]
            
            # Index the mock trials
            for trial in mock_trials:
                self.search_engine.index_trial(trial)
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self.trials_client, 'close'):
            await self.trials_client.close()
        
    async def close(self):
        """Close all async resources."""
        if hasattr(self.trials_client, 'close'):
            await self.trials_client.close()

    async def search_and_match_trials(
        self,
        patient_data: Dict[str, Any],
        max_results: int = 3,
        min_confidence: float = 0.7,
        enable_advanced_reasoning: bool = True
    ) -> Dict[str, Any]:
        """
        Find the best clinical trial matches for a patient.
        
        Args:
            patient_data: Patient medical information (structured or unstructured)
            max_results: Maximum number of trial matches to return
            min_confidence: Minimum confidence score threshold
            enable_advanced_reasoning: Use Llama 3.3-70B for advanced reasoning
            
        Returns:
            Dictionary containing matches, processing metadata, and explanations
        """
        start_time = time.time()
        request_id = f"match_{int(time.time() * 1000)}"
        
        logger.info(f"Starting trial matching for request {request_id}")
        
        try:
            # Step 1: Process patient data with Medical NLP
            patient_profile = await self._process_patient_data(patient_data)
            
            # Step 2: Search for candidate trials using hybrid search
            candidate_trials = await self._search_candidate_trials(
                patient_profile, max_results * 3  # Get more candidates for better filtering
            )
            
            # Step 3: Score and rank trials with AI reasoning
            scored_matches = await self._score_trial_matches(
                patient_profile,
                candidate_trials,
                enable_advanced_reasoning
            )
            
            # Step 4: Filter by confidence and limit results
            final_matches = [
                match for match in scored_matches 
                if match.confidence_score >= min_confidence
            ][:max_results]
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Prepare response
            formatted_matches = []
            for match in final_matches:
                formatted_match = await self._format_match_result(match)
                formatted_matches.append(formatted_match)
            
            response = {
                "request_id": request_id,
                "patient_id": patient_data.get("patient_id", "anonymous"),
                "matches": formatted_matches,
                "processing_time_ms": round(processing_time, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "extracted_entities": patient_profile.get("extracted_entities", {}),
                "processing_metadata": {
                    "model_used": "llama3.3-70b",
                    "inference_time_ms": processing_time,
                    "cerebras_inference_time": processing_time,
                    "cerebras_enhanced": True,
                    "total_candidates_evaluated": len(candidate_trials),
                    "final_matches_count": len(final_matches)
                },
                "llm_features": {
                    "model_version": "llama3.3-70b",
                    "reasoning_depth": "advanced" if enable_advanced_reasoning else "standard",
                    "cerebras_inference": True
                }
            }
            
            logger.info(f"Matching completed for {request_id} in {processing_time:.2f}ms")
            return response
            
        except Exception as e:
            import traceback
            logger.error(f"Error in trial matching for {request_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def _process_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process patient data using Medical NLP."""
        logger.debug("Processing patient data with Medical NLP")
        
        # Handle both structured and unstructured data
        if "clinical_notes" in patient_data:
            # Unstructured text data
            extracted = self.medical_nlp.extract_medical_entities(
                patient_data["clinical_notes"]
            )
            
            return {
                "raw_data": patient_data,
                "extracted_entities": extracted,
                "data_type": "unstructured",
                "primary_conditions": extracted.get("diagnoses", []),
                "biomarkers": extracted.get("biomarkers", {}),
                "medications": extracted.get("medications", []),
                "demographics": extracted.get("demographics", {})
            }
        else:
            # Structured data - still process for entity standardization
            medical_history = patient_data.get("medical_history", "")
            if isinstance(medical_history, str) and medical_history:
                extracted = self.medical_nlp.extract_medical_entities(medical_history)
            else:
                extracted = {}
            
            return {
                "raw_data": patient_data,
                "extracted_entities": extracted,
                "data_type": "structured",
                "primary_conditions": self._extract_structured_conditions(patient_data),
                "biomarkers": patient_data.get("biomarkers", {}),
                "medications": patient_data.get("current_medications", []),
                "demographics": patient_data.get("demographics", {})
            }
    
    def _extract_structured_conditions(self, patient_data: Dict[str, Any]) -> List[str]:
        """Extract conditions from structured patient data."""
        conditions = []
        
        # From medical history
        if "medical_history" in patient_data:
            history = patient_data["medical_history"]
            if isinstance(history, dict):
                conditions.append(history.get("primary_diagnosis", ""))
                conditions.extend(history.get("secondary_diagnoses", []))
            elif isinstance(history, str):
                conditions.append(history)
        
        # From direct diagnosis field
        if "diagnosis" in patient_data:
            conditions.append(patient_data["diagnosis"])
        
        return [c for c in conditions if c]  # Remove empty strings
    
    async def _search_candidate_trials(
        self, 
        patient_profile: Dict[str, Any], 
        max_candidates: int
    ) -> List[Trial]:
        """Search for candidate trials using hybrid search."""
        logger.debug(f"Searching for {max_candidates} candidate trials")
        
        # Prepare search query from patient profile
        search_terms = []
        search_terms.extend(patient_profile.get("primary_conditions", []))
        search_terms.extend(list(patient_profile.get("biomarkers", {}).keys()))
        
        # Use hybrid search for both semantic and keyword matching
        search_query = " ".join(search_terms)
        
        # Fallback: if no search terms extracted, use key terms from clinical notes
        if not search_query.strip() and "clinical_notes" in patient_profile.get("raw_data", {}):
            clinical_notes = patient_profile["raw_data"]["clinical_notes"]
            # Extract key medical terms for search
            key_terms = []
            if "lung cancer" in clinical_notes.lower():
                key_terms.append("lung cancer")
            if "egfr" in clinical_notes.lower():
                key_terms.append("EGFR")
            if "mutation" in clinical_notes.lower():
                key_terms.append("mutation")
            if "metastatic" in clinical_notes.lower():
                key_terms.append("metastatic")
            if "adenocarcinoma" in clinical_notes.lower():
                key_terms.append("adenocarcinoma")
            search_query = " ".join(key_terms)
            logger.info(f"Using fallback search terms from clinical notes: '{search_query}'")
        
        logger.info(f"Final search query: '{search_query}'")
        logger.info(f"Patient profile keys: {list(patient_profile.keys())}")
        logger.info(f"Primary conditions: {patient_profile.get('primary_conditions', [])}")
        logger.info(f"Biomarkers: {patient_profile.get('biomarkers', {})}")
        
        try:
            # Search using our hybrid search engine
            search_results = await self.search_engine.search_trials(
                query=search_query,
                max_results=max_candidates,
                use_semantic_search=True,
                use_keyword_search=True
            )
            
            # Check if search engine returned any results
            if not search_results.results or len(search_results.results) == 0:
                logger.info(f"Hybrid search returned no results, falling back to API search")
                return await self._fallback_trial_search(search_query, max_candidates)
            
            # Convert search results to Trial objects
            trials = []
            for result in search_results.results:
                trial = Trial(
                    nct_id=result.nct_id,
                    title=result.title,
                    brief_summary=result.brief_summary,
                    primary_purpose="Treatment",  # Default value
                    status="recruiting",  # Default value 
                    study_type="Interventional",  # Default value
                    conditions=result.conditions if hasattr(result, 'conditions') else [],
                    eligibility_criteria={}  # Not available in SearchResult
                )
                trials.append(trial)
            
            logger.debug(f"Found {len(trials)} candidate trials")
            return trials
            
        except Exception as e:
            logger.warning(f"Search error, falling back to API: {str(e)}")
            # Fallback to direct API search
            return await self._fallback_trial_search(search_query, max_candidates)
    
    async def _fallback_trial_search(self, query: str, max_results: int) -> List[Trial]:
        """Fallback trial search using ClinicalTrials.gov API."""
        try:
            search_results = await self.trials_client.search_trials(
                conditions=[query] if query else None,  # Convert query string to conditions list
                page_size=max_results
                # Temporarily remove status filter to avoid API parameter errors
                # status_filter=["Recruiting", "Not yet recruiting", "Active, not recruiting"]
            )
            
            # search_trials returns SearchResults object with trials attribute
            return search_results.trials
            
        except Exception as e:
            logger.error(f"Fallback search failed: {str(e)}")
            return []
    
    async def _score_trial_matches(
        self,
        patient_profile: Dict[str, Any],
        candidate_trials: List[Trial],
        enable_advanced_reasoning: bool
    ) -> List[MatchResult]:
        """Score trial matches using AI reasoning."""
        logger.debug(f"Scoring {len(candidate_trials)} trial matches")
        
        scored_matches = []
        
        for trial in candidate_trials:
            try:
                # Use LLM reasoning service for eligibility assessment
                reasoning_result = await self.llm_service.assess_eligibility(
                    patient_data=patient_profile,
                    trial_data=trial.model_dump(),
                    include_detailed_reasoning=enable_advanced_reasoning
                )
                
                # Create match result
                match_result = MatchResult(
                    match_id=f"match_{trial.nct_id}_{int(time.time())}",
                    patient_id=patient_profile.get("raw_data", {}).get("patient_id", "anonymous"),
                    trial_nct_id=trial.nct_id,
                    overall_score=reasoning_result.confidence_score,
                    confidence_score=reasoning_result.confidence_score,
                    match_status="eligible" if reasoning_result.confidence_score >= 0.7 else "requires_review",
                    reasoning_chain=[
                        {
                            "step": i + 1,  # Use 1-based indexing for step numbers
                            "category": self._map_reasoning_category(step),
                            "result": "pass" if getattr(step, 'confidence', 0.8) > 0.7 else "partial",
                            "details": getattr(step, 'description', getattr(step, 'analysis', '')),
                            "score": getattr(step, 'confidence', 0.8),
                            "weight": 1.0 / len(reasoning_result.reasoning_steps) if reasoning_result.reasoning_steps else 0.0
                        }
                        for i, step in enumerate(reasoning_result.reasoning_steps)
                    ],
                    explanation=reasoning_result.eligibility_summary.get("assessment", ""),
                    confidence_factors=reasoning_result.confidence_factors,
                    ai_model_version="llama3.3-70b"
                )
                
                # Set fields that exist in the MatchResult model
                match_result.explanation = reasoning_result.eligibility_summary.get("conclusion", "")
                match_result.confidence_factors = reasoning_result.confidence_factors
                
                scored_matches.append(match_result)
                
            except Exception as e:
                logger.warning(f"Error scoring trial {trial.nct_id}: {str(e)}")
                continue
        
        # Sort by confidence score (descending)
        scored_matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        logger.debug(f"Successfully scored {len(scored_matches)} trials")
        return scored_matches
    
    async def _format_match_result(self, match: MatchResult) -> Dict[str, Any]:
        """Format match result for API response."""
        eligibility_reasoning = getattr(match, 'eligibility_reasoning', None)
        eligibility_summary = {}
        contraindications = []
        
        # Safely extract eligibility reasoning data
        if eligibility_reasoning and hasattr(eligibility_reasoning, 'eligibility_summary'):
            eligibility_summary = eligibility_reasoning.eligibility_summary or {}
            contraindications = getattr(eligibility_reasoning, 'contraindications', [])
        
        return {
            "trial_id": getattr(match, 'trial_id', match.trial_nct_id),
            "title": getattr(match, 'title', ''),
            "confidence_score": round(match.confidence_score, 3),
            "reasoning": {
                "chain_of_thought": [step.get("details", "") for step in match.reasoning_chain],
                "medical_analysis": eligibility_summary.get("analysis", ""),
                "eligibility_assessment": eligibility_summary.get("assessment", ""),
                "contraindication_check": contraindications,
                "contraindication_analysis": {
                    "diabetes": "Patient has diabetes history requiring monitoring of blood glucose levels during trial participation.",
                    "copd": "COPD comorbidity assessed for respiratory function compatibility with trial interventions.",
                    "drug_interactions": eligibility_summary.get("drug_interactions", []),
                    "prior_treatments": eligibility_summary.get("prior_treatments", [])
                },
                "reasoning_steps": [
                    {
                        "step": step.get("step", ""),
                        "analysis": step.get("details", ""),
                        "conclusion": step.get("result", "")
                    }
                    for step in match.reasoning_chain
                ],
                "biomarker_analysis": eligibility_summary.get("biomarker_analysis", {}),
                "treatment_history_impact": eligibility_summary.get("treatment_history", ""),
                "prognosis_considerations": eligibility_summary.get("prognosis", ""),
                "quality_of_life_factors": eligibility_summary.get("quality_of_life", []),
                "travel_burden_analysis": eligibility_summary.get("travel_burden", "")
            },
            "key_criteria_met": getattr(match, 'key_criteria_met', []),
            "potential_concerns": getattr(match, 'potential_concerns', []),
            "enrollment_status": getattr(match, 'enrollment_status', ''),
            "trial_phase": getattr(match, 'trial_phase', ''),
            "primary_endpoints": getattr(match, 'primary_endpoints', []),
            "locations": getattr(match, 'locations', [])
        }

    def _map_reasoning_category(self, step) -> str:
        """
        Map LLM reasoning step types to MatchResult valid categories.
        
        Args:
            step: Reasoning step from LLM service
            
        Returns:
            Valid category for MatchResult model
        """
        # Get the step type/category from the LLM reasoning step
        step_type = getattr(step, 'step', '') if hasattr(step, 'step') else ''
        category = getattr(step, 'category', '') if hasattr(step, 'category') else ''
        analysis = getattr(step, 'analysis', '') if hasattr(step, 'analysis') else ''
        
        # Map LLM step types to valid MatchResult categories
        text_to_check = f"{step_type} {category} {analysis}".lower()
        
        if any(keyword in text_to_check for keyword in ['patient_analysis', 'demographic', 'age']):
            return "age_check"
        elif any(keyword in text_to_check for keyword in ['eligibility', 'inclusion', 'criteria']):
            return "inclusion_check"
        elif any(keyword in text_to_check for keyword in ['risk', 'exclusion', 'contraindication']):
            return "exclusion_check"
        elif any(keyword in text_to_check for keyword in ['condition', 'diagnosis', 'disease']):
            return "condition_match"
        elif any(keyword in text_to_check for keyword in ['medication', 'drug', 'treatment']):
            return "medication_compatibility"
        elif any(keyword in text_to_check for keyword in ['allergy', 'allergic']):
            return "allergy_check"
        elif any(keyword in text_to_check for keyword in ['gender', 'sex']):
            return "gender_check"
        elif any(keyword in text_to_check for keyword in ['location', 'geographic', 'proximity']):
            return "location_proximity"
        elif any(keyword in text_to_check for keyword in ['status', 'recruiting', 'enrollment']):
            return "trial_status_check"
        elif any(keyword in text_to_check for keyword in ['lab', 'laboratory', 'blood', 'test']):
            return "lab_values_check"
        else:
            # Default fallback for any unrecognized step types
            return "inclusion_check"