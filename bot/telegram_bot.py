import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
from telegram.error import TelegramError

from bot.news_processor import NewsProcessor
from config import Config

logger = logging.getLogger(__name__)

class HebrewNewsBot:
    def __init__(self, news_processor: NewsProcessor):
        """Initialize the Telegram bot"""
        self.news_processor = news_processor
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.channel_id = Config.TELEGRAM_CHANNEL_ID
        self.source_channels = Config.SOURCE_CHANNELS
        
        # Initialize bot application
        self.application = Application.builder().token(self.bot_token).build()
        self.bot = self.application.bot
        
        # Setup handlers
        self._setup_handlers()
        
        logger.info(f"Hebrew News Bot initialized for channel {self.channel_id}")
        logger.info(f"Monitoring {len(self.source_channels)} source channels")
    
    def _setup_handlers(self):
        """Setup message and command handlers"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Message handler for monitoring channels
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 ברוכים הבאים לבוט החדשות העברי המתקדם!

הבוט מנטר ערוצי חדשות ומספק סיכומים מעודכנים ומאומתים בעברית.

פקודות זמינות:
/help - עזרה ומידע
/stats - סטטיסטיקות
/status - מצב הבוט

הבוט פועל באופן אוטומטי ומפרסם עדכונים בערוץ.
        """
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📖 מדריך שימוש בבוט החדשות העברי

🔍 תכונות עיקריות:
• ניטור ערוצי חדשות בזמן אמת
• זיהוי כפילויות וחדשות דומות
• עדכון פוסטים עם מידע חדש
• זיהוי חדשות מזויפות
• סיכומים בעברית

⚙️ פקודות:
/start - התחלת השיחה
/help - מדריך זה
/stats - סטטיסטיקות מפורטות
/status - בדיקת מצב הבוט

🎯 הבוט עובד באופן אוטומטי ומפרסם עדכונים בערוץ הייעודי.
        """
        
        await update.message.reply_text(help_message)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        try:
            stats = await self.news_processor.get_statistics()
            
            stats_message = f"""
📊 סטטיסטיקות בוט החדשות

📰 מסד נתונים:
• סה"כ פוסטים: {stats['database'].get('total_posts', 0)}
• פוסטים ב-24 שעות: {stats['database'].get('recent_posts_24h', 0)}
• חדשות מזויפות: {stats['database'].get('fake_news_count', 0)}

⚙️ הגדרות עיבוד:
• סף דמיון לכפילות: {stats['processor']['similarity_threshold']:.2%}
• סף דמיון לעדכונים: {stats['processor']['update_threshold']:.2%}

📡 ערוצי מקור: {len(self.source_channels)}
            """
            
            await update.message.reply_text(stats_message)
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text("❌ שגיאה בקבלת סטטיסטיקות")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            # Check bot status
            bot_info = await self.bot.get_me()
            
            status_message = f"""
🟢 מצב הבוט: פעיל

🤖 פרטי בוט:
• שם: {bot_info.first_name}
• שם משתמש: @{bot_info.username}
• ID: {bot_info.id}

📡 ערוצי ניטור:
{chr(10).join(f"• {channel}" for channel in self.source_channels)}

📢 ערוץ פרסום: {self.channel_id}

