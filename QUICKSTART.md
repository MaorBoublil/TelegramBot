# Quick Start Guide 🚀

Get your Hebrew News Bot up and running in minutes!

## Prerequisites ✅

- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- A Telegram channel where the bot will post news
- Access to Hebrew news channels you want to monitor

## 5-Minute Setup 🕐

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd TelegramBot
python setup.py
```

### 2. Configure Your Bot
Edit the `.env` file with your settings:
```bash
nano .env
```

**Required settings:**
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@your_news_channel
SOURCE_CHANNELS=@channel1,@channel2,@channel3
```

### 3. Run the Bot
```bash
python main.py
```

That's it! Your bot is now monitoring Hebrew news channels. 🎉

## Essential Configuration 📝

### Telegram Setup

1. **Create a Bot:**
   - Message [@BotFather](https://t.me/botfather)
   - Use `/newbot` command
   - Choose a name and username
   - Save the bot token

2. **Create a Channel:**
   - Create a new Telegram channel
   - Add your bot as an admin
   - Get the channel username (e.g., `@mynewschannel`)

3. **Add Source Channels:**
   - Find Hebrew news channels you want to monitor
   - Add their usernames to `SOURCE_CHANNELS` in `.env`

### Key Settings

```env
# Your bot's token from BotFather
TELEGRAM_BOT_TOKEN=your_token_here

# Channel where bot will post news (use @ for usernames or chat ID)
TELEGRAM_CHANNEL_ID=@your_channel

# Channels to monitor (comma-separated)
SOURCE_CHANNELS=@channel1,@channel2,@channel3

# Similarity thresholds (adjust based on your needs)
SIMILARITY_THRESHOLD=0.85    # Higher = stricter duplicate detection
UPDATE_THRESHOLD=0.75        # Lower = more sensitive to updates
```

## Testing Your Setup 🧪

Run the component tests:
```bash
python test_components.py
```

This will verify that all components are working correctly.

## Bot Commands 🤖

Once running, your bot supports these commands:

- `/start` - Welcome message
- `/help` - Detailed help
- `/stats` - View statistics
- `/status` - Check bot status

## How It Works 🔄

1. **Monitoring:** Bot watches your source channels for new messages
2. **Analysis:** Each message is processed for Hebrew content, keywords, and entities
3. **Similarity Check:** Compares with existing posts to detect duplicates/updates
4. **Action:** 
   - **New story** → Posts to your channel
   - **Update** → Edits existing post with new info
   - **Fake news** → Adds warning marker
   - **Duplicate** → Ignores

## Troubleshooting 🔧

### Bot not receiving messages?
- Check if bot has access to source channels
- Verify channel usernames in configuration
- Ensure channels are public or bot is a member

### High similarity threshold causing issues?
- Lower `SIMILARITY_THRESHOLD` (try 0.75-0.80)
- Adjust `UPDATE_THRESHOLD` (try 0.65-0.70)

### Memory issues?
- Reduce number of monitored channels
- Enable database cleanup in configuration

### Check logs:
```bash
tail -f bot.log
```

## Production Deployment 🏭

For production use:

```bash
sudo ./deploy/deploy.sh
```

This sets up:
- System user for the bot
- Systemd service for auto-start
- Log rotation
- Proper permissions

## Support 💬

- Check the full [README.md](README.md) for detailed documentation
- Run `/status` command to verify bot configuration
- Use `LOG_LEVEL=DEBUG` in `.env` for detailed logs

---

**Happy news monitoring! 📰🤖**