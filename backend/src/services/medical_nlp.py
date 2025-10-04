"""
Medical NLP Processor Service.

This service provides advanced natural language processing capabilities
for medical text analysis, including:
- Medical entity extraction (conditions, medications, procedures)
- Clinical text preprocessing and normalization
- Medical terminology standardization
- Entity relationship extraction
"""
from typing import Dict, List, Set, Tuple, Optional, Any
import re
import logging
from datetime import datetime, timezone
from pathlib import Path

# Medical domain dictionaries and patterns
class MedicalVocabulary:
    """Medical vocabulary and pattern definitions."""
    
    # Specific cancer subtypes and compound conditions (checked first)
    COMPOUND_CONDITIONS = [
        'triple-negative breast cancer',
        'estrogen receptor positive breast cancer',
        'her2 positive breast cancer',
        'her2 negative breast cancer',
        'non-small cell lung cancer',
        'small cell lung cancer',
        'stage 3 non-small cell lung cancer',
        'stage 4 breast cancer',
        'metastatic breast cancer',
        'metastatic colorectal cancer',
        'colorectal cancer',
        'colon cancer',
        'rectal cancer',
        'castration-resistant prostate cancer',
        'acute myeloid leukemia',
        'chronic lymphocytic leukemia',
        'stage 1 breast cancer',
        'stage 2 breast cancer', 
        'stage 3 breast cancer',
        'stage 4 breast cancer',
        'locally advanced breast cancer',
        'type 1 diabetes mellitus',
        'type 2 diabetes mellitus',
        'gestational diabetes',
        'chronic kidney disease',
        'end stage renal disease',
        'coronary artery disease',
        'peripheral artery disease',
        'acute myocardial infarction',
        'congestive heart failure',
        'chronic obstructive pulmonary disease',
        'inflammatory bowel disease',
        'rheumatoid arthritis',
        'systemic lupus erythematosus',
        'multiple sclerosis',
        'parkinson disease',
        'alzheimer disease'
    ]
    
    # Common medical conditions
    CONDITIONS = {
        'diabetes': ['diabetes', 'diabetes mellitus', 'type 1 diabetes', 'type 2 diabetes', 'diabetic', 'dm', 't2dm', 'diabetes type 2', 'diabetes mellitus type ii'],
        'hypertension': ['hypertension', 'high blood pressure', 'htn', 'elevated blood pressure'],
        'cancer': ['cancer', 'carcinoma', 'tumor', 'neoplasm', 'malignancy', 'oncology'],
        'breast_cancer': ['breast cancer', 'breast carcinoma', 'breast neoplasm', 'breast tumor', 'triple negative breast cancer', 'her2 positive breast cancer', 'triple negative'],
        'lung_cancer': ['lung cancer', 'lung carcinoma', 'nsclc', 'non-small cell lung cancer', 'adenocarcinoma of lung', 'egfr mutation', 'egfr positive', 'brain metastases', 'stage 3 non-small cell lung cancer'],
        'colorectal_cancer': ['colorectal cancer', 'colon cancer', 'rectal cancer', 'colorectal carcinoma', 'metastatic colorectal cancer'],
        'prostate_cancer': ['prostate cancer', 'prostate carcinoma', 'castration-resistant prostate cancer'],
        'cardiovascular': ['heart disease', 'cardiovascular disease', 'cvd', 'coronary artery disease', 'cad'],
        'respiratory': ['asthma', 'copd', 'chronic obstructive pulmonary disease', 'bronchitis'],
        'kidney': ['kidney disease', 'renal disease', 'chronic kidney disease', 'ckd', 'nephropathy'],
        'liver': ['liver disease', 'hepatitis', 'cirrhosis', 'hepatic'],
        'neurological': ['alzheimer', 'parkinson', 'dementia', 'stroke', 'epilepsy', 'seizure'],
        'psychiatric': ['depression', 'anxiety', 'bipolar', 'schizophrenia', 'ptsd'],
        'autoimmune': ['rheumatoid arthritis', 'lupus', 'multiple sclerosis', 'ms', 'inflammatory bowel disease']
    }
    
    # Common medications
    MEDICATIONS = {
        'diabetes': ['metformin', 'insulin', 'glipizide', 'sitagliptin', 'empagliflozin'],
        'hypertension': ['lisinopril', 'amlodipine', 'hydrochlorothiazide', 'losartan', 'atenolol'],
        'cholesterol': ['atorvastatin', 'simvastatin', 'rosuvastatin', 'pravastatin'],
        'pain': ['ibuprofen', 'acetaminophen', 'aspirin', 'naproxen', 'tramadol'],
        'antibiotics': ['amoxicillin', 'azithromycin', 'ciprofloxacin', 'doxycycline'],
        'psychiatric': ['sertraline', 'fluoxetine', 'escitalopram', 'aripiprazole', 'quetiapine'],
        'chemotherapy': ['folfox', 'folfiri', 'capecitabine', 'oxaliplatin', 'carboplatin', 'docetaxel', 'paclitaxel'],
        'targeted_therapy': ['erlotinib', 'gefitinib', 'osimertinib', 'trastuzumab', 'bevacizumab', 'cetuximab'],
        'immunotherapy': ['pembrolizumab', 'nivolumab', 'atezolizumab', 'durvalumab']
    }
    
    # Medical procedures
    PROCEDURES = {
        'surgery': ['surgery', 'surgical procedure', 'operation', 'laparoscopic', 'endoscopic'],
        'cardiac': ['angioplasty', 'bypass', 'catheterization', 'echocardiogram', 'ekg', 'ecg'],
        'imaging': ['mri', 'ct scan', 'x-ray', 'ultrasound', 'pet scan', 'mammogram'],
        'biopsy': ['biopsy', 'tissue sample', 'pathology'],
        'transplant': ['transplant', 'organ transplant', 'bone marrow transplant'],
        'treatment': ['immunotherapy', 'chemotherapy', 'radiation therapy', 'targeted therapy']
    }
    
    # Lab values and tests
    LAB_VALUES = {
        'diabetes': ['hba1c', 'glucose', 'blood sugar', 'fasting glucose'],
        'lipids': ['cholesterol', 'ldl', 'hdl', 'triglycerides'],
        'kidney': ['creatinine', 'egfr', 'bun', 'protein in urine'],
        'liver': ['alt', 'ast', 'bilirubin', 'alkaline phosphatase'],
        'cardiac': ['troponin', 'bnp', 'nt-probnp'],
        'blood': ['hemoglobin', 'hematocrit', 'white blood cell', 'platelet count'],
        'biomarkers': ['pd-l1', 'pd-1', 'brca1', 'brca2', 'her2', 'egfr', 'kras']
    }