⏰ זמן בדיקה: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await update.message.reply_text(status_message)
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            await update.message.reply_text("❌ שגיאה בבדיקת מצב הבוט")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages from monitored channels"""
        
        message = update.message
        if not message or not message.text:
            return
        
        # Check if message is from a monitored channel
        chat = message.chat
        channel_username = f"@{chat.username}" if chat.username else str(chat.id)
        
        if channel_username not in self.source_channels and str(chat.id) not in self.source_channels:
            logger.debug(f"Ignoring message from non-monitored channel: {channel_username}")
            return
        
        logger.info(f"Processing message from {channel_username}")
        
        try:
            # Process the news post
            result = await self.news_processor.process_new_post(
                content=message.text,
                source_channel=channel_username,
                telegram_message_id=message.message_id,
                timestamp=message.date
            )
            
            # Handle the result
            await self._handle_processing_result(result)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _handle_processing_result(self, result: Dict):
        """Handle the result from news processing"""
        
        action = result.get("action")
        
        if action == "publish_new":
            await self._publish_new_post(result)
        
        elif action == "update_post":
            await self._update_existing_post(result)
        
        elif action == "mark_fake":
            await self._mark_post_as_fake(result)
        
        elif action in ["skip_duplicate", "skip_minor_update"]:
            logger.info(f"Skipped: {result.get('reason', 'unknown')}")
        
        elif action == "error":
            logger.error(f"Processing error: {result.get('error', 'unknown')}")
        
        else:
            logger.warning(f"Unknown action: {action}")
    
    async def _publish_new_post(self, result: Dict):
        """Publish a new post to the channel"""
        
        try:
            post_data = await self.news_processor.get_post_for_publishing(result["post_id"])
            if not post_data:
                logger.error("Failed to get post data for publishing")
                return
            
            # Send message to channel
            sent_message = await self.bot.send_message(
                chat_id=self.channel_id,
                text=post_data["content"],
                parse_mode='HTML'
            )
            
            # Update database with published message ID
            await self.news_processor.mark_post_published(
                result["post_id"], 
                sent_message.message_id
            )
            
            logger.info(f"Published new post {result['post_id']} as message {sent_message.message_id}")
            
        except TelegramError as e:
            logger.error(f"Telegram error publishing post: {e}")
        except Exception as e:
            logger.error(f"Error publishing new post: {e}")
    
    async def _update_existing_post(self, result: Dict):
        """Update an existing post in the channel"""
        
        try:
            published_message_id = result.get("published_message_id")
            if not published_message_id:
                logger.warning("No published message ID for update")
                return
            
            post_data = await self.news_processor.get_post_for_publishing(result["post_id"])
            if not post_data:
                logger.error("Failed to get updated post data")
                return
            
            # Edit the existing message
            await self.bot.edit_message_text(
                chat_id=self.channel_id,
                message_id=published_message_id,
                text=post_data["content"],
                parse_mode='HTML'
            )
            
            logger.info(f"Updated post {result['post_id']} (message {published_message_id})")
            
        except TelegramError as e:
            if "message is not modified" in str(e).lower():
                logger.info("Message content unchanged, no update needed")
            else:
                logger.error(f"Telegram error updating post: {e}")
        except Exception as e:
            logger.error(f"Error updating post: {e}")
    
    async def _mark_post_as_fake(self, result: Dict):
        """Mark a post as fake news"""
        
        try:
            published_message_id = result.get("published_message_id")
            if not published_message_id:
                logger.warning("No published message ID for fake marking")
                return
            
            # Add fake news marker to the original content
            original_content = result.get("original_content", "")
            fake_marker = result.get("fake_marker", Config.FAKE_NEWS_MARKER)
            
            updated_content = f"{original_content}\n\n⚠️ {fake_marker}"
            
            # Ensure content fits Telegram limits
            if len(updated_content) > Config.MAX_POST_LENGTH:
                # Truncate original content to make room for marker
                max_original = Config.MAX_POST_LENGTH - len(f"\n\n⚠️ {fake_marker}") - 3
                updated_content = f"{original_content[:max_original]}...\n\n⚠️ {fake_marker}"
            
            # Edit the message
            await self.bot.edit_message_text(
                chat_id=self.channel_id,
                message_id=published_message_id,
                text=updated_content,
                parse_mode='HTML'
            )
            
            logger.info(f"Marked post {result['post_id']} as fake news")
            
        except TelegramError as e:
            logger.error(f"Telegram error marking fake: {e}")
        except Exception as e:
            logger.error(f"Error marking post as fake: {e}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
    
    async def start_monitoring(self):
        """Start the bot and begin monitoring"""
        logger.info("Starting Hebrew News Bot...")
        
        try:
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            
            # Start polling
            await self.application.updater.start_polling()
            
            logger.info("Bot is now running and monitoring channels")
            
            # Keep the bot running
            await self.application.updater.idle()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            # Cleanup
            await self.application.stop()
    
    async def stop_monitoring(self):
        """Stop the bot"""
        logger.info("Stopping Hebrew News Bot...")
        
        try:
            await self.application.stop()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    def run(self):
        """Run the bot (blocking)"""
        try:
            asyncio.run(self.start_monitoring())
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            raise