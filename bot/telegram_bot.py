import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
from aiohttp import web

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
        self.application.post_init = self.post_init
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
        
        # Message handler for direct interaction (if any)
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
        """Handle incoming messages from users"""
        
        message = update.message
        content = message.text or message.caption
        if not message or not content:
            return
        
        # We can add logic here for direct messages to the bot if needed.
        logger.info(f"Received direct message from {message.chat.id}, ignoring.")
        # For now, let's just log it. If the bot were in a group, this would handle group messages.
        await update.message.reply_text("🤖: איני מנהל שיחות פרטיות, אך אני זמין לפקודות כמו /start ו-/help.")
    
    async def post_init(self, application: Application):
        pass

    async def handle_new_post_request(self, request: web.Request):
        """Handle new post received from the listener via HTTP."""
        try:
            data = await request.json()
            content = data.get('content')
            source_channel = data.get('source_channel')
            telegram_message_id = data.get('telegram_message_id')
            
            if not all([content, source_channel, telegram_message_id]):
                logger.error("Invalid data received from listener: 'content', 'source_channel', and 'telegram_message_id' are required.")
                return web.Response(status=400, text="Invalid data")

            logger.info(f"Received post from listener for channel: {source_channel}")
            
            timestamp = datetime.now(timezone.utc)

            result = await self.news_processor.process_new_post(
                content=content,
                source_channel=source_channel,
                telegram_message_id=telegram_message_id,
                timestamp=timestamp
            )
            
            await self._handle_processing_result(result)
            return web.Response(status=200, text="OK")

        except json.JSONDecodeError:
            logger.error("Listener sent invalid JSON.")
            return web.Response(status=400, text="Invalid JSON")
        except Exception as e:
            logger.error(f"Error processing post from listener: {e}", exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

    async def get_web_app(self) -> web.Application:
        """Create and return the aiohttp web application."""
        app = web.Application()
        app.router.add_post('/new-post', self.handle_new_post_request)
        logger.info("Web server routes configured for endpoint /new-post")
        return app

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
    
    def start_monitoring(self):
        """Start the bot and begin monitoring"""
        logger.info("Starting Hebrew News Bot...")
        
        logger.info("Bot is now running and monitoring channels")
        self.application.run_polling()