class MedicalNLPProcessor:
    """
    Advanced Medical NLP Processor for clinical text analysis.
    
    This service provides comprehensive medical text processing capabilities
    including entity extraction, text normalization, and clinical terminology
    standardization.
    """
    
    def __init__(self):
        """Initialize the Medical NLP Processor."""
        self.logger = logging.getLogger(__name__)
        self.vocabulary = MedicalVocabulary()
        self._compile_patterns()
        
    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient entity extraction."""
        self.condition_patterns = self._create_entity_patterns(self.vocabulary.CONDITIONS)
        self.medication_patterns = self._create_entity_patterns(self.vocabulary.MEDICATIONS)
        self.procedure_patterns = self._create_entity_patterns(self.vocabulary.PROCEDURES)
        self.lab_patterns = self._create_entity_patterns(self.vocabulary.LAB_VALUES)
        
        # Age patterns
        self.age_patterns = [
            r'(\d+)\s*(?:to|\-)\s*(\d+)\s*years?\s*(?:old|of\s*age)?',
            r'(?:aged?|age)\s*(\d+)\s*(?:to|\-)\s*(\d+)',
            r'(?:between|from)\s*(\d+)\s*(?:and|to|\-)\s*(\d+)\s*years?',
            r'(?:minimum|min)\s*age\s*(?:of\s*)?(\d+)',
            r'(?:maximum|max)\s*age\s*(?:of\s*)?(\d+)',
            r'(?:over|above)\s*(\d+)\s*years?',
            r'(?:under|below)\s*(\d+)\s*years?'
        ]
        
        # Gender patterns
        self.gender_patterns = [
            r'\b(?:male|men|man)\b',
            r'\b(?:female|women|woman)\b',
            r'\b(?:all\s*(?:genders?|sexes?))\b',
            r'\b(?:both\s*(?:genders?|sexes?))\b'
        ]
        
    def _create_entity_patterns(self, entity_dict: Dict[str, List[str]]) -> List[Tuple[str, str]]:
        """Create compiled regex patterns from entity dictionary."""
        patterns = []
        for category, terms in entity_dict.items():
            for term in terms:
                # Escape special regex characters and create word boundary pattern
                escaped_term = re.escape(term)
                pattern = f'\\b{escaped_term}\\b'
                patterns.append((category, re.compile(pattern, re.IGNORECASE)))
        return patterns
        
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess and normalize medical text.
        
        Args:
            text: Raw medical text
            
        Returns:
            Preprocessed and normalized text
        """
        if not text:
            return ""
            
        # Convert to lowercase for consistent processing
        text = text.lower()
        
        # Normalize whitespace
        text = re.sub(r'\\s+', ' ', text)
        
        # Normalize common medical abbreviations
        abbreviations = {
            r'\\bw/\\b': 'with',
            r'\\bw/o\\b': 'without', 
            r'\\bhx\\b': 'history',
            r'\\bdx\\b': 'diagnosis',
            r'\\btx\\b': 'treatment',
            r'\\bpt\\b': 'patient',
            r'\\byrs?\\b': 'years',
            r'\\bmos?\\b': 'months'
        }
        
        for abbrev, full_form in abbreviations.items():
            text = re.sub(abbrev, full_form, text)
            
        return text.strip()
        
    def extract_medical_entities(self, text: str, include_context: bool = True) -> Dict[str, List[str]]:
        """
        Extract medical entities from clinical text.
        
        Args:
            text: Clinical text to analyze
            include_context: Whether to include surrounding context for entities
            
        Returns:
            Dictionary mapping entity types to lists of extracted entities
        """
        if not text:
            return {
                "conditions": [],
                "excluded_conditions": [],
                "medications": [],
                "procedures": [],
                "lab_values": [],
                "demographics": [],
                "age_requirements": {"min_age": None, "max_age": None, "age_units": "years"},
                "gender_requirements": "all"
            }
            
        # Preprocess text
        processed_text = self.preprocess_text(text)
        original_text = text.lower()  # Keep original for compound pattern matching
        
        # First, extract compound conditions (multi-word medical terms)
        compound_conditions = self._extract_compound_conditions(original_text)
        
        # Then extract other entities by category
        entities = {
            "conditions": compound_conditions + self._extract_entities_by_patterns(processed_text, self.condition_patterns),
            "medications": self._extract_entities_by_patterns(processed_text, self.medication_patterns),
            "procedures": self._extract_entities_by_patterns(processed_text, self.procedure_patterns),
            "lab_values": self._extract_entities_by_patterns(processed_text, self.lab_patterns),
            "demographics": self._extract_demographics(processed_text),
            "age_requirements": self._extract_age_requirements(processed_text),
            "gender_requirements": self._extract_gender_requirements(processed_text)
        }
        
        # Handle exclusion criteria
        entities["excluded_conditions"] = self._extract_excluded_entities(processed_text)
        
        # Remove duplicates and clean up
        for key in ["conditions", "medications", "procedures", "lab_values"]:
            if key in entities and isinstance(entities[key], list):
                entities[key] = list(set(entities[key]))
        
        # Demographics is now a dict, not a list - no need to deduplicate
            
        return entities
        
    def _extract_compound_conditions(self, text: str) -> List[str]:
        """Extract compound medical conditions that should be preserved as complete terms."""
        found_conditions = []
        
        # Check each compound condition pattern
        for condition in self.vocabulary.COMPOUND_CONDITIONS:
            # Use a simpler approach: just check if the condition appears in the text
            # with flexible spacing and hyphen handling
            condition_pattern = re.escape(condition)
            condition_pattern = condition_pattern.replace(r'\\-', r'[-\\s]*')  # Allow hyphen or space
            condition_pattern = condition_pattern.replace(r'\\ ', r'\\s+')    # Allow flexible spacing
            
            if re.search(condition_pattern, text, re.IGNORECASE):
                found_conditions.append(condition)
                
        return found_conditions
        
    def _extract_entities_by_patterns(self, text: str, patterns: List[Tuple[str, re.Pattern]]) -> List[str]:
        """Extract entities using compiled regex patterns."""
        found_entities = []
        
        for category, pattern in patterns:
            matches = pattern.findall(text)
            if matches:
                found_entities.extend(matches)
                
        return found_entities
        
    def _extract_excluded_entities(self, text: str) -> List[str]:
        """Extract entities mentioned in exclusion contexts."""
        excluded_entities = []
        
        # Look for exclusion keywords
        exclusion_patterns = [
            r'exclusion[^:]*:([^\\n]+)',
            r'exclude[^:]*:([^\\n]+)',
            r'not\s+(?:eligible|allowed|permitted)[^:]*:([^\\n]+)',
            r'contraindication[^:]*:([^\\n]+)'
        ]
        
        for pattern in exclusion_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract medical entities from exclusion text
                exclusion_entities = self._extract_entities_by_patterns(match, self.condition_patterns)
                excluded_entities.extend(exclusion_entities)
                
        return list(set(excluded_entities))
        
    def _extract_age_requirements(self, text: str) -> Dict[str, Any]:
        """Extract age-related requirements from text."""
        age_info = {
            "min_age": None,
            "max_age": None, 
            "age_units": "years"
        }
        
        for pattern in self.age_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple) and len(match) == 2:
                        # Range pattern (e.g., "18-65 years")
                        min_age, max_age = match
                        age_info["min_age"] = int(min_age)
                        age_info["max_age"] = int(max_age)
                    elif isinstance(match, str):
                        # Single age pattern
                        age = int(match)
                        if "minimum" in pattern or "min" in pattern or "over" in pattern:
                            age_info["min_age"] = age
                        elif "maximum" in pattern or "max" in pattern or "under" in pattern:
                            age_info["max_age"] = age
                            
        return age_info
        
    def _extract_gender_requirements(self, text: str) -> str:
        """Extract gender requirements from text."""
        text_lower = text.lower()
        
        if any(pattern in text_lower for pattern in ["all gender", "both gender", "all sex", "both sex"]):
            return "all"
        elif any(pattern in text_lower for pattern in ["male", "men", "man"]) and \
             not any(pattern in text_lower for pattern in ["female", "women", "woman"]):
            return "male"
        elif any(pattern in text_lower for pattern in ["female", "women", "woman"]) and \
             not any(pattern in text_lower for pattern in ["male", "men", "man"]):
            return "female"
        else:
            return "all"
            
    def _extract_demographics(self, text: str) -> Dict[str, Any]:
        """Extract structured demographic information including age and gender."""
        demographics = {
            "age": None,
            "gender": None,
            "other_demographics": []
        }
        
        # Extract specific age (improved patterns to avoid stage confusion)
        age_patterns = [
            r'\bage\s*(\d+)\b',  # "age 45" - more specific word boundary
            r'(\d+)\s*year\s*old',  # "45 year old"
            r'(\d+)\s*year\s*old\s*(?:female|male|woman|man)',  # "45 year old female"
            r'(\d+)\s*yo\b',  # "45 yo" (year old abbreviation)
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    demographics["age"] = int(matches[0])
                    break  # Use first match found
                except (ValueError, IndexError):
                    continue
        
        # Extract specific gender
        gender_patterns = [
            (r'\b(?:female|woman|girl)\b', 'female'),
            (r'\b(?:male|man|boy)\b', 'male'),
        ]
        
        for pattern, gender in gender_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                demographics["gender"] = gender
                break
        
        # Extract other demographic information
        other_demographic_patterns = [
            r'\b(?:pregnant|pregnancy)\b',
            r'\b(?:nursing|breastfeeding)\b',
            r'\b(?:childbearing\s*age)\b',
            r'\b(?:postmenopausal)\b',
            r'\b(?:elderly|geriatric)\b',
            r'\b(?:pediatric|children)\b',
        ]
        
        for pattern in other_demographic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            demographics["other_demographics"].extend(matches)
            
        demographics["other_demographics"] = list(set(demographics["other_demographics"]))
        
        return demographics
        
    def calculate_text_complexity(self, text: str) -> float:
        """
        Calculate complexity score for medical text.
        
        Args:
            text: Medical text to analyze
            
        Returns:
            Complexity score between 0.0 and 1.0
        """
        if not text:
            return 0.0
            
        # Factors contributing to complexity
        factors = {
            'length': min(len(text) / 1000, 1.0) * 0.2,  # Text length
            'medical_terms': 0.0,  # Medical terminology density
            'criteria_count': 0.0,  # Number of criteria
            'nested_conditions': 0.0  # Nested logical conditions
        }
        
        # Count medical terms
        all_entities = self.extract_medical_entities(text)
        total_entities = sum(len(entities) for entities in all_entities.values() if isinstance(entities, list))
        factors['medical_terms'] = min(total_entities / 20, 1.0) * 0.3
        
        # Count criteria (inclusion/exclusion points)
        criteria_count = len(re.findall(r'[\\n\\r]\\s*[\\d\\-\\*]', text))
        factors['criteria_count'] = min(criteria_count / 10, 1.0) * 0.3
        
        # Check for nested conditions (AND, OR, NOT)
        logical_operators = len(re.findall(r'\\b(?:and|or|not|except|unless)\\b', text, re.IGNORECASE))
        factors['nested_conditions'] = min(logical_operators / 5, 1.0) * 0.2
        
        return sum(factors.values())
        
    def normalize_entity(self, entity: str, entity_type: str) -> str:
        """
        Normalize medical entity to standard form.
        
        Args:
            entity: Raw entity text
            entity_type: Type of entity (condition, medication, etc.)
            
        Returns:
            Normalized entity string
        """
        if not entity:
            return ""
            
        entity = entity.lower().strip()
        
        # Normalization mappings
        normalizations = {
            'condition': {
                'dm': 'diabetes mellitus',
                'htn': 'hypertension',
                'cad': 'coronary artery disease',
                'cvd': 'cardiovascular disease',
                'copd': 'chronic obstructive pulmonary disease',
                'ckd': 'chronic kidney disease'
            },
            'medication': {
                'ace inhibitor': 'ace inhibitors',
                'beta blocker': 'beta blockers', 
                'statin': 'statins'
            }
        }
        
        if entity_type in normalizations and entity in normalizations[entity_type]:
            return normalizations[entity_type][entity]
            
        return entity
        
    def get_processing_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the NLP processor.
        
        Returns:
            Dictionary containing processor metadata
        """
        return {
            "processor_version": "1.0.0",
            "vocabulary_size": {
                "conditions": sum(len(terms) for terms in self.vocabulary.CONDITIONS.values()),
                "medications": sum(len(terms) for terms in self.vocabulary.MEDICATIONS.values()),
                "procedures": sum(len(terms) for terms in self.vocabulary.PROCEDURES.values()),
                "lab_values": sum(len(terms) for terms in self.vocabulary.LAB_VALUES.values())
            },
            "supported_entities": [
                "conditions", "medications", "procedures", "lab_values", 
                "demographics", "age_requirements", "gender_requirements"
            ],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }