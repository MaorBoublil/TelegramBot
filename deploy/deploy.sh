#!/bin/bash
# Deployment script for Hebrew News Bot

set -e

# Configuration
BOT_USER="bot"
BOT_GROUP="bot"
INSTALL_DIR="/opt/hebrew-news-bot"
SERVICE_NAME="hebrew-news-bot"

echo "🚀 Deploying Hebrew News Bot"
echo "================================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Create bot user if it doesn't exist
if ! id "$BOT_USER" &>/dev/null; then
    echo "👤 Creating bot user..."
    useradd --system --shell /bin/false --home-dir "$INSTALL_DIR" --create-home "$BOT_USER"
    echo "✅ Bot user created"
else
    echo "✅ Bot user already exists"
fi

# Create installation directory
echo "📁 Setting up installation directory..."
mkdir -p "$INSTALL_DIR"
chown "$BOT_USER:$BOT_GROUP" "$INSTALL_DIR"

# Copy bot files
echo "📋 Copying bot files..."
cp -r . "$INSTALL_DIR/"
chown -R "$BOT_USER:$BOT_GROUP" "$INSTALL_DIR"

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$INSTALL_DIR"
sudo -u "$BOT_USER" python3 -m venv venv
sudo -u "$BOT_USER" ./venv/bin/pip install --upgrade pip
sudo -u "$BOT_USER" ./venv/bin/pip install -r requirements.txt

# Create data directories
echo "📁 Creating data directories..."
sudo -u "$BOT_USER" mkdir -p data/chroma_db logs
chmod 755 data logs

# Copy environment file if it doesn't exist
if [[ ! -f "$INSTALL_DIR/.env" ]]; then
    echo "⚙️ Setting up environment file..."
    sudo -u "$BOT_USER" cp .env.example .env
    echo "⚠️  Please edit $INSTALL_DIR/.env with your configuration"
fi

# Install systemd service
echo "🔧 Installing systemd service..."
cp deploy/systemd/hebrew-news-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# Set up log rotation
echo "📝 Setting up log rotation..."
cat > /etc/logrotate.d/hebrew-news-bot << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $BOT_USER $BOT_GROUP
    postrotate
        systemctl reload-or-restart $SERVICE_NAME
    endscript
}
EOF

echo "✅ Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit the configuration: sudo nano $INSTALL_DIR/.env"
echo "2. Start the bot: sudo systemctl start $SERVICE_NAME"
echo "3. Check status: sudo systemctl status $SERVICE_NAME"
echo "4. View logs: sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"