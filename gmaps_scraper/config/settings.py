import os
from dotenv import load_dotenv
import pathlib

load_dotenv()

BASE_DIR = pathlib.Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / 'data'

API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
LANGUAGE = 'tr'
REGION = 'tr'

SEARCH_RADIUS = 15000  # meters
REQUEST_DELAY = 1  # seconds between requests
MAX_RETRIES = 3

STORAGE_TYPE = 'json'  # Options: 'json', 'mongodb'
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB = os.getenv('MONGODB_DB', 'dental_clinics')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'places')

SEARCH_TERMS = [

    "dentist"
]

LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
LOG_FILE = os.getenv('LOG_FILE', str(BASE_DIR / 'scraper.log'))