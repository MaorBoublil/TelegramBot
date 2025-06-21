import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio

from utils.hebrew_nlp import HebrewNLP
from utils.similarity import SimilarityDetector
from bot.database import NewsDatabase
from config import Config

logger = logging.getLogger(__name__)

class NewsProcessor:
    def __init__(self, database: NewsDatabase, hebrew_nlp: HebrewNLP, similarity_detector: SimilarityDetector):
        """Initialize news processor with required components"""
        self.database = database
        self.hebrew_nlp = hebrew_nlp
        self.similarity_detector = similarity_detector
        
        logger.info("News processor initialized")
    
    async def process_new_post(self, 
                             content: str, 
                             source_channel: str, 
                             telegram_message_id: int,
                             timestamp: datetime = None) -> Dict:
        """Process a new incoming post and determine action"""
        
        if timestamp is None:
            timestamp = datetime.now()
        
        logger.info(f"Processing new post from {source_channel}")
        
        try:
            # Clean and analyze the content
            cleaned_content = self.hebrew_nlp.clean_text(content)
            if not cleaned_content:
                logger.warning("Empty content after cleaning")
                return {"action": "skip", "reason": "empty_content"}
            
            # Extract features
            keywords = self.hebrew_nlp.extract_keywords(cleaned_content)
            entities = self.hebrew_nlp.extract_entities(cleaned_content)
            embedding = self.hebrew_nlp.get_embedding(cleaned_content)
            summary = self.hebrew_nlp.summarize_text(cleaned_content)
            
            # Check for fake news indicators
            is_fake_indicator = self.hebrew_nlp.detect_fake_news_indicators(cleaned_content)
            
            logger.debug(f"Extracted {len(keywords)} keywords, {sum(len(v) for v in entities.values())} entities")
            
            # Search for similar existing posts
            similar_posts = self.database.search_similar_posts(embedding, n_results=10)
            
            if not similar_posts:
                # No similar posts found - this is a new story
                return await self._handle_new_story(
                    cleaned_content, source_channel, timestamp, embedding,
                    keywords, entities, summary, telegram_message_id
                )
            
            # Find the most similar post
            best_match, best_similarity = self.similarity_detector.find_most_similar(
                embedding, keywords, entities,
                [{
                    'embedding': post.get('embedding', embedding),
                    'keywords': post['metadata'].get('keywords', []),
                    'entities': post['metadata'].get('entities', {})
                } for post in similar_posts]
            )
            
            if best_match is None:
                # No good match found
                return await self._handle_new_story(
                    cleaned_content, source_channel, timestamp, embedding,
                    keywords, entities, summary, telegram_message_id
                )
            
            # Get the corresponding post from similar_posts
            best_post = similar_posts[0]  # They should be in the same order
            for post in similar_posts:
                if (post.get('embedding') is not None and 
                    best_match.get('embedding') is not None):
                    # Compare embeddings to find the right post
                    if self.similarity_detector.calculate_cosine_similarity(
                        post.get('embedding', embedding), 
                        best_match.get('embedding', embedding)
                    ) > 0.99:
                        best_post = post
                        break
            
            relationship = self.similarity_detector.classify_relationship(best_similarity)
            
            logger.info(f"Best match similarity: {best_similarity:.3f}, relationship: {relationship}")
            
            if relationship == "duplicate":
                return await self._handle_duplicate(best_post, cleaned_content, is_fake_indicator)
            
            elif relationship == "update":
                return await self._handle_update(
                    best_post, cleaned_content, source_channel, timestamp,
                    embedding, keywords, entities, summary, telegram_message_id, is_fake_indicator
                )
            
            else:
                # Similarity too low - treat as new story
                return await self._handle_new_story(
                    cleaned_content, source_channel, timestamp, embedding,
                    keywords, entities, summary, telegram_message_id
                )
        
        except Exception as e:
            logger.error(f"Error processing post: {e}")
            return {"action": "error", "error": str(e)}
    
    async def _handle_new_story(self, 
                              content: str, 
                              source_channel: str, 
                              timestamp: datetime,
                              embedding, 
                              keywords: List[str], 
                              entities: Dict, 
                              summary: str,
                              telegram_message_id: int) -> Dict:
        """Handle a completely new news story"""
        
        try:
            # Add to database
            post_id = self.database.add_post(
                content=content,
                source_channel=source_channel,
                timestamp=timestamp,
                embedding=embedding,
                keywords=keywords,
                entities=entities,
                summary=summary,
                telegram_message_id=telegram_message_id
            )
            
            logger.info(f"Created new story: {post_id}")
            
            return {
                "action": "publish_new",
                "post_id": post_id,
                "content": content,
                "summary": summary,
                "keywords": keywords,
                "entities": entities
            }
        
        except Exception as e:
            logger.error(f"Error handling new story: {e}")
            return {"action": "error", "error": str(e)}
    
    async def _handle_duplicate(self, existing_post: Dict, new_content: str, is_fake_indicator: bool) -> Dict:
        """Handle a duplicate post"""
        
        logger.info(f"Handling duplicate for post {existing_post['id']}")
        
        if is_fake_indicator:
            # This might be a fake news correction
            return await self._handle_fake_news_correction(existing_post, new_content)
        
        # Regular duplicate - no action needed
        return {
            "action": "skip_duplicate",
            "existing_post_id": existing_post['id'],
            "reason": "duplicate_content"
        }
    
    async def _handle_update(self, 
                           existing_post: Dict, 
                           new_content: str, 
                           source_channel: str,
                           timestamp: datetime,
                           embedding, 
                           keywords: List[str], 
                           entities: Dict, 
                           summary: str,
                           telegram_message_id: int,
                           is_fake_indicator: bool) -> Dict:
        """Handle an update to existing post"""
        
        logger.info(f"Handling update for post {existing_post['id']}")
        
        if is_fake_indicator:
            # This might be a fake news correction
            return await self._handle_fake_news_correction(existing_post, new_content)
        
        # Determine what kind of update this is
        existing_content = existing_post['content']
        
        # Check if new content has significantly more information
        if len(new_content) > len(existing_content) * 1.2:  # 20% more content
            # Significant new information
            updated_content = await self._merge_content(existing_content, new_content)
            
            # Update in database
            success = self.database.update_post(
                post_id=existing_post['id'],
                new_content=updated_content,
                new_embedding=embedding,
                new_keywords=keywords,
                new_entities=entities,
                new_summary=summary
            )
            
            if success:
                return {
                    "action": "update_post",
                    "post_id": existing_post['id'],
                    "updated_content": updated_content,
                    "original_content": existing_content,
                    "published_message_id": existing_post['metadata'].get('published_message_id')
                }
        
        # Minor update or no significant new information
        return {
            "action": "skip_minor_update",
            "existing_post_id": existing_post['id'],
            "reason": "insufficient_new_information"
        }
    
    async def _handle_fake_news_correction(self, existing_post: Dict, correction_content: str) -> Dict:
        """Handle fake news correction"""
        
        logger.info(f"Handling fake news correction for post {existing_post['id']}")
        
        # Mark as fake in database
        success = self.database.update_post(
            post_id=existing_post['id'],
            is_fake=True
        )
        
        if success:
            return {
                "action": "mark_fake",
                "post_id": existing_post['id'],
                "original_content": existing_post['content'],
                "correction_content": correction_content,
                "published_message_id": existing_post['metadata'].get('published_message_id'),
                "fake_marker": Config.FAKE_NEWS_MARKER
            }
        
        return {"action": "error", "error": "Failed to mark as fake"}
    
    async def _merge_content(self, existing_content: str, new_content: str) -> str:
        """Intelligently merge existing and new content"""
        
        # Simple merge strategy - can be improved with more sophisticated NLP
        
        # If new content is much longer, it might contain the old content
        if new_content.find(existing_content[:100]) != -1:
            # New content contains old content
            return new_content
        
        # If old content is much longer, append new info
        if len(existing_content) > len(new_content):
            return f"{existing_content}\n\n--- עדכון ---\n{new_content}"
        
        # Default: replace with new content if it's significantly different
        return new_content
    
    async def get_post_for_publishing(self, post_id: str) -> Optional[Dict]:
        """Get a post formatted for publishing"""
        
        post = self.database.get_post_by_id(post_id)
        if not post:
            return None
        
        # Format for Telegram
        content = post['content']
        metadata = post['metadata']
        
        # Add source attribution if needed
        if metadata.get('source_channel'):
            content += f"\n\n📰 מקור: {metadata['source_channel']}"
        
        # Ensure content fits Telegram limits
        if len(content) > Config.MAX_POST_LENGTH:
            content = content[:Config.MAX_POST_LENGTH - 3] + "..."
        
        return {
            "content": content,
            "post_id": post_id,
            "metadata": metadata
        }
    
    async def mark_post_published(self, post_id: str, published_message_id: int) -> bool:
        """Mark a post as published with the Telegram message ID"""
        
        return self.database.update_post(
            post_id=post_id,
            published_message_id=published_message_id
        )
    
    async def get_statistics(self) -> Dict:
        """Get processing statistics"""
        
        db_stats = self.database.get_stats()
        
        return {
            "database": db_stats,
            "processor": {
                "similarity_threshold": self.similarity_detector.similarity_threshold,
                "update_threshold": self.similarity_detector.update_threshold
            }
        }