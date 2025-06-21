import re
import logging
from typing import List, Dict, Set
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class HebrewNLP:
    def __init__(self, model_name: str):
        """Initialize Hebrew NLP processor with sentence transformer model"""
        self.model = SentenceTransformer(model_name)
        logger.info(f"Loaded Hebrew NLP model: {model_name}")
        
        # Hebrew stop words (common words to filter out)
        self.hebrew_stop_words = {
            'של', 'את', 'על', 'אל', 'עם', 'כל', 'לא', 'זה', 'זו', 'זאת', 'הוא', 'היא', 'הם', 'הן',
            'אני', 'אתה', 'את', 'אנחנו', 'אתם', 'אתן', 'שלי', 'שלך', 'שלו', 'שלה', 'שלנו', 'שלכם', 'שלהם',
            'יש', 'אין', 'היה', 'הייתה', 'היו', 'יהיה', 'תהיה', 'יהיו', 'בין', 'אחר', 'אחרי', 'לפני',
            'תחת', 'מעל', 'ליד', 'בתוך', 'מחוץ', 'כמו', 'אם', 'כי', 'מה', 'מי', 'איך', 'איפה', 'מתי', 'למה'
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize Hebrew text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove Telegram usernames and channels
        text = re.sub(r'@\w+', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{3,}', '...', text)
        
        # Remove emojis (basic pattern)
        text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+', '', text)
        
        return text.strip()
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract Hebrew keywords from text"""
        if not text:
            return []
        
        # Split into words and filter Hebrew words
        words = re.findall(r'[\u0590-\u05FF]+', text)
        
        # Filter out stop words and short words
        keywords = [
            word for word in words 
            if len(word) > 2 and word not in self.hebrew_stop_words
        ]
        
        # Count frequency and return most common
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:max_keywords]]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from Hebrew text (basic implementation)"""
        entities = {
            'locations': [],
            'organizations': [],
            'persons': []
        }
        
        # Basic patterns for Hebrew entities
        # This is a simplified implementation - in production, use a proper Hebrew NER model
        
        # Common location patterns
        location_patterns = [
            r'ב(ירושלים|תל אביב|חיפה|באר שבע|אילת|נתניה|פתח תקווה|ראשון לציון|אשדוד|חולון)',
            r'(ירושלים|תל אביב|חיפה|באר שבע|אילת|נתניה|פתח תקווה|ראשון לציון|אשדוד|חולון)',
            r'(עזה|רמאללה|חברון|נבלס|בית לחם|יריחו)',
            r'(לבנון|סוריה|ירדן|מצרים|איראן|עיראק|תורכיה)'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            entities['locations'].extend(matches)
        
        # Organization patterns
        org_patterns = [
            r'(צה"ל|משטרת ישראל|שב"כ|מוסד|אמ"ן)',
            r'(חמאס|חיזבאללה|פתח|ג\'יהאד אסלאמי)',
            r'(כנסת|ממשלה|בית המשפט העליון)'
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities['organizations'].extend(matches)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get sentence embedding for Hebrew text"""
        if not text:
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        try:
            embedding = self.model.encode(cleaned_text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Create a summary of Hebrew text (basic implementation)"""
        if not text or len(text) <= max_length:
            return text
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return text[:max_length] + "..."
        
        # Take first few sentences that fit within max_length
        summary = ""
        for sentence in sentences:
            if len(summary + sentence + ". ") <= max_length:
                summary += sentence + ". "
            else:
                break
        
        return summary.strip() or text[:max_length] + "..."
    
    def detect_fake_news_indicators(self, text: str) -> bool:
        """Detect potential fake news indicators in Hebrew text"""
        if not text:
            return False
        
        # Hebrew fake news indicators
        fake_indicators = [
            'לא נכון', 'שקר', 'פייק', 'fake', 'שגוי', 'מוטעה', 'לא מדויק',
            'הכחשה', 'תיקון', 'טעות', 'לא אמת', 'דיווח שגוי'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in fake_indicators)