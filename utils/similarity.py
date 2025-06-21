import numpy as np
from typing import List, Tuple, Dict, Optional
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class SimilarityDetector:
    def __init__(self, similarity_threshold: float = 0.85, update_threshold: float = 0.75):
        """Initialize similarity detector with thresholds"""
        self.similarity_threshold = similarity_threshold
        self.update_threshold = update_threshold
    
    def calculate_cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            if embedding1.size == 0 or embedding2.size == 0:
                return 0.0
            
            # Reshape to 2D arrays for sklearn
            emb1 = embedding1.reshape(1, -1)
            emb2 = embedding2.reshape(1, -1)
            
            similarity = cosine_similarity(emb1, emb2)[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def calculate_keyword_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """Calculate Jaccard similarity between keyword sets"""
        if not keywords1 or not keywords2:
            return 0.0
        
        set1 = set(keywords1)
        set2 = set(keywords2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_entity_similarity(self, entities1: Dict[str, List[str]], entities2: Dict[str, List[str]]) -> float:
        """Calculate similarity based on named entities"""
        if not entities1 or not entities2:
            return 0.0
        
        total_similarity = 0.0
        entity_types = set(entities1.keys()).union(set(entities2.keys()))
        
        for entity_type in entity_types:
            ents1 = set(entities1.get(entity_type, []))
            ents2 = set(entities2.get(entity_type, []))
            
            if ents1 or ents2:
                intersection = len(ents1.intersection(ents2))
                union = len(ents1.union(ents2))
                type_similarity = intersection / union if union > 0 else 0.0
                total_similarity += type_similarity
        
        return total_similarity / len(entity_types) if entity_types else 0.0
    
    def calculate_combined_similarity(self, 
                                    embedding1: np.ndarray, 
                                    embedding2: np.ndarray,
                                    keywords1: List[str], 
                                    keywords2: List[str],
                                    entities1: Dict[str, List[str]], 
                                    entities2: Dict[str, List[str]],
                                    weights: Dict[str, float] = None) -> float:
        """Calculate combined similarity score using multiple metrics"""
        
        if weights is None:
            weights = {
                'embedding': 0.6,
                'keywords': 0.25,
                'entities': 0.15
            }
        
        # Calculate individual similarities
        embedding_sim = self.calculate_cosine_similarity(embedding1, embedding2)
        keyword_sim = self.calculate_keyword_similarity(keywords1, keywords2)
        entity_sim = self.calculate_entity_similarity(entities1, entities2)
        
        # Weighted combination
        combined_similarity = (
            weights['embedding'] * embedding_sim +
            weights['keywords'] * keyword_sim +
            weights['entities'] * entity_sim
        )
        
        logger.debug(f"Similarity scores - Embedding: {embedding_sim:.3f}, "
                    f"Keywords: {keyword_sim:.3f}, Entities: {entity_sim:.3f}, "
                    f"Combined: {combined_similarity:.3f}")
        
        return combined_similarity
    
    def is_duplicate(self, similarity_score: float) -> bool:
        """Check if similarity score indicates a duplicate"""
        return similarity_score >= self.similarity_threshold
    
    def is_update_candidate(self, similarity_score: float) -> bool:
        """Check if similarity score indicates a potential update"""
        return self.update_threshold <= similarity_score < self.similarity_threshold
    
    def find_most_similar(self, 
                         target_embedding: np.ndarray,
                         target_keywords: List[str],
                         target_entities: Dict[str, List[str]],
                         candidates: List[Dict]) -> Tuple[Optional[Dict], float]:
        """Find the most similar candidate from a list"""
        
        if not candidates:
            return None, 0.0
        
        best_candidate = None
        best_similarity = 0.0
        
        for candidate in candidates:
            similarity = self.calculate_combined_similarity(
                target_embedding,
                candidate.get('embedding', np.array([])),
                target_keywords,
                candidate.get('keywords', []),
                target_entities,
                candidate.get('entities', {})
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_candidate = candidate
        
        return best_candidate, best_similarity
    
    def classify_relationship(self, similarity_score: float) -> str:
        """Classify the relationship between two posts based on similarity"""
        if similarity_score >= self.similarity_threshold:
            return "duplicate"
        elif similarity_score >= self.update_threshold:
            return "update"
        else:
            return "new"
    
    def get_similarity_explanation(self, 
                                 embedding_sim: float,
                                 keyword_sim: float,
                                 entity_sim: float,
                                 combined_sim: float) -> str:
        """Generate human-readable explanation of similarity scores"""
        explanation = f"דמיון כולל: {combined_sim:.2%}\n"
        explanation += f"דמיון סמנטי: {embedding_sim:.2%}\n"
        explanation += f"דמיון מילות מפתח: {keyword_sim:.2%}\n"
        explanation += f"דמיון ישויות: {entity_sim:.2%}"
        
        return explanation