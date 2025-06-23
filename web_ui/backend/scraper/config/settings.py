"""
Default settings for the scraper backend.
These can be overridden by the web UI settings.
"""

import os
from pathlib import Path

# Base directory for backend
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'

# Default API settings (will be overridden by UI)
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
LANGUAGE = 'tr'
REGION = 'tr'

# Default search settings
SEARCH_RADIUS = 15000  # meters
REQUEST_DELAY = 1  # seconds between requests
MAX_RETRIES = 3

# Default storage settings
STORAGE_TYPE = 'json'  # Options: 'json', 'mongodb'
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB = os.getenv('MONGODB_DB', 'dental_clinics')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'places')

# Default search terms (will be overridden by UI)
SEARCH_TERMS = [
    "diş kliniği",
    "dentist"
]

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', str(BASE_DIR / 'scraper.log'))