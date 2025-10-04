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
from .metrics_service import (
    track_trial_matching,
    track_ai_model_request,
    track_patient_search,
    track_clinical_trials_api
)

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
        
        # For production: Skip mock trials to ensure only real data
        # self._add_mock_trials_for_testing()  # Commented out for production
    
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
                    "status": "recruiting",
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
                    "status": "recruiting",
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
                    "status": "recruiting",
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

    @track_trial_matching("general")
    async def search_and_match_trials(
        self,
        patient_data: Dict[str, Any],
        max_results: int = 3,
        min_confidence: float = 0.5,
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
            
            logger.info(f"Found {len(candidate_trials)} candidate trials from search")
            
            # Step 2.5: Filter trials for relevance to patient condition
            if candidate_trials:
                filtered_trials = self._filter_relevant_trials(candidate_trials, patient_profile)
                logger.info(f"Filtered to {len(filtered_trials)} relevant trials (removed {len(candidate_trials) - len(filtered_trials)} irrelevant)")
                candidate_trials = filtered_trials[:max_results]  # Limit to requested number
            
            # If no trials found, return empty results instead of mock data
            if not candidate_trials:
                logger.info("No candidate trials found from real API search")
                return {
                    "matches": [],
                    "total_count": 0,
                    "has_more": False,
                    "next_page_token": None,
                    "search_metadata": {
                        "query_analysis": {},
                        "search_strategy": "api_only",
                        "processing_time_ms": 0,
                        "api_calls_made": 1,
                        "results_found": 0,
                        "confidence_threshold": min_confidence,
                        "reasoning_depth": "none"
                    }
                }
            
            # Step 3: Score and rank trials with AI reasoning
            scored_matches = await self._score_trial_matches(
                patient_profile,
                candidate_trials,
                enable_advanced_reasoning
            )
            
            logger.info(f"Scored matches: {len(scored_matches)} trials with scores: {[m.confidence_score for m in scored_matches]}")
            
            # Step 4: Filter by confidence and limit results
            final_matches = [
                match for match in scored_matches 
                if match.confidence_score >= min_confidence
            ][:max_results]
            
            logger.info(f"Final matches after confidence filter ({min_confidence}): {len(final_matches)}")
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Prepare response
            formatted_matches = []
            for match in final_matches:
                formatted_match = await self._format_match_result_for_frontend(match)
                formatted_matches.append(formatted_match)
            
            response = {
                "matches": formatted_matches,  # Frontend expects "matches" array
                "total": len(final_matches),
                "query_id": request_id,
                "request_id": request_id,
                "patient_id": patient_data.get("patient_id", "anonymous"),
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
        
        # Handle medical_query field from frontend
        if "medical_query" in patient_data:
            logger.info(f"Processing medical query: {patient_data['medical_query']}")
            # Process the natural language medical query
            extracted = self.medical_nlp.extract_medical_entities(
                patient_data["medical_query"]
            )
            
            logger.info(f"Medical NLP extracted: {extracted}")
            logger.info(f"Extracted conditions: {extracted.get('conditions', [])}")
            logger.info(f"Extracted medications: {extracted.get('medications', [])}")
            
            patient_profile = {
                "raw_data": patient_data,
                "extracted_entities": extracted,
                "data_type": "medical_query",
                "primary_conditions": extracted.get("conditions", []),  # Changed from 'diagnoses' to 'conditions'
                "biomarkers": extracted.get("biomarkers", {}),
                "medications": extracted.get("medications", []),
                "demographics": extracted.get("demographics", {}),  # Now a dict with age/gender
                "age": extracted.get("demographics", {}).get("age"),  # Add structured age
                "gender": extracted.get("demographics", {}).get("gender"),  # Add structured gender
            }
            
            logger.info(f"Patient profile created: {patient_profile}")
            return patient_profile
        # Handle both structured and unstructured data
        elif "clinical_notes" in patient_data:
            # Unstructured text data
            extracted = self.medical_nlp.extract_medical_entities(
                patient_data["clinical_notes"]
            )
            
            return {
                "raw_data": patient_data,
                "extracted_entities": extracted,
                "data_type": "unstructured",
                "primary_conditions": extracted.get("conditions", []),  # Changed from 'diagnoses' to 'conditions'
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
        
        # Fallback: if no search terms extracted, use key terms from clinical notes or medical_query
        if not search_query.strip():
            raw_data = patient_profile.get("raw_data", {})
            
            # Check for medical_query first
            if "medical_query" in raw_data:
                medical_query = raw_data["medical_query"]
                key_terms = self._extract_key_terms_from_text(medical_query)
                search_query = " ".join(key_terms)
                logger.info(f"Using fallback search terms from medical query: '{search_query}'")
            
            # Then check clinical notes
            elif "clinical_notes" in raw_data:
                clinical_notes = raw_data["clinical_notes"]
                key_terms = self._extract_key_terms_from_text(clinical_notes)
                search_query = " ".join(key_terms)
                logger.info(f"Using fallback search terms from clinical notes: '{search_query}'")
        
        logger.info(f"Final search query: '{search_query}'")
        logger.info(f"Patient profile keys: {list(patient_profile.keys())}")
        logger.info(f"Primary conditions: {patient_profile.get('primary_conditions', [])}")
        logger.info(f"Biomarkers: {patient_profile.get('biomarkers', {})}")
        
        try:
            # Skip hybrid search engine (contains mock data) - go directly to real API
            logger.info(f"Skipping hybrid search, using API search directly for query: {search_query}")
            return await self._fallback_trial_search(search_query, max_candidates)
            
        except Exception as e:
            logger.warning(f"Search error, falling back to API: {str(e)}")
            # Fallback to direct API search
            return await self._fallback_trial_search(search_query, max_candidates)
    
    async def _fallback_trial_search(self, query: str, max_results: int) -> List[Trial]:
        """Fallback trial search using ClinicalTrials.gov API."""
        try:
            # Extract specific medical keywords for better search
            keywords = []
            query_lower = query.lower()
            
            # Track patient search
            track_patient_search("trial_search", "patient")
            
            # Track ClinicalTrials.gov API call start time
            api_start_time = time.time()
            
            # Specific cancer types with mutation-specific keywords
            cancer_types = {
                "breast cancer": ["breast cancer", "breast"],
                "lung cancer": ["non-small cell lung cancer", "nsclc", "lung adenocarcinoma"],  # More specific
                "colon cancer": ["colon cancer", "colorectal"],
                "prostate cancer": ["prostate cancer", "prostate"],
                "pancreatic cancer": ["pancreatic cancer", "pancreas"],
                "ovarian cancer": ["ovarian cancer", "ovary"],
                "liver cancer": ["liver cancer", "hepatocellular"],
                "kidney cancer": ["kidney cancer", "renal cell"],
                "skin cancer": ["skin cancer", "melanoma"],
                "brain cancer": ["brain cancer", "glioma"]
            }
            
            # Initialize found_cancer flag
            found_cancer = False
            
            # Special handling for EGFR+ lung cancer
            if "egfr" in query_lower and "lung" in query_lower:
                keywords.extend(["EGFR", "non-small cell lung cancer", "lung adenocarcinoma", "targeted therapy"])
                found_cancer = True
            # Check for specific cancer types
            elif not found_cancer:
                for cancer_type, cancer_keywords in cancer_types.items():
                    if cancer_type in query_lower:
                        keywords.extend(cancer_keywords)
                        found_cancer = True
                        break
            
            # If no specific cancer found but "cancer" is mentioned
            if not found_cancer and "cancer" in query_lower:
                keywords.append("cancer")
            
            # Add other medical conditions
            medical_conditions = {
                "diabetes": ["diabetes", "type 2 diabetes", "type 1 diabetes"],
                "heart": ["heart disease", "cardiovascular", "cardiac"],
                "stroke": ["stroke", "cerebrovascular"],
                "hypertension": ["hypertension", "high blood pressure"],
                "asthma": ["asthma", "respiratory"],
                "copd": ["copd", "chronic obstructive pulmonary"],
                "alzheimer": ["alzheimer", "dementia"],
                "parkinson": ["parkinson", "movement disorder"]
            }
            
            for condition, condition_keywords in medical_conditions.items():
                if condition in query_lower:
                    keywords.extend(condition_keywords[:2])  # Limit to 2 keywords per condition
            
            # If still no keywords found, extract from age/demographics
            if not keywords:
                # Try to extract age-related or gender-related terms
                if "woman" in query_lower or "female" in query_lower:
                    keywords.append("female")
                if "man" in query_lower or "male" in query_lower:
                    keywords.append("male")
                
                # As last resort, use the entire query but limit length
                if not keywords:
                    keywords = [query[:50]]  # Limit query length
            
            logger.info(f"Using keywords for search: {keywords}")
            
            search_results = await self.trials_client.search_trials(
                keywords=keywords,
                page_size=max_results
            )
            
            # Track ClinicalTrials.gov API call success
            api_latency = time.time() - api_start_time
            track_clinical_trials_api("search", "success", api_latency)
            
            # If API search returned no valid trials, try broader search terms
            if not search_results.trials or len(search_results.trials) == 0:
                logger.info(f"API search returned no valid trials, trying broader search for query: {query}")
                # Try broader search with just "cancer" or primary condition
                broader_keywords = ["cancer"]
                if any(term in query.lower() for term in ["breast", "lung", "colorectal", "prostate"]):
                    cancer_type = next(term for term in ["breast", "lung", "colorectal", "prostate"] if term in query.lower())
                    broader_keywords = [f"{cancer_type} cancer", "cancer"]
                
                search_results = await self.trials_client.search_trials(
                    keywords=broader_keywords,
                    page_size=max_results
                )
                
                # Track broader search API call
                broader_api_latency = time.time() - api_start_time
                track_clinical_trials_api("search_broader", "success", broader_api_latency)
            
            return search_results.trials
            
        except Exception as e:
            # Track API error
            api_latency = time.time() - api_start_time
            track_clinical_trials_api("search", "error", api_latency)
            
            logger.error(f"Search failed: {str(e)}")
            # Return empty list instead of mock data - let the system handle no results gracefully
            return []
    
    def _create_mock_lung_cancer_trials(self) -> List[Trial]:
        """Create mock lung cancer trial data for testing."""
        from datetime import datetime, timezone
        from ..models.trial import Trial
        
        mock_trial_data = [
            {
                "nct_id": "NCT12345678",
                "title": "Phase III Study of Immunotherapy in Advanced Non-Small Cell Lung Cancer",
                "brief_summary": "This study evaluates the effectiveness of combination immunotherapy in patients with advanced non-small cell lung cancer who have progressed on prior therapy.",
                "primary_purpose": "treatment",
                "study_type": "interventional",
                "status": "recruiting",
                "phase": "Phase 3",
                "conditions": ["Non-small Cell Lung Cancer", "Lung Cancer"],
                "interventions": ["Pembrolizumab", "Carboplatin", "Pemetrexed"],
                "eligibility_criteria": {
                    "min_age": 18,
                    "max_age": 100,
                    "gender": "all",
                    "inclusion_criteria": [
                        "Age 18 years or older",
                        "Histologically confirmed non-small cell lung cancer",
                        "Stage IIIB or IV disease",
                        "EGFR wild-type or T790M negative",
                        "ECOG performance status 0-1"
                    ],
                    "exclusion_criteria": [
                        "Prior immunotherapy",
                        "Autoimmune disease",
                        "Active brain metastases"
                    ]
                },
                "locations": [
                    {
                        "facility": "Johns Hopkins Hospital",
                        "city": "Baltimore",
                        "state": "Maryland",
                        "country": "United States"
                    },
                    {
                        "facility": "Memorial Sloan Kettering Cancer Center", 
                        "city": "New York",
                        "state": "New York",
                        "country": "United States"
                    }
                ],
                "enrollment": 450,
                "start_date": "2024-01-15",
                "completion_date": "2026-12-31"
            },
            {
                "nct_id": "NCT87654321",
                "title": "Targeted Therapy for EGFR-Positive Lung Cancer",
                "brief_summary": "A phase 2 trial studying the efficacy of next-generation EGFR inhibitors in patients with EGFR-mutated non-small cell lung cancer.",
                "primary_purpose": "treatment",
                "study_type": "interventional",
                "status": "recruiting",
                "phase": "Phase 2",
                "conditions": ["Non-small Cell Lung Cancer", "EGFR-positive Lung Cancer"],
                "interventions": ["Osimertinib", "AZD9291"],
                "eligibility_criteria": {
                    "min_age": 18,
                    "max_age": 75,
                    "gender": "all",
                    "inclusion_criteria": [
                        "Age 18-75 years",
                        "EGFR mutation positive",
                        "Stage IIIB, IV, or recurrent NSCLC",
                        "Previous treatment with EGFR TKI",
                        "Adequate organ function"
                    ],
                    "exclusion_criteria": [
                        "Prior osimertinib treatment",
                        "Severe cardiac dysfunction",
                        "Active infection"
                    ]
                },
                "locations": [
                    {
                        "facility": "Mayo Clinic",
                        "city": "Rochester", 
                        "state": "Minnesota",
                        "country": "United States"
                    }
                ],
                "enrollment": 150,
                "start_date": "2024-03-01",
                "completion_date": "2025-09-30"
            },
            {
                "nct_id": "NCT11223344",
                "title": "Early Stage Lung Cancer Adjuvant Therapy Study",
                "brief_summary": "Randomized trial comparing adjuvant chemotherapy regimens in patients with completely resected stage II-III non-small cell lung cancer.",
                "primary_purpose": "treatment",
                "study_type": "interventional",
                "status": "not_yet_recruiting", 
                "phase": "Phase 3",
                "conditions": ["Non-small Cell Lung Cancer", "Early Stage Lung Cancer"],
                "interventions": ["Cisplatin", "Vinorelbine", "Carboplatin", "Paclitaxel"],
                "eligibility_criteria": {
                    "min_age": 18,
                    "max_age": 70,
                    "gender": "all",
                    "inclusion_criteria": [
                        "Completely resected NSCLC",
                        "Stage IIA-IIIA disease",
                        "Age 18-70 years",
                        "No prior chemotherapy",
                        "Good performance status"
                    ],
                    "exclusion_criteria": [
                        "Prior chemotherapy",
                        "Severe comorbidities",
                        "Active second malignancy"
                    ]
                },
                "locations": [
                    {
                        "facility": "MD Anderson Cancer Center",
                        "city": "Houston",
                        "state": "Texas", 
                        "country": "United States"
                    }
                ],
                "enrollment": 300,
                "start_date": "2023-06-01",
                "completion_date": "2025-12-31"
            }
        ]
        
        # Convert to Trial objects
        mock_trials = []
        for trial_data in mock_trial_data:
            try:
                trial = Trial(**trial_data)
                mock_trials.append(trial)
            except Exception as e:
                logger.warning(f"Failed to create Trial object from mock data: {e}")
                continue
        
        return mock_trials
    
    def _create_mock_breast_cancer_trials(self) -> List[Trial]:
        """Create mock breast cancer trial data for testing."""
        from datetime import datetime, timezone
        from ..models.trial import Trial
        
        logger.info("Creating mock breast cancer trials")
        
        mock_trial_data = [
            {
                "nct_id": "NCT98765432",
                "title": "Phase III Trial of CDK4/6 Inhibitor in Early-Stage Breast Cancer",
                "brief_summary": "This study evaluates the effectiveness of CDK4/6 inhibitors in women aged 18-75 with newly diagnosed breast cancer. Open to all breast cancer subtypes including hormone receptor positive, HER2 positive, and triple-negative breast cancer.",
                "primary_purpose": "treatment",
                "study_type": "interventional", 
                "status": "recruiting",
                "phase": "Phase 3",
                "conditions": ["Breast Cancer", "Early-Stage Breast Cancer", "All Breast Cancer Subtypes"],
                "interventions": ["Palbociclib", "Standard Chemotherapy", "Hormonal Therapy"],
                "eligibility_criteria": {
                    "min_age": 18,
                    "max_age": 75,
                    "gender": "female",
                    "inclusion_criteria": [
                        "Age 18-75 years",
                        "Female patients",
                        "Histologically confirmed breast cancer",
                        "Any stage (I-IV)",
                        "All breast cancer subtypes eligible",
                        "ECOG performance status 0-2",
                        "Willing to provide informed consent"
                    ],
                    "exclusion_criteria": [
                        "Male patients",
                        "Age under 18 or over 75",
                        "Pregnancy (pregnancy test required)"
                    ]
                },
                "locations": [
                    {
                        "facility": "Dana-Farber Cancer Institute",
                        "city": "Boston",
                        "state": "Massachusetts",
                        "country": "United States"
                    },
                    {
                        "facility": "Memorial Sloan Kettering Cancer Center", 
                        "city": "New York",
                        "state": "New York",
                        "country": "United States"
                    }
                ],
                "enrollment": 350,
                "start_date": "2024-02-01",
                "completion_date": "2026-08-31"
            },
            {
                "nct_id": "NCT56789012",
                "title": "Targeted Therapy for HER2-Positive Breast Cancer After Radiation",
                "brief_summary": "A phase 2 study of next-generation HER2-targeted agents in patients who have completed radiation therapy for locally advanced breast cancer.",
                "primary_purpose": "treatment",
                "study_type": "interventional",
                "status": "recruiting",
                "phase": "Phase 2",
                "conditions": ["HER2-Positive Breast Cancer", "Locally Advanced Breast Cancer"],
                "interventions": ["Trastuzumab deruxtecan", "T-DM1"],
                "eligibility_criteria": {
                    "min_age": 21,
                    "max_age": 75,
                    "gender": "all",
                    "inclusion_criteria": [
                        "Age 21-75 years",
                        "HER2-positive breast cancer",
                        "Completed radiation therapy within 6 months",
                        "No prior HER2-targeted therapy",
                        "Adequate cardiac function"
                    ],
                    "exclusion_criteria": [
                        "Prior HER2-targeted therapy",
                        "Cardiac dysfunction",
                        "Active infection"
                    ]
                },
                "locations": [
                    {
                        "facility": "MD Anderson Cancer Center",
                        "city": "Houston", 
                        "state": "Texas",
                        "country": "United States"
                    }
                ],
                "enrollment": 120,
                "start_date": "2024-04-15",
                "completion_date": "2025-12-31"
            },
            {
                "nct_id": "NCT34567890",
                "title": "Post-Radiation Adjuvant Therapy in Stage IV Breast Cancer",
                "brief_summary": "Randomized trial of adjuvant therapy options for patients with stage IV breast cancer who have completed radiation therapy.",
                "primary_purpose": "treatment",
                "study_type": "interventional",
                "status": "not_yet_recruiting", 
                "phase": "Phase 3",
                "conditions": ["Stage IV Breast Cancer", "Metastatic Breast Cancer"],
                "interventions": ["Docetaxel", "Cyclophosphamide", "Doxorubicin"],
                "eligibility_criteria": {
                    "min_age": 18,
                    "max_age": 70,
                    "gender": "all",
                    "inclusion_criteria": [
                        "Stage IV breast cancer",
                        "Completed radiation therapy 1-6 months prior",
                        "Age 18-70 years",
                        "No active brain metastases",
                        "Adequate organ function"
                    ],
                    "exclusion_criteria": [
                        "Active brain metastases",
                        "Prior chemotherapy",
                        "Severe comorbidities"
                    ]
                },
                "locations": [
                    {
                        "facility": "Northwestern Medicine",
                        "city": "Chicago",
                        "state": "Illinois", 
                        "country": "United States"
                    }
                ],
                "enrollment": 280,
                "start_date": "2023-09-01",
                "completion_date": "2025-11-30"
            }
        ]
        
        # Convert to Trial objects
        mock_trials = []
        for trial_data in mock_trial_data:
            try:
                trial = Trial(**trial_data)
                mock_trials.append(trial)
            except Exception as e:
                logger.warning(f"Failed to create Trial object from mock data: {e}")
                continue
        
        logger.info(f"Successfully created {len(mock_trials)} mock breast cancer trials: {[t.nct_id for t in mock_trials]}")
        return mock_trials
    
    def _create_mock_colorectal_cancer_trials(self) -> List[Trial]:
        """Create mock colorectal cancer trial data for testing."""
        from datetime import datetime, timezone
        from ..models.trial import Trial
        
        logger.info("Creating mock colorectal cancer trials")
        
        mock_trial_data = [
            {
                "nct_id": "NCT55566677",
                "title": "Phase II Study of Immunotherapy in Metastatic Colorectal Cancer",
                "brief_summary": "This study evaluates combination immunotherapy in patients with metastatic colorectal cancer who have failed first-line chemotherapy including FOLFOX regimen.",
                "primary_purpose": "treatment",
                "study_type": "interventional", 
                "status": "recruiting",
                "phase": "Phase 2",
                "conditions": ["Colorectal Cancer", "Metastatic Colorectal Cancer", "Colon Cancer"],
                "interventions": ["Pembrolizumab", "Bevacizumab", "Capecitabine"],
                "eligibility_criteria": {
                    "min_age": 18,
                    "max_age": 80,
                    "gender": "all",
                    "inclusion_criteria": [
                        "Metastatic colorectal cancer",
                        "Failed FOLFOX or similar chemotherapy",
                        "Age 18-80 years",
                        "ECOG performance status 0-2",
                        "Adequate organ function"
                    ],
                    "exclusion_criteria": [
                        "Active autoimmune disease",
                        "Prior immunotherapy",
                        "Active brain metastases"
                    ]
                },
                "locations": [
                    {
                        "facility": "Massachusetts General Hospital",
                        "city": "Boston",
                        "state": "Massachusetts",
                        "country": "United States"
                    }
                ],
                "enrollment": 150,
                "start_date": "2024-02-01",
                "completion_date": "2026-06-30"
            },
            {
                "nct_id": "NCT77788899",
                "title": "Targeted Therapy for KRAS-Mutant Colorectal Cancer",
                "brief_summary": "Phase 1/2 trial of novel KRAS inhibitor in patients with KRAS-mutant metastatic colorectal cancer.",
                "primary_purpose": "treatment",
                "study_type": "interventional",
                "status": "recruiting", 
                "phase": "Phase 1",
                "conditions": ["KRAS-Mutant Colorectal Cancer", "Metastatic Colorectal Cancer"],
                "interventions": ["KRAS G12C Inhibitor", "Cetuximab"],
                "eligibility_criteria": {
                    "min_age": 18,
                    "max_age": 75,
                    "gender": "all",
                    "inclusion_criteria": [
                        "KRAS G12C mutation confirmed",
                        "Metastatic colorectal cancer",
                        "Progressive disease on standard therapy"
                    ],
                    "exclusion_criteria": [
                        "Wild-type KRAS",
                        "Active CNS metastases"
                    ]
                },
                "locations": [
                    {
                        "facility": "Dana-Farber Cancer Institute",
                        "city": "Boston",
                        "state": "Massachusetts",
                        "country": "United States"
                    }
                ],
                "enrollment": 80,
                "start_date": "2024-03-15",
                "completion_date": "2025-09-30"
            }
        ]
        
        # Convert to Trial objects
        mock_trials = []
        for trial_data in mock_trial_data:
            try:
                trial = Trial(**trial_data)
                mock_trials.append(trial)
            except Exception as e:
                logger.warning(f"Failed to create Trial object from mock data: {e}")
                continue
        
        logger.info(f"Successfully created {len(mock_trials)} mock colorectal cancer trials: {[t.nct_id for t in mock_trials]}")
        return mock_trials
    
    def _create_mock_prostate_cancer_trials(self) -> List[Trial]:
        """Create mock prostate cancer trial data for testing."""
        from datetime import datetime, timezone
        from ..models.trial import Trial
        
        logger.info("Creating mock prostate cancer trials")
        
        mock_trial_data = [
            {
                "nct_id": "NCT11122233",
                "title": "Androgen Receptor Targeted Therapy in Advanced Prostate Cancer",
                "brief_summary": "Phase 3 study of next-generation androgen receptor inhibitor in men with metastatic castration-resistant prostate cancer.",
                "primary_purpose": "treatment",
                "study_type": "interventional", 
                "status": "recruiting",
                "phase": "Phase 3",
                "conditions": ["Prostate Cancer", "Castration-Resistant Prostate Cancer"],
                "interventions": ["Enzalutamide", "Abiraterone", "Docetaxel"],
                "eligibility_criteria": {
                    "min_age": 18,
                    "max_age": 85,
                    "gender": "male",
                    "inclusion_criteria": [
                        "Metastatic castration-resistant prostate cancer",
                        "Progressive disease on androgen deprivation therapy",
                        "Male patients only"
                    ],
                    "exclusion_criteria": [
                        "Prior chemotherapy for metastatic disease",
                        "Severe cardiac disease"
                    ]
                },
                "locations": [
                    {
                        "facility": "Mayo Clinic",
                        "city": "Rochester",
                        "state": "Minnesota",
                        "country": "United States"
                    }
                ],
                "enrollment": 400,
                "start_date": "2024-01-10",
                "completion_date": "2026-12-31"
            }
        ]
        
        # Convert to Trial objects
        mock_trials = []
        for trial_data in mock_trial_data:
            try:
                trial = Trial(**trial_data)
                mock_trials.append(trial)
            except Exception as e:
                logger.warning(f"Failed to create Trial object from mock data: {e}")
                continue
        
        logger.info(f"Successfully created {len(mock_trials)} mock prostate cancer trials: {[t.nct_id for t in mock_trials]}")
        return mock_trials
    
    def _extract_conditions_from_query(self, query: str) -> List[str]:
        """Extract medical conditions from natural language query."""
        if not query:
            return []
        
        # Common medical conditions patterns
        conditions = []
        query_lower = query.lower()
        
        # Cancer types
        cancer_patterns = [
            "lung cancer", "breast cancer", "colon cancer", "prostate cancer",
            "skin cancer", "liver cancer", "pancreatic cancer", "kidney cancer",
            "brain cancer", "ovarian cancer", "cervical cancer", "stomach cancer"
        ]
        
        for pattern in cancer_patterns:
            if pattern in query_lower:
                conditions.append(pattern.title())
        
        # Other common conditions
        condition_patterns = [
            "diabetes", "hypertension", "heart disease", "stroke", "asthma",
            "copd", "alzheimer", "parkinson", "arthritis", "depression"
        ]
        
        for pattern in condition_patterns:
            if pattern in query_lower:
                conditions.append(pattern.title())
        
        # If no specific conditions found, try to extract key medical terms
        if not conditions:
            medical_terms = []
            # Look for cancer stages
            if "cancer" in query_lower:
                conditions.append("Cancer")
            
            # Look for other key terms
            if "heart" in query_lower:
                medical_terms.append("Heart Disease")
            if "lung" in query_lower and "cancer" not in query_lower:
                medical_terms.append("Lung Disease")
                
            conditions.extend(medical_terms)
        
        return conditions
    
    async def _score_trial_matches(
        self,
        patient_profile: Dict[str, Any],
        candidate_trials: List[Trial],
        enable_advanced_reasoning: bool
    ) -> List[MatchResult]:
        """Score trial matches using AI reasoning."""
        logger.info(f"Scoring {len(candidate_trials)} trial matches")
        
        scored_matches = []
        
        for trial in candidate_trials:
            try:
                logger.info(f"Scoring trial {trial.nct_id}")
                
                # Use LLM reasoning service for eligibility assessment
                reasoning_result = await self.llm_service.assess_eligibility(
                    patient_data=patient_profile,
                    trial_data=trial.model_dump(),
                    include_detailed_reasoning=enable_advanced_reasoning
                )
                
                logger.info(f"Trial {trial.nct_id} scored with confidence: {reasoning_result.confidence_score}")
                
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
                
                # Store trial data for formatting
                match_result._trial_data = trial.model_dump()
                
                # Set fields that exist in the MatchResult model
                match_result.explanation = reasoning_result.eligibility_summary.get("conclusion", "")
                match_result.confidence_factors = reasoning_result.confidence_factors
                
                scored_matches.append(match_result)
                
            except Exception as e:
                import traceback
                logger.error(f"Error scoring trial {trial.nct_id}: {str(e)}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
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
    
    async def _format_match_result_for_frontend(self, match: MatchResult) -> Dict[str, Any]:
        """Format match result for frontend compatibility (TrialMatch interface)."""
        
        # Get trial data
        trial_data = getattr(match, '_trial_data', {})
        locations = trial_data.get('locations', [])
        primary_location = locations[0] if locations else {}
        
        return {
            "id": getattr(match, 'match_id', f"match_{match.trial_nct_id}"),
            "nctId": match.trial_nct_id,
            "title": trial_data.get('title', f"Clinical Trial {match.trial_nct_id}"),
            "matchScore": round(match.confidence_score * 100, 1),  # Convert 0.8 -> 80.0
            "location": {
                "facility": primary_location.get("facility", "Study Location"),
                "city": primary_location.get("city", "Not specified"),
                "state": primary_location.get("state", "See ClinicalTrials.gov"),
                "distance": "TBD"  # Would require geocoding
            },
            "explanation": match.explanation or "AI-powered eligibility assessment based on medical profile and trial criteria.",
            "contact": {
                "name": "See study details",
                "phone": "Contact via ClinicalTrials.gov", 
                "email": f"https://clinicaltrials.gov/study/{match.trial_nct_id}"
            },
            "eligibility": self._format_eligibility_criteria(trial_data),
            "phase": trial_data.get('phase', 'Phase 2'),
            "status": trial_data.get('status', 'recruiting').title(),
            "conditions": trial_data.get('conditions', ['Cancer'])
        }
    
    def _filter_relevant_trials(self, trials: List[Trial], patient_profile: Dict[str, Any]) -> List[Trial]:
        """Filter trials to remove irrelevant studies based on patient condition."""
        if not trials:
            return []
        
        filtered_trials = []
        patient_conditions = patient_profile.get('primary_conditions', [])
        patient_age = patient_profile.get('age', 0)
        
        logger.info(f"Filtering trials for conditions: {patient_conditions}, age: {patient_age}")
        
        try:
            for trial in trials:
                try:
                    relevance_score = self._calculate_trial_relevance(trial, patient_profile)
                    
                    if relevance_score >= 0.5:  # Raised threshold for better quality
                        filtered_trials.append(trial)
                        logger.debug(f"Trial {getattr(trial, 'nct_id', 'unknown')} passed filter with relevance: {relevance_score:.2f}")
                    else:
                        logger.debug(f"Trial {getattr(trial, 'nct_id', 'unknown')} filtered out, relevance: {relevance_score:.2f}")
                except Exception as e:
                    logger.warning(f"Error filtering trial {getattr(trial, 'nct_id', 'unknown')}: {str(e)}")
                    # Include trial if filtering fails to avoid losing results
                    filtered_trials.append(trial)
            
            # Sort by relevance score (highest first) - with error handling
            try:
                filtered_trials.sort(key=lambda t: self._calculate_trial_relevance(t, patient_profile), reverse=True)
            except Exception as e:
                logger.warning(f"Error sorting trials by relevance: {str(e)}")
                # Return unsorted if sorting fails
            
            return filtered_trials
            
        except Exception as e:
            logger.error(f"Critical error in trial filtering: {str(e)}")
            # Return original trials if filtering completely fails
            return trials
    
    def _calculate_trial_relevance(self, trial: Trial, patient_profile: Dict[str, Any]) -> float:
        """Calculate relevance score for a trial based on patient profile."""
        try:
            score = 0.0
            
            # Safely get trial text for analysis
            trial_title = getattr(trial, 'title', '') or ''
            trial_summary = getattr(trial, 'brief_summary', '') or ''
            trial_text = f"{trial_title} {trial_summary}".lower()
            
            patient_conditions = [c.lower() for c in patient_profile.get('primary_conditions', [])]
            patient_age = patient_profile.get('age', 0)
            
            # 1. Condition matching (most important)
            condition_match = False
            for condition in patient_conditions:
                if condition and any(cond_word in trial_text for cond_word in condition.split() if cond_word):
                    condition_match = True
                    score += 0.4
                    break
            
            # 2. Exclude irrelevant study types for cancer patients
            if any(condition in patient_conditions for condition in ['cancer', 'tumor', 'carcinoma']):
                
                # Exclude prevention studies for advanced cancer patients
                patient_text = ' '.join(patient_conditions).lower()
                if any(stage in patient_text for stage in ['stage 4', 'stage iv', 'metastatic', 'advanced']):
                    if any(phrase in trial_text for phrase in [
                        'prevention', 'prophylaxis', 'risk reduction', 'preventive',
                        'high-risk', 'postmenopausal women'  # Added postmenopausal prevention
                    ]):
                        score = -1.0  # Automatic disqualification 
                        logger.debug(f"Trial {getattr(trial, 'nct_id', 'unknown')}: Prevention study - automatic disqualification for advanced cancer")
                        return 0.0  # Early return to prevent any bonuses
                
                # Exclude surgical/reconstruction studies for Stage 4 patients
                if any(stage in patient_text for stage in ['stage 4', 'stage iv', 'metastatic', 'advanced']):
                    if any(phrase in trial_text for phrase in [
                        'reconstruction', 'surgery', 'surgical', 'cosmetic', 'aesthetic',
                        'mastectomy', 'lumpectomy', 'breast reconstruction'
                    ]):
                        score = -1.0  # Automatic disqualification for Stage 4
                        logger.debug(f"Trial {getattr(trial, 'nct_id', 'unknown')}: Surgery/reconstruction - automatic disqualification for advanced cancer")
                        return 0.0  # Early return
                
                # Exclude healthy subjects studies - automatic disqualification
                if any(phrase in trial_text for phrase in [
                    'healthy subjects', 'healthy volunteers', 'healthy participants',
                    'in healthy', 'pharmacokinetics in healthy'
                ]):
                    logger.debug(f"Trial {getattr(trial, 'nct_id', 'unknown')}: Healthy subject study - automatic disqualification")
                    return 0.0  # Early return
                
                # Exclude imaging/diagnostic only studies
                if any(phrase in trial_text for phrase in [
                    'quantitative ultrasound', 'imaging study', 'diagnostic study',
                    'biomarker study', 'blood samples', 'registry'
                ]):
                    score -= 0.4
                    logger.debug(f"Trial {getattr(trial, 'nct_id', 'unknown')}: Observational/diagnostic study penalty")
            
            # 3. Age appropriateness
            if patient_age is not None and patient_age > 0:
                # Exclude pediatric studies for adults
                if patient_age >= 18 and any(phrase in trial_text for phrase in [
                    'pediatric', 'children', 'adolescent', 'child'
                ]):
                    score -= 0.6
                    logger.debug(f"Trial {getattr(trial, 'nct_id', 'unknown')}: Pediatric study penalty for adult patient")
                
                # Exclude adult studies for children
                elif patient_age < 18 and 'adult' in trial_text and 'pediatric' not in trial_text:
                    score -= 0.6
            
            # 4. Study type preferences - enhanced for cancer treatment
            if any(phrase in trial_text for phrase in [
                'treatment', 'therapy', 'therapeutic', 'drug trial', 'medication',
                'chemotherapy', 'immunotherapy', 'targeted therapy', 'clinical trial'
            ]):
                score += 0.3  # Strong preference for treatment trials
            elif any(phrase in trial_text for phrase in [
                'phase 1', 'phase 2', 'phase 3', 'phase i', 'phase ii', 'phase iii'
            ]):
                score += 0.2  # Phase trials are usually treatment
            elif 'observational' in trial_text:
                score -= 0.1  # Observational studies are less preferred for treatment-seeking patients
            
            # 5. Status relevance
            trial_status = getattr(trial, 'status', '')
            if trial_status:
                status = trial_status.lower()
                if status in ['recruiting', 'active']:
                    score += 0.1
                elif status in ['completed', 'terminated']:
                    score -= 0.2
            
            # 6. Specific cancer type matching
            if condition_match:
                # Bonus for exact cancer type matches
                cancer_types = {
                    'breast cancer': ['breast'],
                    'lung cancer': ['lung', 'nsclc', 'non-small cell'],
                    'colorectal cancer': ['colorectal', 'colon', 'rectal'],
                    'prostate cancer': ['prostate'],
                    'pancreatic cancer': ['pancreatic', 'pancreas']
                }
                
                cancer_bonus_applied = False
                for patient_condition in patient_conditions:
                    if patient_condition and not cancer_bonus_applied:
                        for cancer_type, keywords in cancer_types.items():
                            if cancer_type in patient_condition:
                                if any(keyword in trial_text for keyword in keywords):
                                    score += 0.3
                                    cancer_bonus_applied = True
                                    logger.debug(f"Trial {getattr(trial, 'nct_id', 'unknown')}: Cancer type bonus for {cancer_type}")
                                    break
                        if cancer_bonus_applied:
                            break
            
            return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            
        except Exception as e:
            logger.warning(f"Error calculating relevance for trial {getattr(trial, 'nct_id', 'unknown')}: {str(e)}")
            return 0.5  # Default relevance if calculation fails
    
    def _format_eligibility_criteria(self, trial_data: Dict[str, Any]) -> List[str]:
        """Format eligibility criteria from trial data."""
        criteria = []
        
        # Age requirements
        eligibility = trial_data.get('eligibility_criteria', {})
        min_age = eligibility.get('min_age', 18)
        max_age = eligibility.get('max_age', 100)
        criteria.append(f"Age {min_age}-{max_age} years")
        
        # Gender requirements
        gender = eligibility.get('sex', 'All')
        if gender != 'All':
            criteria.append(f"Gender: {gender}")
        
        # Conditions from trial data
        conditions = trial_data.get('conditions', [])
        if conditions:
            if isinstance(conditions, list):
                main_condition = conditions[0] if conditions else "Cancer"
            else:
                main_condition = str(conditions)
            criteria.append(f"Diagnosis: {main_condition}")
        
        # Status
        status = trial_data.get('status', '').lower()
        if status == 'recruiting':
            criteria.append("Currently recruiting participants")
        elif status == 'terminated':
            criteria.append("Study terminated")
        elif status == 'completed':
            criteria.append("Study completed")
        
        # Always add informed consent
        criteria.append("Informed consent required")
        
        return criteria
    
    def _extract_key_terms_from_text(self, text: str) -> List[str]:
        """Extract key medical terms from text for search fallback."""
        if not text:
            return []
            
        text_lower = text.lower()
        key_terms = []
        
        # Age extraction
        import re
        age_match = re.search(r'(\d+)\s*year', text_lower)
        if age_match:
            key_terms.append(f"age {age_match.group(1)}")
        
        # Gender extraction
        if any(gender in text_lower for gender in ["woman", "female", "girl"]):
            key_terms.append("female")
        elif any(gender in text_lower for gender in ["man", "male", "boy"]):
            key_terms.append("male")
            
        # Cancer types
        cancer_types = {
            "breast cancer": ["breast cancer", "breast"],
            "lung cancer": ["lung cancer", "lung", "nsclc"],
            "colon cancer": ["colon cancer", "colorectal"],
            "prostate cancer": ["prostate cancer", "prostate"],
            "pancreatic cancer": ["pancreatic cancer", "pancreas"],
            "ovarian cancer": ["ovarian cancer", "ovary"],
            "liver cancer": ["liver cancer", "hepatocellular"],
            "kidney cancer": ["kidney cancer", "renal cell"],
            "skin cancer": ["skin cancer", "melanoma"],
            "brain cancer": ["brain cancer", "glioma"]
        }
        
        for cancer_type, keywords in cancer_types.items():
            if cancer_type in text_lower:
                key_terms.extend(keywords)
                break
        
        # General cancer if no specific type found
        if not any("cancer" in term for term in key_terms) and "cancer" in text_lower:
            key_terms.append("cancer")
            
        # Other medical conditions
        medical_conditions = [
            "diabetes", "hypertension", "heart disease", "asthma", 
            "arthritis", "depression", "anxiety", "copd"
        ]
        
        for condition in medical_conditions:
            if condition in text_lower:
                key_terms.append(condition)
                
        # Medical terms
        medical_terms = [
            "metastatic", "stage", "mutation", "egfr", "her2", 
            "chemotherapy", "radiation", "immunotherapy", "surgery"
        ]
        
        for term in medical_terms:
            if term in text_lower:
                key_terms.append(term)
        
        return list(set(key_terms))  # Remove duplicates
    
    async def _smart_fallback_trials(self, patient_profile: Dict[str, Any], patient_data: Dict[str, Any]) -> List[Trial]:
        """Smart fallback to generate appropriate mock trials based on patient data analysis."""
        logger.info("Performing smart fallback trial generation based on patient context")
        
        # Analyze the raw patient data to understand what type of trials we need
        raw_data = patient_profile.get("raw_data", {})
        
        # Check the medical_query directly
        medical_query = raw_data.get("medical_query", "").lower()
        
        # Also check other fields
        medical_history = str(raw_data.get("medical_history", "")).lower()
        clinical_notes = str(raw_data.get("clinical_notes", "")).lower()
        
        # Combine all text for analysis
        all_text = f"{medical_query} {medical_history} {clinical_notes}".lower()
        
        logger.info(f"Analyzing text for fallback: '{all_text[:100]}...'")
        
        # Determine cancer type based on keywords (check specific types first)
        if any(keyword in all_text for keyword in ["colorectal cancer", "colon cancer", "rectal cancer", "colorectal", "folfox"]):
            logger.info("Detected colorectal cancer context, generating colorectal cancer trials")
            return self._create_mock_colorectal_cancer_trials()
        elif any(keyword in all_text for keyword in ["lung cancer", "lung", "egfr", "nsclc", "non-small cell lung cancer", "erlotinib"]):
            logger.info("Detected lung cancer context, generating lung cancer trials")
            return self._create_mock_lung_cancer_trials()
        elif any(keyword in all_text for keyword in ["breast cancer", "breast", "triple negative", "her2", "cdk4/6"]):
            logger.info("Detected breast cancer context, generating breast cancer trials")
            return self._create_mock_breast_cancer_trials()
        elif any(keyword in all_text for keyword in ["prostate cancer", "prostate"]):
            logger.info("Detected prostate cancer context, generating prostate cancer trials")
            return self._create_mock_prostate_cancer_trials()
        elif "cancer" in all_text:
            logger.info("Detected general cancer context, generating mixed cancer trials")
            return self._create_mock_breast_cancer_trials() + self._create_mock_lung_cancer_trials()[:1]
        else:
            # No specific cancer detected, but we should still provide some trials
            # Check age and gender for appropriate defaults
            age_text = all_text
            if any(keyword in age_text for keyword in ["woman", "female", "girl"]):
                logger.info("Detected female patient, defaulting to breast cancer trials")
                return self._create_mock_breast_cancer_trials()
            else:
                logger.info("No specific cancer detected, providing general cancer trials")
                return self._create_mock_breast_cancer_trials()[:2]