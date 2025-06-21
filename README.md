# Hebrew News Bot 🤖📰

An advanced AI-powered Telegram bot that monitors Hebrew news channels and provides verified, up-to-date summaries. The bot uses semantic similarity detection to identify duplicate content, updates existing posts with new information, and flags potentially fake news.

## Features 🚀

### Core Functionality
- **Real-time Monitoring**: Continuously monitors specified Telegram news channels
- **Hebrew Language Processing**: Advanced NLP specifically designed for Hebrew text
- **Semantic Similarity Detection**: Uses AI embeddings to identify related content
- **Smart Content Management**: Automatically handles duplicates, updates, and corrections
- **Fake News Detection**: Identifies and flags potentially false information

### Key Capabilities
- ✅ **New Story Detection**: Publishes completely new news stories
- 🔄 **Content Updates**: Merges new information into existing posts
- ⚠️ **Fake News Flagging**: Marks posts with "ייתכן ומדובר בפייק" when corrections are detected
- 📊 **Vector Database Storage**: Efficient storage and retrieval using ChromaDB
- 🎯 **Hebrew-Optimized**: All processing and output in Hebrew

## Architecture 🏗️

```
Hebrew News Bot
├── main.py                 # Entry point
├── config.py              # Configuration management
├── bot/
│   ├── telegram_bot.py    # Telegram bot interface
│   ├── news_processor.py  # Core news processing logic
│   └── database.py        # Vector database operations
├── utils/
│   ├── hebrew_nlp.py      # Hebrew text processing
│   └── similarity.py      # Similarity detection algorithms
└── data/                  # Local data storage
```

## Installation 📦

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- Access to source news channels

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TelegramBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up Telegram Bot**
   - Create a bot via [@BotFather](https://t.me/botfather)
   - Get your bot token
   - Create a channel for publishing news
   - Add your bot as an admin to the channel

## Configuration ⚙️

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=@your_channel_or_chat_id

# Source channels to monitor (comma-separated)
SOURCE_CHANNELS=@channel1,@channel2,@channel3

# Vector Database Configuration
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# Similarity Thresholds (0.0 to 1.0)
SIMILARITY_THRESHOLD=0.85    # Threshold for considering posts as duplicates
UPDATE_THRESHOLD=0.75        # Threshold for considering posts as updates

# Hebrew NLP Model
HEBREW_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Bot Settings
MAX_POST_LENGTH=4096
FAKE_NEWS_MARKER=ייתכן ומדובר בפייק

# Logging
LOG_LEVEL=INFO
```

### Key Configuration Parameters

- **SIMILARITY_THRESHOLD**: Higher values (0.8-0.9) = stricter duplicate detection
- **UPDATE_THRESHOLD**: Lower values (0.7-0.8) = more sensitive to updates
- **SOURCE_CHANNELS**: List of channels to monitor (use @ for usernames or chat IDs)

## Usage 🚀

### Running the Bot

```bash
python main.py
```

### Bot Commands

The bot supports the following commands:

- `/start` - Welcome message and introduction
- `/help` - Detailed help and usage guide
- `/stats` - Database and processing statistics
- `/status` - Current bot status and configuration

### Monitoring Workflow

1. **Message Reception**: Bot receives messages from monitored channels
2. **Content Analysis**: Extracts keywords, entities, and generates embeddings
3. **Similarity Check**: Compares with existing posts in the database
4. **Action Decision**:
   - **New Story**: Publishes to the target channel
   - **Update**: Edits existing post with new information
   - **Fake News**: Adds warning marker to existing post
   - **Duplicate**: Ignores the message

## Technical Details 🔧

### Hebrew NLP Processing

- **Text Cleaning**: Removes URLs, mentions, excessive punctuation
- **Keyword Extraction**: Identifies important Hebrew terms
- **Named Entity Recognition**: Extracts locations, organizations, people
- **Embedding Generation**: Creates semantic vectors for similarity comparison
- **Summarization**: Generates concise summaries when needed

### Similarity Detection

The bot uses a multi-factor similarity algorithm:

- **Semantic Similarity** (60%): Cosine similarity of sentence embeddings
- **Keyword Overlap** (25%): Jaccard similarity of extracted keywords  
- **Entity Matching** (15%): Overlap of named entities

### Database Schema

Each news post is stored with:
- Original Hebrew content
- Source channel information
- Timestamp and metadata
- Keywords and named entities
- Vector embedding for similarity search
- Publication status and message IDs

## Customization 🎨

### Adding New Source Channels

1. Add channel username or ID to `SOURCE_CHANNELS` in `.env`
2. Ensure the bot has access to read messages from the channel
3. Restart the bot

### Adjusting Similarity Thresholds

- **Higher SIMILARITY_THRESHOLD**: Fewer duplicates detected, more separate posts
- **Lower UPDATE_THRESHOLD**: More updates detected, more post edits

### Hebrew NLP Model

You can use different multilingual models:
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (default)
- `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (better quality, slower)

## Monitoring and Maintenance 📊

### Logs

The bot generates detailed logs in:
- Console output (real-time)
- `bot.log` file (persistent)

### Database Maintenance

The bot includes automatic cleanup features:
- Old posts cleanup (configurable retention period)
- Database statistics and health monitoring

### Performance Monitoring

Use the `/stats` command to monitor:
- Total posts processed
- Recent activity (24h)
- Fake news detection count
- Processing thresholds

## Troubleshooting 🔧

### Common Issues

1. **Bot not receiving messages**
   - Check if bot has access to source channels
   - Verify channel usernames/IDs in configuration

2. **High memory usage**
   - Reduce the number of monitored channels
   - Implement more aggressive database cleanup

3. **False duplicate detection**
   - Lower the SIMILARITY_THRESHOLD
   - Adjust similarity algorithm weights

4. **Missing Hebrew processing**
   - Ensure Hebrew NLP model is properly downloaded
   - Check internet connection for model downloads

### Debug Mode

Set `LOG_LEVEL=DEBUG` in `.env` for detailed processing information.

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the logs for error details
- Use `/status` command to verify bot configuration

---

**Note**: This bot is designed specifically for Hebrew news content. While it may work with other languages, optimal performance is achieved with Hebrew text.