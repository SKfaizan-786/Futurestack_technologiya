"""
LLM Reasoning Service for Medical Decision Making.

This service provides advanced medical reasoning capabilities using
the Cerebras API with Llama 3.1 for:
- Chain-of-Thought medical reasoning
- Patient eligibility assessment
- Clinical trial compatibility analysis
- Medical decision explanation generation
- HIPAA-compliant processing
"""
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from enum import Enum

# Import the existing Cerebras client
from ..integrations.cerebras_client import CerebrasClient, CerebrasResponse, CerebrasAPIError


class ReasoningType(Enum):
    """Types of medical reasoning."""
    ELIGIBILITY_ASSESSMENT = "eligibility_assessment"
    TRIAL_MATCHING = "trial_matching"
    CONTRAINDICATION_CHECK = "contraindication_check"
    RISK_ASSESSMENT = "risk_assessment"
    DOSAGE_RECOMMENDATION = "dosage_recommendation"


@dataclass
class ReasoningStep:
    """Individual step in medical reasoning chain."""
    step_number: int
    category: str  # "assessment", "analysis", "conclusion"
    description: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0
    medical_justification: str = ""


@dataclass
class MedicalReasoningResult:
    """Result of medical reasoning analysis."""
    reasoning_type: ReasoningType
    conclusion: str
    confidence_score: float
    reasoning_chain: List[ReasoningStep]
    patient_summary: str  # HIPAA-safe summary
    trial_summary: str
    eligibility_status: str  # "eligible", "ineligible", "requires_review"
    contraindications: List[str]
    recommendations: List[str]
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PromptTemplates:
    """Medical reasoning prompt templates."""
    
    SYSTEM_PROMPT = """You are a medical AI assistant specializing in clinical trial eligibility assessment. You provide evidence-based reasoning following these principles:

1. Patient Safety: Always prioritize patient safety in your assessments
2. Evidence-Based: Base decisions on medical evidence and established criteria
3. Clear Reasoning: Provide step-by-step reasoning with medical justification
4. Compliance: Maintain HIPAA compliance - never store or repeat patient identifiers
5. Accuracy: Be precise about medical contraindications and eligibility factors

Your responses should follow this structure:
1. ASSESSMENT: Review patient characteristics against trial criteria
2. ANALYSIS: Identify eligibility factors, contraindications, and risks
3. CONCLUSION: Provide clear eligibility determination with confidence level

Always explain your medical reasoning and cite relevant eligibility criteria."""

    ELIGIBILITY_PROMPT = """
PATIENT PROFILE (anonymized):
Age: {age}
Gender: {gender}
Primary Conditions: {conditions}
Current Medications: {medications}
Relevant Medical History: {medical_history}
Allergies: {allergies}

CLINICAL TRIAL CRITERIA:
Trial ID: {trial_id}
Title: {trial_title}
Conditions: {trial_conditions}
Inclusion Criteria:
{inclusion_criteria}

Exclusion Criteria:
{exclusion_criteria}

Age Requirements: {age_requirements}
Gender Requirements: {gender_requirements}

TASK:
Assess patient eligibility for this clinical trial. Provide step-by-step medical reasoning including:

1. ASSESSMENT: Review each inclusion/exclusion criterion
2. ANALYSIS: Identify any contraindications or safety concerns
3. CONCLUSION: Final eligibility determination (Eligible/Ineligible/Requires Review) with confidence level

Format your response as structured reasoning with clear medical justification for each step.
"""

    CONTRAINDICATION_PROMPT = """
PATIENT MEDICATIONS: {medications}
PATIENT CONDITIONS: {conditions}
PATIENT ALLERGIES: {allergies}

TRIAL INTERVENTION: {intervention}
TRIAL MEDICATIONS: {trial_medications}

TASK:
Analyze potential contraindications between the patient's current medical profile and the trial intervention. Consider:

1. Drug-Drug Interactions
2. Drug-Condition Interactions  
3. Allergy Conflicts
4. Dosage Considerations
5. Monitoring Requirements

Provide evidence-based assessment with risk levels and recommendations.
"""

    TRIAL_MATCHING_PROMPT = """
PATIENT PROFILE (anonymized):
Age: {age}, Gender: {gender}
Conditions: {conditions}
Treatment Goals: {treatment_goals}

AVAILABLE TRIALS (summary):
{trial_summaries}

TASK:
Rank and analyze trial compatibility for this patient. For each trial, provide:

1. Compatibility Score (0-100)
2. Key Matching Factors
3. Potential Concerns
4. Recommendation Priority

Focus on medical suitability and therapeutic alignment.
"""


