"""
Configuration file for API keys and settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys and Credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')

KALSHI_API_KEY = os.getenv('KALSHI_API_KEY', '')
KALSHI_API_SECRET = os.getenv('KALSHI_API_SECRET', '')

# TikTok (requires RapidAPI or similar)
TIKTOK_API_KEY = os.getenv('TIKTOK_API_KEY', '')

# Radio Airplay (Mediabase/BDS credentials - NOT NEEDED, using kworb.net)
MEDIABASE_USERNAME = os.getenv('MEDIABASE_USERNAME', '')
MEDIABASE_PASSWORD = os.getenv('MEDIABASE_PASSWORD', '')

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'billboard_data')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Data Collection Settings
TOP_N_SONGS = 200  # Number of top songs to track
COLLECTION_INTERVAL_HOURS = 24  # How often to collect data
BILLBOARD_TRACKING_WEEK_START = 'Friday'  # Billboard week starts Friday
BILLBOARD_TRACKING_WEEK_END = 'Thursday'  # Billboard week ends Thursday

# Storage paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

