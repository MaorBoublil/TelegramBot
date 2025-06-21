#!/usr/bin/env python3
"""
Test script for Hebrew News Bot components
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_hebrew_nlp():
    """Test Hebrew NLP functionality"""
    print("🧪 Testing Hebrew NLP...")
    
    try:
        from utils.hebrew_nlp import HebrewNLP
        
        # Use a lightweight model for testing
        nlp = HebrewNLP("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        
        # Test Hebrew text
        test_text = "ראש הממשלה נתניהו נפגש היום עם נשיא ארצות הברית בירושלים לדיון על המצב הביטחוני באזור"
        
        # Test text cleaning
        cleaned = nlp.clean_text(test_text)
        print(f"✅ Text cleaning: {len(cleaned)} characters")
        
        # Test keyword extraction
        keywords = nlp.extract_keywords(test_text)
        print(f"✅ Keywords extracted: {len(keywords)} keywords")
        print(f"   Keywords: {', '.join(keywords[:5])}")
        
        # Test entity extraction
        entities = nlp.extract_entities(test_text)
        print(f"✅ Entities extracted: {sum(len(v) for v in entities.values())} entities")
        
        # Test embedding generation
        embedding = nlp.get_embedding(test_text)
        print(f"✅ Embedding generated: shape {embedding.shape}")
        
        # Test summarization
        summary = nlp.summarize_text(test_text, max_length=50)
        print(f"✅ Summarization: {len(summary)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Hebrew NLP test failed: {e}")
        return False

def test_similarity_detector():
    """Test similarity detection"""
    print("\n🧪 Testing Similarity Detector...")
    
    try:
        from utils.similarity import SimilarityDetector
        import numpy as np
        
        detector = SimilarityDetector()
        
        # Test embeddings
        emb1 = np.random.rand(384)
        emb2 = np.random.rand(384)
        emb3 = emb1 + np.random.rand(384) * 0.1  # Similar to emb1
        
        # Test cosine similarity
        sim1 = detector.calculate_cosine_similarity(emb1, emb2)
        sim2 = detector.calculate_cosine_similarity(emb1, emb3)
        print(f"✅ Cosine similarity: random={sim1:.3f}, similar={sim2:.3f}")
        
        # Test keyword similarity
        keywords1 = ["ירושלים", "נתניהו", "ביטחון"]
        keywords2 = ["תל אביב", "גנץ", "כלכלה"]
        keywords3 = ["ירושלים", "נתניהו", "מדיניות"]
        
        kw_sim1 = detector.calculate_keyword_similarity(keywords1, keywords2)
        kw_sim2 = detector.calculate_keyword_similarity(keywords1, keywords3)
        print(f"✅ Keyword similarity: different={kw_sim1:.3f}, similar={kw_sim2:.3f}")
        
        # Test classification
        classification = detector.classify_relationship(0.9)
        print(f"✅ Relationship classification: {classification}")
        
        return True
        
    except Exception as e:
        print(f"❌ Similarity detector test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\n🧪 Testing Database...")
    
    try:
        from bot.database import NewsDatabase
        from datetime import datetime
        import numpy as np
        
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            db = NewsDatabase(temp_dir)
            
            # Test adding a post
            test_embedding = np.random.rand(384)
            test_keywords = ["ירושלים", "חדשות"]
            test_entities = {"locations": ["ירושלים"], "organizations": ["כנסת"]}
            
            post_id = db.add_post(
                content="זהו פוסט בדיקה",
                source_channel="@test_channel",
                timestamp=datetime.now(),
                embedding=test_embedding,
                keywords=test_keywords,
                entities=test_entities,
                summary="סיכום בדיקה"
            )
            
            print(f"✅ Post added with ID: {post_id}")
            
            # Test retrieving the post
            retrieved_post = db.get_post_by_id(post_id)
            if retrieved_post:
                print(f"✅ Post retrieved successfully")
            else:
                print(f"❌ Failed to retrieve post")
                return False
            
            # Test similarity search
            similar_posts = db.search_similar_posts(test_embedding, n_results=5)
            print(f"✅ Similarity search returned {len(similar_posts)} results")
            
            # Test statistics
            stats = db.get_stats()
            print(f"✅ Database stats: {stats['total_posts']} posts")
            
            return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_news_processor():
    """Test news processor"""
    print("\n🧪 Testing News Processor...")
    
    try:
        from bot.news_processor import NewsProcessor
        from bot.database import NewsDatabase
        from utils.hebrew_nlp import HebrewNLP
        from utils.similarity import SimilarityDetector
        from datetime import datetime
        
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize components
            nlp = HebrewNLP("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            detector = SimilarityDetector()
            db = NewsDatabase(temp_dir)
            processor = NewsProcessor(db, nlp, detector)
            
            # Test processing a new post
            test_content = "ראש הממשלה הודיע על מדיניות חדשה בתחום הביטחון"
            
            result = await processor.process_new_post(
                content=test_content,
                source_channel="@test_channel",
                telegram_message_id=123,
                timestamp=datetime.now()
            )
            
            print(f"✅ News processing result: {result['action']}")
            
            # Test processing a similar post (should be detected as duplicate/update)
            similar_content = "ראש הממשלה נתניהו הודיע היום על מדיניות ביטחונית חדשה"
            
            result2 = await processor.process_new_post(
                content=similar_content,
                source_channel="@test_channel",
                telegram_message_id=124,
                timestamp=datetime.now()
            )
            
            print(f"✅ Similar post processing result: {result2['action']}")
            
            # Test statistics
            stats = await processor.get_statistics()
            print(f"✅ Processor statistics retrieved")
            
            return True
        
    except Exception as e:
        print(f"❌ News processor test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n🧪 Testing Configuration...")
    
    try:
        # Create a temporary .env file for testing
        test_env_content = """
TELEGRAM_BOT_TOKEN=test_token
TELEGRAM_CHANNEL_ID=@test_channel
SOURCE_CHANNELS=@channel1,@channel2
SIMILARITY_THRESHOLD=0.85
UPDATE_THRESHOLD=0.75
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(test_env_content)
            temp_env_path = f.name
        
        try:
            # Temporarily set environment variables
            os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
            os.environ['TELEGRAM_CHANNEL_ID'] = '@test_channel'
            os.environ['SOURCE_CHANNELS'] = '@channel1,@channel2'
            
            from config import Config
            
            # Test configuration loading
            print(f"✅ Bot token loaded: {Config.TELEGRAM_BOT_TOKEN[:10]}...")
            print(f"✅ Channel ID: {Config.TELEGRAM_CHANNEL_ID}")
            print(f"✅ Source channels: {len(Config.SOURCE_CHANNELS)} channels")
            print(f"✅ Similarity threshold: {Config.SIMILARITY_THRESHOLD}")
            
            # Test validation
            Config.validate()
            print(f"✅ Configuration validation passed")
            
            return True
            
        finally:
            # Cleanup
            os.unlink(temp_env_path)
            # Remove test environment variables
            for key in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID', 'SOURCE_CHANNELS']:
                os.environ.pop(key, None)
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Hebrew News Bot Component Tests")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Hebrew NLP", test_hebrew_nlp),
        ("Similarity Detector", test_similarity_detector),
        ("Database", test_database),
        ("News Processor", test_news_processor)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_function in tests:
        try:
            if asyncio.iscoroutinefunction(test_function):
                result = await test_function()
            else:
                result = test_function()
            
            if result:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed! The bot components are working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)