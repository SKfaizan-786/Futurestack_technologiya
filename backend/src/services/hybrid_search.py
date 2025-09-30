"""
Hybrid Search Engine Service.

This service provides advanced search capabilities for clinical trials
by combining:
- Vector similarity search for semantic matching
- Keyword-based lexical search for exact terminology
- Fusion scoring for optimal relevance ranking
- Medical domain-specific search optimizations
"""
import json
import math
from typing import Dict, List, Set, Tuple, Optional, Any, Union
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from collections import defaultdict
import re

# For computing text similarity and embeddings
import hashlib
from pathlib import Path


@dataclass
class SearchResult:
    """Individual search result with scoring information."""
    trial_id: str
    nct_id: str
    title: str
    brief_summary: str
    conditions: List[str]
    relevance_score: float
    similarity_score: float
    keyword_score: float
    explanation: str
    matched_keywords: List[str] = field(default_factory=list)
    matched_concepts: List[str] = field(default_factory=list)


@dataclass
class SearchQuery:
    """Structured search query with multiple search modes."""
    text: str
    conditions: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    age_range: Optional[Tuple[int, int]] = None
    gender: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    status_filter: Optional[List[str]] = None
    search_mode: str = "hybrid"  # "hybrid", "semantic", "lexical"
    limit: int = 20
    offset: int = 0


@dataclass 
class SearchResults:
    """Search results with metadata."""
    results: List[SearchResult]
    total_count: int
    search_time_ms: float
    query: SearchQuery
    search_metadata: Dict[str, Any] = field(default_factory=dict)


