import chromadb
from chromadb.config import Settings
import uuid
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class NewsDatabase:
    def __init__(self, persist_directory: str):
        """Initialize ChromaDB for news storage"""
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection for news posts
        self.collection = self.client.get_or_create_collection(
            name="hebrew_news",
            metadata={"description": "Hebrew news posts with embeddings"}
        )
        
        logger.info(f"Initialized news database at {persist_directory}")
    
    def add_post(self, 
                 content: str,
                 source_channel: str,
                 timestamp: datetime,
                 embedding: np.ndarray,
                 keywords: List[str],
                 entities: Dict[str, List[str]],
                 summary: str = "",
                 telegram_message_id: Optional[int] = None,
                 published_message_id: Optional[int] = None) -> str:
        """Add a new news post to the database"""
        
        post_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            "source_channel": source_channel,
            "timestamp": timestamp.isoformat(),
            "keywords": json.dumps(keywords, ensure_ascii=False),
            "entities": json.dumps(entities, ensure_ascii=False),
            "summary": summary,
            "telegram_message_id": telegram_message_id or 0,
            "published_message_id": published_message_id or 0,
            "is_fake": False,
            "update_count": 0,
            "created_at": datetime.now().isoformat()
        }
        
        try:
            # Add to ChromaDB
            self.collection.add(
                ids=[post_id],
                embeddings=[embedding.tolist()],
                documents=[content],
                metadatas=[metadata]
            )
            
            logger.info(f"Added new post {post_id} from {source_channel}")
            return post_id
            
        except Exception as e:
            logger.error(f"Error adding post to database: {e}")
            raise
    
    def update_post(self, 
                   post_id: str, 
                   new_content: str = None,
                   new_embedding: np.ndarray = None,
                   new_keywords: List[str] = None,
                   new_entities: Dict[str, List[str]] = None,
                   new_summary: str = None,
                   is_fake: bool = None,
                   published_message_id: int = None) -> bool:
        """Update an existing post"""
        
        try:
            # Get current post
            result = self.collection.get(ids=[post_id], include=['metadatas', 'documents'])
            
            if not result['ids']:
                logger.warning(f"Post {post_id} not found for update")
                return False
            
            current_metadata = result['metadatas'][0]
            current_document = result['documents'][0]
            
            # Prepare updates
            updated_metadata = current_metadata.copy()
            updated_document = current_document
            updated_embedding = None
            
            if new_content is not None:
                updated_document = new_content
            
            if new_embedding is not None:
                updated_embedding = new_embedding.tolist()
            
            if new_keywords is not None:
                updated_metadata['keywords'] = json.dumps(new_keywords, ensure_ascii=False)
            
            if new_entities is not None:
                updated_metadata['entities'] = json.dumps(new_entities, ensure_ascii=False)
            
            if new_summary is not None:
                updated_metadata['summary'] = new_summary
            
            if is_fake is not None:
                updated_metadata['is_fake'] = is_fake
            
            if published_message_id is not None:
                updated_metadata['published_message_id'] = published_message_id
            
            # Increment update count
            updated_metadata['update_count'] = updated_metadata.get('update_count', 0) + 1
            updated_metadata['last_updated'] = datetime.now().isoformat()
            
            # Update in ChromaDB
            update_params = {
                'ids': [post_id],
                'documents': [updated_document],
                'metadatas': [updated_metadata]
            }
            
            if updated_embedding is not None:
                update_params['embeddings'] = [updated_embedding]
            
            self.collection.update(**update_params)
            
            logger.info(f"Updated post {post_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {e}")
            return False
    
    def search_similar_posts(self, 
                           embedding: np.ndarray, 
                           n_results: int = 10,
                           where_filter: Dict = None) -> List[Dict]:
        """Search for similar posts using embedding similarity"""
        
        try:
            query_params = {
                'query_embeddings': [embedding.tolist()],
                'n_results': n_results,
                'include': ['documents', 'metadatas', 'distances']
            }
            
            if where_filter:
                query_params['where'] = where_filter
            
            results = self.collection.query(**query_params)
            
            # Format results
            similar_posts = []
            for i in range(len(results['ids'][0])):
                post = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                }
                
                # Parse JSON fields in metadata
                if 'keywords' in post['metadata']:
                    try:
                        post['metadata']['keywords'] = json.loads(post['metadata']['keywords'])
                    except:
                        post['metadata']['keywords'] = []
                
                if 'entities' in post['metadata']:
                    try:
                        post['metadata']['entities'] = json.loads(post['metadata']['entities'])
                    except:
                        post['metadata']['entities'] = {}
                
                similar_posts.append(post)
            
            return similar_posts
            
        except Exception as e:
            logger.error(f"Error searching similar posts: {e}")
            return []
    
    def get_post_by_id(self, post_id: str) -> Optional[Dict]:
        """Get a specific post by ID"""
        
        try:
            result = self.collection.get(
                ids=[post_id],
                include=['documents', 'metadatas', 'embeddings']
            )
            
            if not result['ids']:
                return None
            
            post = {
                'id': result['ids'][0],
                'content': result['documents'][0],
                'metadata': result['metadatas'][0],
                'embedding': np.array(result['embeddings'][0])
            }
            
            # Parse JSON fields
            if 'keywords' in post['metadata']:
                try:
                    post['metadata']['keywords'] = json.loads(post['metadata']['keywords'])
                except:
                    post['metadata']['keywords'] = []
            
            if 'entities' in post['metadata']:
                try:
                    post['metadata']['entities'] = json.loads(post['metadata']['entities'])
                except:
                    post['metadata']['entities'] = {}
            
            return post
            
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            return None
    
    def get_recent_posts(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """Get recent posts within specified hours"""
        
        try:
            # Calculate timestamp threshold
            from datetime import timedelta
            threshold = datetime.now() - timedelta(hours=hours)
            
            # Get all posts (ChromaDB doesn't support date filtering directly)
            result = self.collection.get(
                include=['documents', 'metadatas'],
                limit=limit
            )
            
            recent_posts = []
            for i in range(len(result['ids'])):
                metadata = result['metadatas'][i]
                post_time = datetime.fromisoformat(metadata.get('timestamp', '1970-01-01'))
                
                if post_time >= threshold:
                    post = {
                        'id': result['ids'][i],
                        'content': result['documents'][i],
                        'metadata': metadata
                    }
                    
                    # Parse JSON fields
                    if 'keywords' in metadata:
                        try:
                            post['metadata']['keywords'] = json.loads(metadata['keywords'])
                        except:
                            post['metadata']['keywords'] = []
                    
                    if 'entities' in metadata:
                        try:
                            post['metadata']['entities'] = json.loads(metadata['entities'])
                        except:
                            post['metadata']['entities'] = {}
                    
                    recent_posts.append(post)
            
            # Sort by timestamp (newest first)
            recent_posts.sort(
                key=lambda x: x['metadata'].get('timestamp', '1970-01-01'),
                reverse=True
            )
            
            return recent_posts
            
        except Exception as e:
            logger.error(f"Error getting recent posts: {e}")
            return []
    
    def delete_post(self, post_id: str) -> bool:
        """Delete a post from the database"""
        
        try:
            self.collection.delete(ids=[post_id])
            logger.info(f"Deleted post {post_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        
        try:
            count = self.collection.count()
            
            # Get recent activity
            recent_posts = self.get_recent_posts(hours=24)
            recent_count = len(recent_posts)
            
            # Count fake news posts
            all_posts = self.collection.get(include=['metadatas'])
            fake_count = sum(1 for metadata in all_posts['metadatas'] 
                           if metadata.get('is_fake', False))
            
            return {
                'total_posts': count,
                'recent_posts_24h': recent_count,
                'fake_news_count': fake_count,
                'database_path': self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_posts(self, days: int = 30) -> int:
        """Clean up posts older than specified days"""
        
        try:
            from datetime import timedelta
            threshold = datetime.now() - timedelta(days=days)
            
            # Get all posts
            result = self.collection.get(include=['metadatas'])
            
            old_post_ids = []
            for i, metadata in enumerate(result['metadatas']):
                post_time = datetime.fromisoformat(metadata.get('timestamp', '1970-01-01'))
                if post_time < threshold:
                    old_post_ids.append(result['ids'][i])
            
            # Delete old posts
            if old_post_ids:
                self.collection.delete(ids=old_post_ids)
                logger.info(f"Cleaned up {len(old_post_ids)} old posts")
            
            return len(old_post_ids)
            
        except Exception as e:
            logger.error(f"Error cleaning up old posts: {e}")
            return 0