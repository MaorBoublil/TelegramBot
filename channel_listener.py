import logging
import httpx
from telethon import TelegramClient, events
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
API_ID = Config.API_ID
API_HASH = Config.API_HASH
SESSION_NAME = Config.SESSION_NAME
SOURCE_CHANNELS = Config.SOURCE_CHANNELS
BOT_WEBHOOK_URL = "http://localhost:8080/new-post"

# Basic validation
if not all([API_ID, API_HASH, SESSION_NAME]):
    raise ValueError("API_ID, API_HASH, and SESSION_NAME must be set in your environment or .env file.")

if not SOURCE_CHANNELS:
    raise ValueError("SOURCE_CHANNELS must be defined in your environment or .env file.")

# Initialize the Telegram Client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handle_new_message(event):
    """Handle new messages from source channels and forward them to the main bot."""
    try:
        channel_username = f"@{event.chat.username}"
        message_text = event.message.text
        message_id = event.message.id
        
        if not message_text:
            logger.info("Received a message with no text content. Skipping.")
            return

        logger.info(f"Forwarding message from {channel_username} (ID: {message_id}) to main bot.")

        payload = {
            "content": message_text,
            "source_channel": channel_username,
            "telegram_message_id": message_id
        }

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(BOT_WEBHOOK_URL, json=payload, timeout=10.0)

        if response.status_code == 200:
            logger.info(f"Successfully forwarded message {message_id} to main bot.")
        else:
            logger.error(f"Failed to forward message {message_id}. Bot returned status {response.status_code}: {response.text}")

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)

async def main():
    """Main function to start the listener."""
    logger.info("Starting channel listener...")
    await client.start()
    
    # Ensure we are connected
    if await client.is_user_authorized():
        logger.info("Client is authorized and listening for messages.")
        # Get the source channel entities to confirm access
        try:
            logger.info("Monitoring the following channels:")
            for channel in SOURCE_CHANNELS:
                logger.info(f"- {channel}")
        except Exception as e:
            logger.error(f"Could not access one or more channels. Please ensure they are correct public channels. Error: {e}")
    else:
        logger.warning("Client is not authorized. Please run interactively first to log in.")

    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Listener stopped by user.")
    except Exception as e:
        logger.error(f"Listener crashed: {e}") 