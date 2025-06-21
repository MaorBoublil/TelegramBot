import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    # Telegram Client API (for listening to public channels)
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_listener')

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
    
    # Source channels to monitor
    SOURCE_CHANNELS = [
        channel.strip() 
        for channel in os.getenv('SOURCE_CHANNELS', '').split(',') 
        if channel.strip()
    ]
    
    # Vector Database Configuration
    CHROMA_PERSIST_DIRECTORY = os.getenv('CHROMA_PERSIST_DIRECTORY', './data/chroma_db')
    
    # Similarity Thresholds
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.85'))
    UPDATE_THRESHOLD = float(os.getenv('UPDATE_THRESHOLD', '0.75'))
    
    # Hebrew NLP Model
    HEBREW_MODEL_NAME = os.getenv('HEBREW_MODEL_NAME', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    # Bot Settings
    MAX_POST_LENGTH = int(os.getenv('MAX_POST_LENGTH', '4096'))
    FAKE_NEWS_MARKER = os.getenv('FAKE_NEWS_MARKER', 'ייתכן ומדובר בפייק')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not cls.TELEGRAM_CHANNEL_ID:
            raise ValueError("TELEGRAM_CHANNEL_ID is required")
        if not cls.SOURCE_CHANNELS:
            raise ValueError("At least one SOURCE_CHANNEL is required")
        # No validation for API_ID and API_HASH as they are for the standalone listener
        return True