class VectorEmbeddings:
    """Simple vector embedding simulation for medical text."""
    
    def __init__(self):
        """Initialize embedding generator."""
        self.dimension = 384  # Common embedding dimension
        self.medical_vocab = self._build_medical_vocabulary()
        
    def _build_medical_vocabulary(self) -> Dict[str, float]:
        """Build medical vocabulary with importance weights."""
        vocab = {}
        
        # High importance medical terms
        conditions = [
            'diabetes', 'cancer', 'hypertension', 'cardiovascular', 'oncology',
            'tumor', 'malignancy', 'carcinoma', 'lymphoma', 'leukemia',
            'heart disease', 'stroke', 'alzheimer', 'parkinson', 'copd',
            'asthma', 'kidney disease', 'liver disease', 'autoimmune'
        ]
        
        treatments = [
            'chemotherapy', 'immunotherapy', 'radiation', 'surgery', 'medication',
            'insulin', 'metformin', 'statins', 'ace inhibitors', 'beta blockers',
            'antibiotics', 'vaccines', 'biologics', 'car-t', 'gene therapy'
        ]
        
        procedures = [
            'clinical trial', 'biopsy', 'screening', 'diagnosis', 'treatment',
            'intervention', 'therapy', 'procedure', 'surgery', 'transplant'
        ]
        
        # Assign weights
        for term in conditions:
            vocab[term] = 1.0
        for term in treatments:
            vocab[term] = 0.9
        for term in procedures:
            vocab[term] = 0.8
            
        return vocab
        
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate simple embedding vector for text.
        In production, this would use a proper embedding model like sentence-transformers.
        """
        if not text:
            return [0.0] * self.dimension
            
        text_lower = text.lower()
        
        # Create embedding based on medical vocabulary presence
        embedding = [0.0] * self.dimension
        
        # Hash-based features for consistency
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        for i in range(self.dimension):
            # Base value from text hash
            hash_val = int(text_hash[i % len(text_hash)], 16) / 15.0
            embedding[i] = hash_val * 0.1
            
        # Enhance with medical vocabulary
        for term, weight in self.medical_vocab.items():
            if term in text_lower:
                # Add vocabulary-based features
                term_hash = hashlib.md5(term.encode()).hexdigest()
                for i in range(min(len(term_hash), self.dimension)):
                    hash_val = int(term_hash[i], 16) / 15.0
                    embedding[i] += hash_val * weight * 0.1
                    
        # Normalize to unit vector
        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
            
        return embedding
        
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2) or not vec1 or not vec2:
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
            
        return dot_product / (magnitude1 * magnitude2)


class LexicalSearchEngine:
    """Keyword-based search engine with medical terminology focus."""
    
    def __init__(self):
        """Initialize lexical search engine."""
        self.logger = logging.getLogger(__name__)
        self.medical_synonyms = self._build_synonym_map()
        
    def _build_synonym_map(self) -> Dict[str, List[str]]:
        """Build medical term synonym mapping."""
        return {
            'diabetes': ['diabetes mellitus', 'dm', 'diabetic', 'hyperglycemia'],
            'cancer': ['carcinoma', 'tumor', 'neoplasm', 'malignancy', 'oncology'],
            'heart disease': ['cardiovascular disease', 'cvd', 'cardiac', 'coronary'],
            'hypertension': ['high blood pressure', 'htn', 'elevated bp'],
            'kidney disease': ['renal disease', 'nephropathy', 'ckd'],
            'liver disease': ['hepatic disease', 'hepatitis', 'cirrhosis'],
            'lung disease': ['pulmonary disease', 'respiratory disease', 'copd'],
            'medication': ['drug', 'medicine', 'pharmaceutical', 'therapy'],
            'treatment': ['therapy', 'intervention', 'procedure', 'protocol']
        }
        
    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        if not text:
            return []
            
        text_lower = text.lower()
        
        # Extract medical terms
        keywords = []
        
        # Check for exact medical terms
        for term in self.medical_synonyms.keys():
            if term in text_lower:
                keywords.append(term)
                
        # Extract medical patterns
        medical_patterns = [
            r'\b\w*diabetes\w*\b',
            r'\b\w*cancer\w*\b', 
            r'\b\w*cardio\w*\b',
            r'\b\w*therapy\w*\b',
            r'\b\w*treatment\w*\b',
            r'\bnct\d+\b',  # NCT IDs
            r'\b(?:type\s*[12])\b'  # Type 1/2
        ]
        
        for pattern in medical_patterns:
            matches = re.findall(pattern, text_lower)
            keywords.extend(matches)
            
        # Extract capitalized medical terms (likely proper nouns)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        keywords.extend([noun.lower() for noun in proper_nouns])
        
        return list(set(keywords))
        
    def calculate_keyword_score(self, query_keywords: List[str], target_text: str) -> float:
        """Calculate keyword-based relevance score."""
        if not query_keywords or not target_text:
            return 0.0
            
        target_keywords = self.extract_keywords(target_text)
        target_text_lower = target_text.lower()
        
        matches = 0
        total_weight = 0
        
        for keyword in query_keywords:
            keyword_lower = keyword.lower()
            weight = 1.0
            
            # Exact match
            if keyword_lower in target_text_lower:
                matches += weight
                
            # Synonym match
            elif keyword_lower in self.medical_synonyms:
                for synonym in self.medical_synonyms[keyword_lower]:
                    if synonym in target_text_lower:
                        matches += weight * 0.8  # Synonym match gets 80% weight
                        break
                        
            total_weight += weight
            
        return matches / total_weight if total_weight > 0 else 0.0


class HybridSearchEngine:
    """
    Advanced hybrid search engine combining semantic and lexical search.
    
    Provides comprehensive search capabilities for clinical trials including:
    - Vector similarity search for semantic matching
    - Keyword-based lexical search for exact terminology
    - Fusion scoring using Reciprocal Rank Fusion (RRF)
    - Medical domain-specific optimizations
    - Filtering and ranking capabilities
    """
    
    def __init__(self):
        """Initialize the hybrid search engine."""
        self.logger = logging.getLogger(__name__)
        self.embeddings = VectorEmbeddings()
        self.lexical_engine = LexicalSearchEngine()
        self.trial_index = {}  # In-memory trial index
        self.embedding_cache = {}  # Cache for generated embeddings
        
    def index_trial(self, trial_data: Dict[str, Any]) -> None:
        """
        Index a clinical trial for search.
        
        Args:
            trial_data: Trial data dictionary with required fields
        """
        trial_id = trial_data.get('id') or trial_data.get('nct_id')
        if not trial_id:
            self.logger.warning("Trial missing ID, skipping indexing")
            return
            
        # Create search text
        search_text = self._create_search_text(trial_data)
        
        # Generate embedding
        embedding = self.embeddings.generate_embedding(search_text)
        
        # Index the trial
        self.trial_index[trial_id] = {
            **trial_data,
            'search_text': search_text,
            'embedding': embedding,
            'keywords': self.lexical_engine.extract_keywords(search_text),
            'indexed_at': datetime.now(timezone.utc)
        }
        
        self.logger.info(f"Indexed trial {trial_id}")
        
    def _create_search_text(self, trial_data: Dict[str, Any]) -> str:
        """Create comprehensive search text from trial data."""
        components = []
        
        # Core fields
        if title := trial_data.get('title'):
            components.append(title)
        if summary := trial_data.get('brief_summary'):
            components.append(summary)
            
        # Conditions
        if conditions := trial_data.get('conditions'):
            if isinstance(conditions, list):
                components.extend(conditions)
            elif isinstance(conditions, str):
                components.append(conditions)
                
        # Interventions
        if interventions := trial_data.get('interventions'):
            if isinstance(interventions, list):
                components.extend(interventions)
            elif isinstance(interventions, str):
                components.append(interventions)
                
        # Purpose and phase
        if purpose := trial_data.get('primary_purpose'):
            components.append(purpose)
        if phase := trial_data.get('phase'):
            components.append(phase)
            
        # Eligibility criteria
        if criteria := trial_data.get('eligibility_criteria'):
            if isinstance(criteria, dict):
                if inclusion := criteria.get('inclusion_criteria'):
                    components.extend(inclusion if isinstance(inclusion, list) else [inclusion])
                if exclusion := criteria.get('exclusion_criteria'):
                    components.extend(exclusion if isinstance(exclusion, list) else [exclusion])
            elif isinstance(criteria, str):
                components.append(criteria)
                
        return ' '.join(str(comp) for comp in components if comp)
        
    def search(self, query: SearchQuery) -> SearchResults:
        """
        Perform hybrid search on indexed trials.
        
        Args:
            query: Search query with text and filters
            
        Returns:
            SearchResults with ranked trials
        """
        start_time = datetime.now(timezone.utc)
        
        if query.search_mode == "semantic":
            results = self._semantic_search(query)
        elif query.search_mode == "lexical":
            results = self._lexical_search(query)
        else:  # hybrid
            results = self._hybrid_search(query)
            
        # Apply filters
        filtered_results = self._apply_filters(results, query)
        
        # Paginate
        total_count = len(filtered_results)
        start_idx = query.offset
        end_idx = min(start_idx + query.limit, total_count)
        paginated_results = filtered_results[start_idx:end_idx]
        
        # Calculate search time
        search_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return SearchResults(
            results=paginated_results,
            total_count=total_count,
            search_time_ms=search_time,
            query=query,
            search_metadata={
                "indexed_trials": len(self.trial_index),
                "search_mode": query.search_mode,
                "filters_applied": self._get_applied_filters(query)
            }
        )
        
    def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform semantic search using vector similarity."""
        if not query.text:
            return []
            
        # Generate query embedding
        query_embedding = self.embeddings.generate_embedding(query.text)
        
        results = []
        for trial_id, trial_data in self.trial_index.items():
            if 'embedding' not in trial_data:
                continue
                
            # Calculate similarity
            similarity = self.embeddings.cosine_similarity(
                query_embedding, 
                trial_data['embedding']
            )
            
            if similarity > 0.1:  # Minimum threshold
                result = SearchResult(
                    trial_id=trial_id,
                    nct_id=trial_data.get('nct_id', trial_id),
                    title=trial_data.get('title', ''),
                    brief_summary=trial_data.get('brief_summary', ''),
                    conditions=trial_data.get('conditions', []),
                    relevance_score=similarity,
                    similarity_score=similarity,
                    keyword_score=0.0,
                    explanation=f"Semantic similarity: {similarity:.3f}",
                    matched_concepts=self._extract_matched_concepts(query.text, trial_data['search_text'])
                )
                results.append(result)
                
        return sorted(results, key=lambda x: x.similarity_score, reverse=True)
        
    def _lexical_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform lexical search using keyword matching."""
        query_keywords = self.lexical_engine.extract_keywords(query.text)
        if query.keywords:
            query_keywords.extend(query.keywords)
            
        if not query_keywords:
            return []
            
        results = []
        for trial_id, trial_data in self.trial_index.items():
            # Calculate keyword score
            keyword_score = self.lexical_engine.calculate_keyword_score(
                query_keywords,
                trial_data['search_text']
            )
            
            if keyword_score > 0.1:  # Minimum threshold
                matched_keywords = self._find_matched_keywords(
                    query_keywords,
                    trial_data['search_text']
                )
                
                result = SearchResult(
                    trial_id=trial_id,
                    nct_id=trial_data.get('nct_id', trial_id),
                    title=trial_data.get('title', ''),
                    brief_summary=trial_data.get('brief_summary', ''),
                    conditions=trial_data.get('conditions', []),
                    relevance_score=keyword_score,
                    similarity_score=0.0,
                    keyword_score=keyword_score,
                    explanation=f"Keyword match: {keyword_score:.3f}",
                    matched_keywords=matched_keywords
                )
                results.append(result)
                
        return sorted(results, key=lambda x: x.keyword_score, reverse=True)
        
    def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform hybrid search using Reciprocal Rank Fusion."""
        # Get results from both search modes
        semantic_results = self._semantic_search(query)
        lexical_results = self._lexical_search(query)
        
        # Create rank maps
        semantic_ranks = {r.trial_id: i + 1 for i, r in enumerate(semantic_results)}
        lexical_ranks = {r.trial_id: i + 1 for i, r in enumerate(lexical_results)}
        
        # Combine all trial IDs
        all_trial_ids = set(semantic_ranks.keys()) | set(lexical_ranks.keys())
        
        # Calculate RRF scores
        k = 60  # RRF parameter
        fused_results = []
        
        for trial_id in all_trial_ids:
            semantic_rank = semantic_ranks.get(trial_id, float('inf'))
            lexical_rank = lexical_ranks.get(trial_id, float('inf'))
            
            # RRF formula
            rrf_score = (1.0 / (k + semantic_rank)) + (1.0 / (k + lexical_rank))
            
            # Get trial data
            trial_data = self.trial_index[trial_id]
            
            # Find original scores
            semantic_score = 0.0
            lexical_score = 0.0
            matched_keywords = []
            matched_concepts = []
            
            for result in semantic_results:
                if result.trial_id == trial_id:
                    semantic_score = result.similarity_score
                    matched_concepts = result.matched_concepts
                    break
                    
            for result in lexical_results:
                if result.trial_id == trial_id:
                    lexical_score = result.keyword_score
                    matched_keywords = result.matched_keywords
                    break
                    
            result = SearchResult(
                trial_id=trial_id,
                nct_id=trial_data.get('nct_id', trial_id),
                title=trial_data.get('title', ''),
                brief_summary=trial_data.get('brief_summary', ''),
                conditions=trial_data.get('conditions', []),
                relevance_score=rrf_score,
                similarity_score=semantic_score,
                keyword_score=lexical_score,
                explanation=f"Hybrid score: {rrf_score:.3f} (semantic: {semantic_score:.3f}, lexical: {lexical_score:.3f})",
                matched_keywords=matched_keywords,
                matched_concepts=matched_concepts
            )
            fused_results.append(result)
            
        return sorted(fused_results, key=lambda x: x.relevance_score, reverse=True)
        
    def _apply_filters(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        """Apply query filters to search results."""
        filtered = results
        
        # Filter by conditions
        if query.conditions:
            condition_set = {c.lower() for c in query.conditions}
            filtered = [
                r for r in filtered 
                if any(c.lower() in condition_set for c in r.conditions)
            ]
            
        # Filter by status
        if query.status_filter:
            status_set = {s.lower() for s in query.status_filter}
            filtered = [
                r for r in filtered
                if self.trial_index[r.trial_id].get('status', '').lower() in status_set
            ]
            
        # Filter by age range
        if query.age_range:
            min_age, max_age = query.age_range
            filtered = [
                r for r in filtered
                if self._trial_matches_age_range(r.trial_id, min_age, max_age)
            ]
            
        # Filter by gender
        if query.gender and query.gender != "all":
            filtered = [
                r for r in filtered
                if self._trial_matches_gender(r.trial_id, query.gender)
            ]
            
        return filtered
        
    def _trial_matches_age_range(self, trial_id: str, min_age: int, max_age: int) -> bool:
        """Check if trial matches age range criteria."""
        trial = self.trial_index.get(trial_id, {})
        criteria = trial.get('eligibility_criteria', {})
        
        trial_min = criteria.get('min_age')
        trial_max = criteria.get('max_age')
        
        # If trial has no age limits, it matches
        if trial_min is None and trial_max is None:
            return True
            
        # Check overlap
        if trial_min is not None and max_age < trial_min:
            return False
        if trial_max is not None and min_age > trial_max:
            return False
            
        return True
        
    def _trial_matches_gender(self, trial_id: str, gender: str) -> bool:
        """Check if trial matches gender criteria."""
        trial = self.trial_index.get(trial_id, {})
        criteria = trial.get('eligibility_criteria', {})
        trial_gender = criteria.get('gender', 'all').lower()
        
        return trial_gender == 'all' or trial_gender == gender.lower()
        
    def _extract_matched_concepts(self, query_text: str, target_text: str) -> List[str]:
        """Extract semantically matched concepts."""
        query_keywords = self.lexical_engine.extract_keywords(query_text)
        target_keywords = self.lexical_engine.extract_keywords(target_text)
        
        matched = []
        for q_keyword in query_keywords:
            for t_keyword in target_keywords:
                if self._are_related_concepts(q_keyword, t_keyword):
                    matched.append(t_keyword)
                    
        return list(set(matched))
        
    def _are_related_concepts(self, concept1: str, concept2: str) -> bool:
        """Check if two concepts are semantically related."""
        # Simple implementation - in production use embeddings
        c1_lower = concept1.lower()
        c2_lower = concept2.lower()
        
        # Exact match
        if c1_lower == c2_lower:
            return True
            
        # Check synonyms
        for term, synonyms in self.lexical_engine.medical_synonyms.items():
            if c1_lower in [term] + synonyms and c2_lower in [term] + synonyms:
                return True
                
        # Substring match for related terms
        if len(c1_lower) > 4 and len(c2_lower) > 4:
            if c1_lower in c2_lower or c2_lower in c1_lower:
                return True
                
        return False
        
    def _find_matched_keywords(self, query_keywords: List[str], target_text: str) -> List[str]:
        """Find which query keywords matched in target text."""
        target_lower = target_text.lower()
        matched = []
        
        for keyword in query_keywords:
            if keyword.lower() in target_lower:
                matched.append(keyword)
                
        return matched
        
    def _get_applied_filters(self, query: SearchQuery) -> List[str]:
        """Get list of applied filters for metadata."""
        filters = []
        if query.conditions:
            filters.append("conditions")
        if query.status_filter:
            filters.append("status")
        if query.age_range:
            filters.append("age_range")
        if query.gender and query.gender != "all":
            filters.append("gender")
        if query.location:
            filters.append("location")
        return filters
        
    def get_index_stats(self) -> Dict[str, Any]:
        """Get search index statistics."""
        return {
            "total_trials": len(self.trial_index),
            "embedding_dimension": self.embeddings.dimension,
            "medical_vocabulary_size": len(self.embeddings.medical_vocab),
            "synonym_groups": len(self.lexical_engine.medical_synonyms),
            "cache_size": len(self.embedding_cache),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    def clear_index(self) -> None:
        """Clear the search index."""
        self.trial_index.clear()
        self.embedding_cache.clear()
        self.logger.info("Search index cleared")
        
    def remove_trial(self, trial_id: str) -> bool:
        """Remove a trial from the search index."""
        if trial_id in self.trial_index:
            del self.trial_index[trial_id]
            self.logger.info(f"Removed trial {trial_id} from index")
            return True
        return False
        
    def get_trial_embedding(self, trial_id: str) -> Optional[List[float]]:
        """Get embedding vector for a specific trial."""
        trial_data = self.trial_index.get(trial_id)
        return trial_data.get('embedding') if trial_data else None
        
    def bulk_index_trials(self, trials: List[Dict[str, Any]]) -> int:
        """Bulk index multiple trials."""
        indexed_count = 0
        for trial_data in trials:
            try:
                self.index_trial(trial_data)
                indexed_count += 1
            except Exception as e:
                self.logger.error(f"Failed to index trial: {e}")
                
        self.logger.info(f"Bulk indexed {indexed_count}/{len(trials)} trials")
        return indexed_count