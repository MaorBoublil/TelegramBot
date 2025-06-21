#!/usr/bin/env python3
"""
Setup script for Hebrew News Bot
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def install_dependencies():
    """Install required Python packages"""
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = [
        "data",
        "data/chroma_db",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def setup_environment():
    """Setup environment file"""
    print("⚙️ Setting up environment configuration...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists():
        if env_example.exists():
            # Copy example to .env
            with open(env_example, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Created .env file from .env.example")
            print("⚠️  Please edit .env file with your configuration before running the bot")
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
    
    return True

def download_models():
    """Download required NLP models"""
    print("🤖 Downloading Hebrew NLP models...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Download the default model
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        print(f"📥 Downloading {model_name}...")
        
        model = SentenceTransformer(model_name)
        print("✅ Hebrew NLP model downloaded successfully")
        return True
        
    except ImportError:
        print("⚠️  sentence-transformers not installed yet, models will be downloaded on first run")
        return True
    except Exception as e:
        print(f"❌ Error downloading models: {e}")
        return False

def verify_setup():
    """Verify the setup is complete"""
    print("🔍 Verifying setup...")
    
    # Check if .env exists and has required variables
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Check for required environment variables
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHANNEL_ID",
        "SOURCE_CHANNELS"
    ]
    
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=your_" in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  The following environment variables need to be configured:")
        for var in missing_vars:
            print(f"   - {var}")
        print("Please edit the .env file before running the bot")
    else:
        print("✅ Environment configuration looks good")
    
    # Check directories
    required_dirs = ["data", "data/chroma_db", "logs"]
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"❌ Directory missing: {directory}")
            return False
    
    print("✅ All directories exist")
    return True

def main():
    """Main setup function"""
    print("🚀 Hebrew News Bot Setup")
    print("=" * 40)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Creating directories", create_directories),
        ("Setting up environment", setup_environment),
        ("Downloading models", download_models),
        ("Verifying setup", verify_setup)
    ]
    
    failed_steps = []
    
    for step_name, step_function in steps:
        if not step_function():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 40)
    
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease fix the errors and run setup again.")
        return False
    else:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit the .env file with your Telegram bot token and channel information")
        print("2. Run the bot with: python main.py")
        print("3. Use /help command in Telegram to see available commands")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)