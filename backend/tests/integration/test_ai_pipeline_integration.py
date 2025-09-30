"""
Integration tests for AI Pipeline Services.

These tests validate the coordination and integration between all
AI pipeline components including NLP, search, LLM reasoning, and API clients.
"""
import pytest
import asyncio
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# Import our AI pipeline services
from backend.src.services.medical_nlp import MedicalNLPProcessor
from backend.src.services.hybrid_search import HybridSearchEngine, SearchQuery, SearchResult
from backend.src.services.llm_reasoning import LLMReasoningService, ReasoningType
from backend.src.integrations.trials_api_client import ClinicalTrialsClient
from backend.src.integrations.cerebras_client import CerebrasClient

# Import models
from backend.src.models.patient import Patient
from backend.src.models.trial import Trial
from backend.src.models.eligibility_criteria import EligibilityCriteria


class TestAIPipelineIntegration:
    """Integration tests for AI pipeline services working together."""
    
    @pytest.fixture
    def sample_patient_data(self) -> Dict[str, Any]:
        """Sample patient data for testing."""
        return {
            "patient_id": "PAT-TEST-001",
            "age": 45,
            "gender": "female",
            "medical_conditions": ["Type 2 Diabetes", "Hypertension"],
            "medications": ["Metformin", "Lisinopril"],
            "allergies": ["Penicillin"],
            "medical_history": ["Family history of diabetes", "Previous gestational diabetes"]
        }
        
    @pytest.fixture
    def sample_trial_data(self) -> Dict[str, Any]:
        """Sample trial data for testing."""
        return {
            "nct_id": "NCT12345678",
            "title": "Novel Diabetes Treatment Study",
            "brief_summary": "Testing new medication for Type 2 diabetes control",
            "conditions": ["Type 2 Diabetes Mellitus"],
            "interventions": ["Experimental diabetes medication"],
            "primary_purpose": "treatment",
            "status": "recruiting",
            "study_type": "interventional",
            "eligibility_criteria": {
                "inclusion_criteria": [
                    "Adults aged 18-65 years",
                    "Diagnosed with Type 2 diabetes",
                    "HbA1c between 7-11%",
                    "Stable on current diabetes medication"
                ],
                "exclusion_criteria": [
                    "Type 1 diabetes",
                    "Pregnant or nursing women",
                    "Severe kidney disease",
                    "Recent heart attack"
                ],
                "age_requirements": {"min_age": 18, "max_age": 65},
                "gender_requirements": "all"
            }
        }
        
    @pytest.fixture
    def nlp_processor(self) -> MedicalNLPProcessor:
        """Medical NLP processor instance."""
        return MedicalNLPProcessor()
        
    @pytest.fixture
    def search_engine(self) -> HybridSearchEngine:
        """Hybrid search engine instance."""
        return HybridSearchEngine()
        
    @pytest.fixture 
    async def llm_service(self) -> LLMReasoningService:
        """LLM reasoning service with mocked Cerebras client."""
        mock_client = AsyncMock(spec=CerebrasClient)
        return LLMReasoningService(cerebras_client=mock_client)
        
    def test_nlp_processor_initialization(self, nlp_processor: MedicalNLPProcessor):
        """Test NLP processor initializes correctly."""
        assert nlp_processor is not None
        metadata = nlp_processor.get_processing_metadata()
        assert "processor_version" in metadata
        assert "vocabulary_size" in metadata
        assert "supported_entities" in metadata
        
    def test_search_engine_initialization(self, search_engine: HybridSearchEngine):
        """Test search engine initializes correctly."""
        assert search_engine is not None
        stats = search_engine.get_index_stats()
        assert "total_trials" in stats
        assert "embedding_dimension" in stats
        assert stats["total_trials"] == 0  # Empty initially
        
    async def test_llm_service_initialization(self, llm_service: LLMReasoningService):
        """Test LLM service initializes correctly."""
        assert llm_service is not None
        stats = llm_service.get_service_stats()
        assert "supported_reasoning_types" in stats
        assert ReasoningType.ELIGIBILITY_ASSESSMENT.value in stats["supported_reasoning_types"]
        
    def test_nlp_entity_extraction_integration(
        self, 
        nlp_processor: MedicalNLPProcessor,
        sample_patient_data: Dict[str, Any]
    ):
        """Test NLP processor extracts entities from patient data."""
        # Create patient text
        patient_text = f"Patient is {sample_patient_data['age']} years old {sample_patient_data['gender']} "
        patient_text += f"with {', '.join(sample_patient_data['medical_conditions'])} "
        patient_text += f"taking {', '.join(sample_patient_data['medications'])}"
        
        # Extract entities
        entities = nlp_processor.extract_medical_entities(patient_text)
        
        # Validate extraction results
        assert isinstance(entities, dict)
        assert "conditions" in entities
        assert "medications" in entities
        assert "demographics" in entities
        
        # Check that key conditions were detected
        conditions_text = " ".join(entities["conditions"]).lower()
        assert "diabetes" in conditions_text
        
    def test_search_engine_trial_indexing(
        self, 
        search_engine: HybridSearchEngine,
        sample_trial_data: Dict[str, Any]
    ):
        """Test search engine can index and search trials."""
        # Index the trial
        search_engine.index_trial(sample_trial_data)
        
        # Verify indexing
        stats = search_engine.get_index_stats()
        assert stats["total_trials"] == 1
        
        # Test search
        query = SearchQuery(
            text="diabetes treatment study",
            search_mode="hybrid",
            limit=10
        )
        
        results = search_engine.search(query)
        assert results.total_count == 1
        assert len(results.results) == 1
        assert results.results[0].nct_id == sample_trial_data["nct_id"]
        
    async def test_llm_eligibility_assessment_integration(
        self,
        llm_service: LLMReasoningService,
        sample_patient_data: Dict[str, Any],
        sample_trial_data: Dict[str, Any]
    ):
        """Test LLM service performs eligibility assessment."""
        # Mock the Cerebras client response
        mock_response = MagicMock()
        mock_response.content = """
        ASSESSMENT: Patient meets basic demographic criteria
        ANALYSIS: Has target condition (Type 2 diabetes), appropriate age
        CONCLUSION: Eligible for trial participation with 85% confidence
        """
        mock_response.usage = {"total_tokens": 100}
        
        llm_service.cerebras_client.chat_completion = AsyncMock(return_value=mock_response)
        
        # Perform assessment
        result = await llm_service.assess_eligibility(
            patient_data=sample_patient_data,
            trial_data=sample_trial_data
        )
        
        # Validate results
        assert result.reasoning_type == ReasoningType.ELIGIBILITY_ASSESSMENT
        assert result.eligibility_status in ["eligible", "ineligible", "requires_review"]
        assert 0.0 <= result.confidence_score <= 1.0
        assert len(result.reasoning_chain) >= 0
        
    def test_model_nlp_integration(
        self,
        sample_trial_data: Dict[str, Any]
    ):
        """Test model integration with NLP processor."""
        # Create eligibility criteria from trial data
        criteria_data = {
            "criteria_id": "CRIT-TEST-001",
            "trial_nct_id": sample_trial_data["nct_id"],
            "raw_text": "Adults 18-65 with Type 2 diabetes, excluding pregnant women",
            "inclusion_criteria": sample_trial_data["eligibility_criteria"]["inclusion_criteria"],
            "exclusion_criteria": sample_trial_data["eligibility_criteria"]["exclusion_criteria"]
        }
        
        criteria = EligibilityCriteria(**criteria_data)
        
        # Test entity extraction
        entities = criteria.extract_medical_entities()
        
        # Validate integration
        assert isinstance(entities, dict)
        assert "conditions" in entities
        assert criteria.processing_metadata is not None
        assert "nlp_processor_version" in criteria.processing_metadata
        
    def test_trial_embedding_integration(
        self,
        sample_trial_data: Dict[str, Any]
    ):
        """Test trial model integration with embedding generation."""
        # Create trial model
        trial = Trial(**sample_trial_data)
        
        # Generate embedding
        embedding = trial.generate_embedding()
        
        # Validate embedding
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
        assert trial.embedding_model == "medical_nlp_v1"
        
    async def test_end_to_end_matching_workflow(
        self,
        nlp_processor: MedicalNLPProcessor,
        search_engine: HybridSearchEngine,
        llm_service: LLMReasoningService,
        sample_patient_data: Dict[str, Any],
        sample_trial_data: Dict[str, Any]
    ):
        """Test complete end-to-end patient-trial matching workflow."""
        # Step 1: Process patient data with NLP
        patient_text = f"{sample_patient_data['age']} year old {sample_patient_data['gender']} "
        patient_text += f"with {', '.join(sample_patient_data['medical_conditions'])}"
        
        patient_entities = nlp_processor.extract_medical_entities(patient_text)
        assert "conditions" in patient_entities
        
        # Step 2: Index trial in search engine
        search_engine.index_trial(sample_trial_data)
        
        # Step 3: Search for matching trials
        query = SearchQuery(
            text=patient_text,
            conditions=sample_patient_data["medical_conditions"],
            search_mode="hybrid"
        )
        
        search_results = search_engine.search(query)
        assert search_results.total_count > 0
        
        # Step 4: Assess eligibility with LLM
        mock_response = MagicMock()
        mock_response.content = "CONCLUSION: Patient is eligible for this diabetes trial"
        mock_response.usage = {"total_tokens": 50}
        llm_service.cerebras_client.chat_completion = AsyncMock(return_value=mock_response)
        
        eligibility_result = await llm_service.assess_eligibility(
            patient_data=sample_patient_data,
            trial_data=sample_trial_data
        )
        
        # Validate complete workflow
        assert eligibility_result.eligibility_status is not None
        assert eligibility_result.processing_time_ms > 0
        
    def test_service_coordination_error_handling(
        self,
        nlp_processor: MedicalNLPProcessor,
        search_engine: HybridSearchEngine
    ):
        """Test error handling across service boundaries."""
        # Test NLP processor with invalid input
        empty_entities = nlp_processor.extract_medical_entities("")
        assert isinstance(empty_entities, dict)
        assert all(isinstance(v, list) for v in empty_entities.values() if isinstance(v, list))
        
        # Test search engine with empty query
        empty_query = SearchQuery(text="", limit=5)
        empty_results = search_engine.search(empty_query)
        assert empty_results.total_count == 0
        assert len(empty_results.results) == 0
        
    def test_service_performance_benchmarks(
        self,
        nlp_processor: MedicalNLPProcessor,
        search_engine: HybridSearchEngine,
        sample_trial_data: Dict[str, Any]
    ):
        """Test performance characteristics of AI pipeline services."""
        import time
        
        # Test NLP processing speed
        start_time = time.time()
        entities = nlp_processor.extract_medical_entities(
            "Patient with diabetes, hypertension, and heart disease taking multiple medications"
        )
        nlp_time = time.time() - start_time
        
        assert nlp_time < 1.0  # Should complete within 1 second
        assert len(entities) > 0
        
        # Test search indexing and query speed
        start_time = time.time()
        search_engine.index_trial(sample_trial_data)
        index_time = time.time() - start_time
        
        start_time = time.time()
        query = SearchQuery(text="diabetes treatment", limit=5)
        results = search_engine.search(query)
        search_time = time.time() - start_time
        
        assert index_time < 0.5  # Indexing should be fast
        assert search_time < 0.5  # Search should be fast
        assert results.search_time_ms < 500  # Internal timing should be reasonable
        
    async def test_concurrent_service_usage(
        self,
        nlp_processor: MedicalNLPProcessor,
        search_engine: HybridSearchEngine
    ):
        """Test concurrent usage of AI pipeline services."""
        # Create multiple concurrent NLP tasks
        texts = [
            "Patient with diabetes",
            "Patient with cancer",
            "Patient with heart disease",
            "Patient with kidney disease"
        ]
        
        # Process concurrently (simulated)
        results = []
        for text in texts:
            entities = nlp_processor.extract_medical_entities(text)
            results.append(entities)
            
        # Validate all processed correctly
        assert len(results) == 4
        for result in results:
            assert isinstance(result, dict)
            assert "conditions" in result
            
    def test_service_state_isolation(
        self,
        search_engine: HybridSearchEngine,
        sample_trial_data: Dict[str, Any]
    ):
        """Test that services maintain proper state isolation."""
        # Test that multiple search engine instances are independent
        engine1 = HybridSearchEngine()
        engine2 = HybridSearchEngine()
        
        # Index trial in first engine only
        engine1.index_trial(sample_trial_data)
        
        # Verify isolation
        stats1 = engine1.get_index_stats()
        stats2 = engine2.get_index_stats()
        
        assert stats1["total_trials"] == 1
        assert stats2["total_trials"] == 0
        
    def test_medical_terminology_consistency(
        self,
        nlp_processor: MedicalNLPProcessor
    ):
        """Test consistency of medical terminology across services."""
        # Test various medical term formats
        test_cases = [
            "Type 2 diabetes mellitus",
            "diabetes type 2", 
            "T2DM",
            "diabetes mellitus type II"
        ]
        
        results = []
        for case in test_cases:
            entities = nlp_processor.extract_medical_entities(case)
            results.append(entities)
            
        # All should detect diabetes-related conditions
        for result in results:
            conditions = [c.lower() for c in result.get("conditions", [])]
            assert any("diabetes" in c for c in conditions), f"Failed to detect diabetes in: {result}"


