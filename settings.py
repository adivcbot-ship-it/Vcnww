import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# ==================== TELEGRAM CONFIGURATION ====================
API_ID = int(os.getenv("API_ID", "25568104"))
API_HASH = os.getenv("API_HASH", "1fad906cac7681b06288c491a2cc0617")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7852875386:AAHQPfLwbGRX6iSHOnq8H9hoN3lU-Xr6Hns")
SUDO_USERS = [int(x.strip()) for x in os.getenv("SUDO_USERS", "7793252666").split(",")]

# ==================== AUDIO CONFIGURATION ====================
DEFAULT_RADIO_URL = os.getenv("DEFAULT_RADIO_URL", "https://ice1.somafm.com/groovesalad-128-mp3")
AUDIO_BITRATE = int(os.getenv("AUDIO_BITRATE", "48000"))
AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", "2"))

# ==================== SCREENSHARE CONFIGURATION ====================
SCREENSHARE_QUALITY = os.getenv("SCREENSHARE_QUALITY", "720p")
SCREENSHARE_FPS = int(os.getenv("SCREENSHARE_FPS", "30"))

# ==================== DATABASE CONFIGURATION ====================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///vcfight.db")

# ==================== LOGGING CONFIGURATION ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==================== EFFECTS CONFIGURATION ====================
DEFAULT_EFFECTS = {
    'gain': int(os.getenv("DEFAULT_GAIN", "100")),
    'echo': int(os.getenv("DEFAULT_ECHO", "0")),
    'loudness': int(os.getenv("DEFAULT_LOUDNESS", "0")),
    'bass': int(os.getenv("DEFAULT_BASS", "0"))
}

# ==================== VOICE CHAT CONFIGURATION ====================
AUTO_LEAVE_ON_STOP = os.getenv("AUTO_LEAVE_ON_STOP", "true").lower() == "true"
MAX_BRIDGES = int(os.getenv("MAX_BRIDGES", "5"))

# ==================== ADVANCED CONFIGURATION ====================
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/vcfight")
SESSION_PREFIX = os.getenv("SESSION_PREFIX", "Assistant_")

# Create directories
Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("downloads").mkdir(exist_ok=True)
Path("screenshots").mkdir(exist_ok=True)

# Logging setup
import logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vcfight.log'),
        logging.StreamHandler()
    ]
)