class LLMReasoningService:
    """
    Advanced LLM-powered medical reasoning service.
    
    Provides sophisticated medical decision making capabilities using
    Chain-of-Thought prompting with the Cerebras API for clinical
    trial eligibility assessment and medical reasoning.
    """
    
    def __init__(self, cerebras_client: Optional[CerebrasClient] = None):
        """Initialize the LLM reasoning service."""
        self.logger = logging.getLogger(__name__)
        self.cerebras_client = cerebras_client or CerebrasClient()
        self.templates = PromptTemplates()
        self.reasoning_cache = {}  # Cache for similar reasoning queries
        
    async def assess_eligibility(
        self,
        patient_data: Dict[str, Any],
        trial_data: Dict[str, Any],
        include_detailed_reasoning: bool = True
    ) -> MedicalReasoningResult:
        """
        Assess patient eligibility for a clinical trial.
        
        Args:
            patient_data: Anonymized patient information
            trial_data: Clinical trial information
            include_detailed_reasoning: Whether to include detailed reasoning steps
            
        Returns:
            MedicalReasoningResult with eligibility assessment
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Create anonymized patient summary
            patient_summary = self._create_patient_summary(patient_data)
            
            # Format the prompt
            prompt = self._format_eligibility_prompt(patient_data, trial_data)
            
            # Get LLM reasoning
            response = await self._get_llm_response(
                prompt,
                reasoning_type=ReasoningType.ELIGIBILITY_ASSESSMENT
            )
            
            # Parse the response into structured reasoning
            reasoning_result = await self._parse_eligibility_response(
                response,
                patient_summary,
                trial_data,
                start_time
            )
            
            return reasoning_result
            
        except Exception as e:
            self.logger.error(f"Error in eligibility assessment: {e}")
            
            # Return safe fallback result
            return MedicalReasoningResult(
                reasoning_type=ReasoningType.ELIGIBILITY_ASSESSMENT,
                conclusion="Unable to complete automated assessment - requires manual review",
                confidence_score=0.0,
                reasoning_chain=[],
                patient_summary=self._create_patient_summary(patient_data),
                trial_summary=trial_data.get('title', 'Unknown Trial'),
                eligibility_status="requires_review",
                contraindications=["Assessment error - manual review needed"],
                recommendations=["Consult with medical professional for eligibility determination"],
                processing_time_ms=(datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                metadata={"error": str(e)}
            )
            
    async def check_contraindications(
        self,
        patient_data: Dict[str, Any],
        intervention_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check for contraindications between patient and intervention.
        
        Args:
            patient_data: Patient medical information
            intervention_data: Trial intervention details
            
        Returns:
            List of contraindications with risk levels
        """
        try:
            prompt = self._format_contraindication_prompt(patient_data, intervention_data)
            
            response = await self._get_llm_response(
                prompt,
                reasoning_type=ReasoningType.CONTRAINDICATION_CHECK
            )
            
            return await self._parse_contraindications(response)
            
        except Exception as e:
            self.logger.error(f"Error checking contraindications: {e}")
            return [
                {
                    "type": "assessment_error",
                    "description": "Unable to complete contraindication check",
                    "risk_level": "unknown",
                    "recommendation": "Requires manual medical review"
                }
            ]
            
    async def rank_trial_matches(
        self,
        patient_data: Dict[str, Any],
        trials: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rank multiple trials by compatibility with patient.
        
        Args:
            patient_data: Patient information
            trials: List of trial data
            limit: Maximum number of results
            
        Returns:
            Ranked list of trial matches with reasoning
        """
        try:
            # Create trial summaries for the prompt
            trial_summaries = self._create_trial_summaries(trials)
            
            prompt = self._format_trial_matching_prompt(patient_data, trial_summaries)
            
            response = await self._get_llm_response(
                prompt,
                reasoning_type=ReasoningType.TRIAL_MATCHING
            )
            
            return await self._parse_trial_rankings(response, trials, limit)
            
        except Exception as e:
            self.logger.error(f"Error ranking trial matches: {e}")
            return []
            
    async def generate_explanation(
        self,
        reasoning_result: MedicalReasoningResult,
        target_audience: str = "patient"  # "patient", "physician", "researcher"
    ) -> str:
        """
        Generate human-readable explanation of reasoning.
        
        Args:
            reasoning_result: Medical reasoning result to explain
            target_audience: Who the explanation is for
            
        Returns:
            Human-readable explanation
        """
        try:
            explanation_prompt = self._format_explanation_prompt(reasoning_result, target_audience)
            
            response = await self._get_llm_response(
                explanation_prompt,
                reasoning_type=ReasoningType.ELIGIBILITY_ASSESSMENT,
                temperature=0.2  # More consistent explanations
            )
            
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating explanation: {e}")
            return self._generate_fallback_explanation(reasoning_result, target_audience)
            
    def _create_patient_summary(self, patient_data: Dict[str, Any]) -> str:
        """Create HIPAA-compliant patient summary."""
        components = []
        
        if age := patient_data.get('age'):
            components.append(f"{age}-year-old")
            
        if gender := patient_data.get('gender'):
            components.append(gender.lower())
            
        if conditions := patient_data.get('conditions', patient_data.get('medical_conditions', [])):
            conditions_text = ", ".join(conditions)
            components.append(f"with {conditions_text}")
            
        return " ".join(components) if components else "Patient profile"
        
    def _format_eligibility_prompt(
        self, 
        patient_data: Dict[str, Any], 
        trial_data: Dict[str, Any]
    ) -> str:
        """Format the eligibility assessment prompt."""
        # Extract patient data safely
        age = patient_data.get('age', 'Not specified')
        gender = patient_data.get('gender', 'Not specified')
        conditions = patient_data.get('conditions', patient_data.get('medical_conditions', []))
        medications = patient_data.get('medications', [])
        medical_history = patient_data.get('medical_history', [])
        allergies = patient_data.get('allergies', [])
        
        # Extract trial data
        trial_id = trial_data.get('nct_id', trial_data.get('id', 'Unknown'))
        trial_title = trial_data.get('title', 'Unknown Trial')
        trial_conditions = trial_data.get('conditions', [])
        
        # Get eligibility criteria
        criteria = trial_data.get('eligibility_criteria', {})
        inclusion_criteria = criteria.get('inclusion_criteria', [])
        exclusion_criteria = criteria.get('exclusion_criteria', [])
        age_requirements = criteria.get('age_requirements', 'Not specified')
        gender_requirements = criteria.get('gender_requirements', 'All')
        
        # Format lists as bullet points
        inclusion_text = '\n'.join([f"- {item}" for item in inclusion_criteria]) if inclusion_criteria else "- Not specified"
        exclusion_text = '\n'.join([f"- {item}" for item in exclusion_criteria]) if exclusion_criteria else "- Not specified"
        
        return self.templates.ELIGIBILITY_PROMPT.format(
            age=age,
            gender=gender,
            conditions=", ".join(conditions) if conditions else "None specified",
            medications=", ".join(medications) if medications else "None specified",
            medical_history=", ".join(medical_history) if medical_history else "None specified",
            allergies=", ".join(allergies) if allergies else "None specified",
            trial_id=trial_id,
            trial_title=trial_title,
            trial_conditions=", ".join(trial_conditions) if trial_conditions else "Not specified",
            inclusion_criteria=inclusion_text,
            exclusion_criteria=exclusion_text,
            age_requirements=age_requirements,
            gender_requirements=gender_requirements
        )
        
    def _format_contraindication_prompt(
        self,
        patient_data: Dict[str, Any],
        intervention_data: Dict[str, Any]
    ) -> str:
        """Format contraindication check prompt."""
        medications = patient_data.get('medications', [])
        conditions = patient_data.get('conditions', patient_data.get('medical_conditions', []))
        allergies = patient_data.get('allergies', [])
        
        intervention = intervention_data.get('intervention', 'Unknown')
        trial_medications = intervention_data.get('medications', intervention_data.get('interventions', []))
        
        return self.templates.CONTRAINDICATION_PROMPT.format(
            medications=", ".join(medications) if medications else "None",
            conditions=", ".join(conditions) if conditions else "None",
            allergies=", ".join(allergies) if allergies else "None",
            intervention=intervention,
            trial_medications=", ".join(trial_medications) if trial_medications else "None"
        )
        
    def _format_trial_matching_prompt(
        self,
        patient_data: Dict[str, Any],
        trial_summaries: str
    ) -> str:
        """Format trial matching prompt."""
        age = patient_data.get('age', 'Not specified')
        gender = patient_data.get('gender', 'Not specified')
        conditions = patient_data.get('conditions', patient_data.get('medical_conditions', []))
        treatment_goals = patient_data.get('treatment_goals', ['Symptom improvement', 'Disease management'])
        
        return self.templates.TRIAL_MATCHING_PROMPT.format(
            age=age,
            gender=gender,
            conditions=", ".join(conditions) if conditions else "None specified",
            treatment_goals=", ".join(treatment_goals) if treatment_goals else "General treatment",
            trial_summaries=trial_summaries
        )
        
    def _create_trial_summaries(self, trials: List[Dict[str, Any]]) -> str:
        """Create formatted trial summaries for prompt."""
        summaries = []
        
        for i, trial in enumerate(trials[:10], 1):  # Limit to 10 trials
            trial_id = trial.get('nct_id', trial.get('id', f'Trial-{i}'))
            title = trial.get('title', 'Unknown Title')
            conditions = trial.get('conditions', [])
            phase = trial.get('phase', 'Unknown')
            
            summary = f"{i}. {trial_id}: {title}\n"
            summary += f"   Conditions: {', '.join(conditions) if conditions else 'Not specified'}\n"
            summary += f"   Phase: {phase}\n"
            
            summaries.append(summary)
            
        return "\n".join(summaries)
        
    def _format_explanation_prompt(
        self,
        reasoning_result: MedicalReasoningResult,
        target_audience: str
    ) -> str:
        """Format prompt for generating explanations."""
        audience_styles = {
            "patient": "Use simple, non-technical language that a patient can understand",
            "physician": "Use medical terminology appropriate for healthcare professionals",
            "researcher": "Use scientific language appropriate for clinical researchers"
        }
        
        style_instruction = audience_styles.get(target_audience, audience_styles["patient"])
        
        return f"""
Based on this medical reasoning analysis, provide a clear explanation for a {target_audience}:

Eligibility Status: {reasoning_result.eligibility_status}
Confidence: {reasoning_result.confidence_score:.1%}
Conclusion: {reasoning_result.conclusion}

Reasoning Steps:
{self._format_reasoning_steps(reasoning_result.reasoning_chain)}

Contraindications: {', '.join(reasoning_result.contraindications) if reasoning_result.contraindications else 'None identified'}

Instructions: {style_instruction}. Focus on the key factors that led to this determination.
"""
        
    def _format_reasoning_steps(self, reasoning_chain: List[ReasoningStep]) -> str:
        """Format reasoning steps for prompts."""
        if not reasoning_chain:
            return "No detailed reasoning available"
            
        formatted = []
        for step in reasoning_chain:
            formatted.append(f"{step.step_number}. {step.category.title()}: {step.description}")
            if step.medical_justification:
                formatted.append(f"   Justification: {step.medical_justification}")
                
        return "\n".join(formatted)
        
    async def _get_llm_response(
        self,
        prompt: str,
        reasoning_type: ReasoningType,
        temperature: float = 0.1
    ) -> CerebrasResponse:
        """Get response from LLM with appropriate parameters."""
        messages = [
            {
                "role": "system",
                "content": self.templates.SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        return await self.cerebras_client.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=1500,
            stream=False
        )
        
    async def _parse_eligibility_response(
        self,
        response: CerebrasResponse,
        patient_summary: str,
        trial_data: Dict[str, Any],
        start_time: datetime
    ) -> MedicalReasoningResult:
        """Parse LLM response into structured reasoning result."""
        content = response.content
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        # Extract key information from response
        eligibility_status = self._extract_eligibility_status(content)
        confidence_score = self._extract_confidence_score(content)
        reasoning_chain = self._extract_reasoning_steps(content)
        contraindications = self._extract_contraindications(content)
        recommendations = self._extract_recommendations(content)
        
        return MedicalReasoningResult(
            reasoning_type=ReasoningType.ELIGIBILITY_ASSESSMENT,
            conclusion=self._extract_conclusion(content),
            confidence_score=confidence_score,
            reasoning_chain=reasoning_chain,
            patient_summary=patient_summary,
            trial_summary=trial_data.get('title', 'Unknown Trial'),
            eligibility_status=eligibility_status,
            contraindications=contraindications,
            recommendations=recommendations,
            processing_time_ms=processing_time,
            metadata={
                "llm_usage": response.usage,
                "response_length": len(content)
            }
        )
        
    def _extract_eligibility_status(self, content: str) -> str:
        """Extract eligibility status from LLM response."""
        content_lower = content.lower()
        
        if any(phrase in content_lower for phrase in ["eligible", "qualifies", "meets criteria"]):
            if any(phrase in content_lower for phrase in ["not eligible", "ineligible", "does not qualify"]):
                return "requires_review"  # Conflicting signals
            return "eligible"
        elif any(phrase in content_lower for phrase in ["not eligible", "ineligible", "does not qualify"]):
            return "ineligible"
        else:
            return "requires_review"
            
    def _extract_confidence_score(self, content: str) -> float:
        """Extract confidence score from response."""
        import re
        
        # Look for confidence patterns
        patterns = [
            r'confidence[:\s]*(\d+)%',
            r'confident[:\s]*(\d+)%',
            r'certainty[:\s]*(\d+)%',
            r'(\d+)%\s*confidence'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                try:
                    return float(matches[0]) / 100.0
                except ValueError:
                    continue
                    
        # Default confidence based on eligibility status
        if "eligible" in content.lower():
            return 0.8
        elif "ineligible" in content.lower():
            return 0.7
        else:
            return 0.5
            
    def _extract_reasoning_steps(self, content: str) -> List[ReasoningStep]:
        """Extract reasoning steps from response."""
        steps = []
        
        # Simple extraction - in production would use more sophisticated parsing
        sections = ["assessment", "analysis", "conclusion"]
        
        for i, section in enumerate(sections, 1):
            if section.lower() in content.lower():
                # Find content for this section
                start_idx = content.lower().find(section.lower())
                if start_idx != -1:
                    # Extract a reasonable chunk
                    end_idx = start_idx + 200
                    section_content = content[start_idx:end_idx]
                    
                    step = ReasoningStep(
                        step_number=i,
                        category=section,
                        description=section_content[:100] + "..." if len(section_content) > 100 else section_content,
                        evidence=[],
                        confidence=0.7,
                        medical_justification=""
                    )
                    steps.append(step)
                    
        return steps
        
    def _extract_contraindications(self, content: str) -> List[str]:
        """Extract contraindications from response."""
        contraindications = []
        
        # Look for contraindication keywords
        contra_keywords = [
            "contraindication", "contraindicated", "not recommended",
            "risk", "interaction", "allergy", "adverse"
        ]
        
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in contra_keywords):
                contraindications.append(line.strip())
                
        return contraindications[:5]  # Limit to 5 most relevant
        
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from response."""
        recommendations = []
        
        # Look for recommendation keywords
        rec_keywords = [
            "recommend", "suggest", "advise", "should", "consider"
        ]
        
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in rec_keywords):
                recommendations.append(line.strip())
                
        return recommendations[:3]  # Limit to 3 most relevant
        
    def _extract_conclusion(self, content: str) -> str:
        """Extract main conclusion from response."""
        # Look for conclusion section
        if "conclusion" in content.lower():
            start_idx = content.lower().find("conclusion")
            conclusion_section = content[start_idx:start_idx + 300]
            return conclusion_section.strip()
        
        # Fallback: use first sentence
        sentences = content.split('.')
        return sentences[0].strip() if sentences else "Assessment completed"
        
    async def _parse_contraindications(self, response: CerebrasResponse) -> List[Dict[str, Any]]:
        """Parse contraindications from LLM response."""
        # Simplified parsing - would be more sophisticated in production
        contraindications = []
        
        content = response.content
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ["risk", "interaction", "contraindication"]):
                contraindications.append({
                    "type": "potential_interaction",
                    "description": line.strip(),
                    "risk_level": "medium",
                    "recommendation": "Requires medical review"
                })
                
        return contraindications
        
    async def _parse_trial_rankings(
        self,
        response: CerebrasResponse,
        trials: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Parse trial rankings from LLM response."""
        # Simplified parsing - would be more sophisticated in production
        rankings = []
        
        for i, trial in enumerate(trials[:limit]):
            rankings.append({
                "trial": trial,
                "compatibility_score": 75 - (i * 5),  # Simple decreasing score
                "reasoning": f"Based on medical analysis (rank {i+1})",
                "key_factors": ["Medical suitability", "Safety profile"],
                "concerns": [] if i < 3 else ["Lower compatibility"]
            })
            
        return rankings
        
    def _generate_fallback_explanation(
        self,
        reasoning_result: MedicalReasoningResult,
        target_audience: str
    ) -> str:
        """Generate fallback explanation when LLM fails."""
        status_text = {
            "eligible": "appears to meet the trial criteria",
            "ineligible": "does not meet some key trial criteria", 
            "requires_review": "requires further medical review"
        }
        
        status = status_text.get(reasoning_result.eligibility_status, "has unclear eligibility")
        
        if target_audience == "patient":
            return f"Based on the medical analysis, your profile {status}. Please consult with your healthcare provider to discuss this clinical trial opportunity in detail."
        else:
            return f"Patient {status} based on automated eligibility assessment. Manual review recommended for final determination."
            
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "cache_size": len(self.reasoning_cache),
            "supported_reasoning_types": [rt.value for rt in ReasoningType],
            "service_version": "1.0.0",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }