import json
import time
import os
from pathlib import Path
from datetime import datetime

# Handle both direct execution and package imports
try:
    from ..config.settings import DATA_DIR
except ImportError:
    from config.settings import DATA_DIR


def load_json_file(file_path):
    """Load data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Error loading JSON file {file_path}: {str(e)}")


def save_json_file(data, file_path, ensure_dir=True):
    """Save data to a JSON file."""
    if ensure_dir:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise Exception(f"Error saving JSON file {file_path}: {str(e)}")


def get_timestamp_filename(prefix, extension):
    """Generate a filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def create_data_directory(dir_name=None):
    """Create a directory for storing data."""
    if dir_name:
        directory = DATA_DIR / dir_name
    else:
        directory = DATA_DIR

    os.makedirs(directory, exist_ok=True)
    return directory


def retry_function(func, max_retries=3, delay=2, backoff=2):
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        retries = 0
        current_delay = delay

        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    raise e

                time.sleep(current_delay)
                current_delay *= backoff

    return wrapper