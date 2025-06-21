#!/usr/bin/env python3
"""
Hebrew News Bot - Advanced AI-powered Telegram news bot
Monitors Hebrew news channels and provides verified summaries
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from aiohttp import web

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from bot.database import NewsDatabase
from bot.news_processor import NewsProcessor
from bot.telegram_bot import HebrewNewsBot
from utils.hebrew_nlp import HebrewNLP
from utils.similarity import SimilarityDetector

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    
    # Reduce noise from some libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)
    logging.getLogger('chromadb').setLevel(logging.WARNING)

def create_data_directories():
    """Create necessary data directories"""
    os.makedirs(Config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
    os.makedirs('logs', exist_ok=True)

def initialize_components():
    """Initialize all bot components"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing Hebrew News Bot components...")
        
        # Initialize Hebrew NLP
        logger.info("Loading Hebrew NLP model...")
        hebrew_nlp = HebrewNLP(Config.HEBREW_MODEL_NAME)
        
        # Initialize similarity detector
        similarity_detector = SimilarityDetector(
            similarity_threshold=Config.SIMILARITY_THRESHOLD,
            update_threshold=Config.UPDATE_THRESHOLD
        )
        
        # Initialize database
        logger.info("Initializing news database...")
        database = NewsDatabase(Config.CHROMA_PERSIST_DIRECTORY)
        
        # Initialize news processor
        news_processor = NewsProcessor(database, hebrew_nlp, similarity_detector)
        
        # Initialize Telegram bot
        logger.info("Initializing Telegram bot...")
        telegram_bot = HebrewNewsBot(news_processor)
        
        logger.info("All components initialized successfully")
        return telegram_bot
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise

async def main():
    """Main function to initialize and run components concurrently."""
    logger = logging.getLogger(__name__)
    
    # Validate config and create directories
    Config.validate()
    logger.info("Configuration validated successfully")
    create_data_directories()
    
    # Initialize components
    bot = initialize_components()
    
    ptb_app = bot.application
    web_app = await bot.get_web_app()
    
    # Setup web server runner
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    
    # Run both applications concurrently
    logger.info("Starting Telegram Bot and Web Server...")
    
    await ptb_app.initialize()
    await site.start()
    await ptb_app.start()
    await ptb_app.updater.start_polling()
    
    # Keep the main function alive to wait for termination signals
    await asyncio.Event().wait()
    
    # Cleanup logic (will be called by shutdown signal)
    logger.info("Shutting down...")
    await ptb_app.updater.stop()
    await ptb_app.stop()
    await runner.cleanup()

def run_bot():
    """Entry point for running the bot"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("Hebrew News Bot Starting")
    logger.info("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_bot()