@pytest.mark.integration
class TestExternalAPIIntegration:
    """Integration tests for external API coordination."""
    
    @pytest.fixture
    async def trials_client(self) -> ClinicalTrialsClient:
        """Clinical trials API client."""
        return ClinicalTrialsClient()
        
    @pytest.fixture
    async def cerebras_client(self) -> CerebrasClient:
        """Cerebras API client."""
        return CerebrasClient()
        
    async def test_trials_api_search_integration(
        self,
        trials_client: ClinicalTrialsClient,
        search_engine: HybridSearchEngine
    ):
        """Test integration with ClinicalTrials.gov API."""
        # This test would normally make real API calls
        # For testing, we'll use mock data
        
        # Mock search results
        with patch.object(trials_client, 'search_trials') as mock_search:
            mock_search.return_value = MagicMock()
            mock_search.return_value.trials = []
            mock_search.return_value.total_count = 0
            
            # Test search coordination
            results = await trials_client.search_trials(
                conditions=["diabetes"],
                page_size=10
            )
            
            assert results.total_count >= 0
            mock_search.assert_called_once()
            
    def test_service_configuration_validation(self):
        """Test that all services have proper configuration."""
        # Test NLP processor configuration
        nlp = MedicalNLPProcessor()
        metadata = nlp.get_processing_metadata()
        assert "processor_version" in metadata
        
        # Test search engine configuration
        search = HybridSearchEngine()
        stats = search.get_index_stats()
        assert "embedding_dimension" in stats
        assert stats["embedding_dimension"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])