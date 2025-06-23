
import logging
import sys
import io
import os

# Handle both direct and package imports
try:
    from ..config.settings import LOG_LEVEL, LOG_FILE
except ImportError:
    from config.settings import LOG_LEVEL, LOG_FILE


def setup_logger():
    logger = logging.getLogger("dental_clinics_scraper")

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler - always UTF-8
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Console handler with UTF-8 encoding
    if sys.platform == 'win32':
        # On Windows, use a special approach to handle UTF-8 in console
        try:
            # Try to set console to UTF-8 mode on Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # 65001 is the code page for UTF-8
        except:
            # If setting console mode fails, just use a string IO buffer for logging
            pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()