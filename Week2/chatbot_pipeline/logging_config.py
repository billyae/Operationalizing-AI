import logging
import os
from logging.handlers import RotatingFileHandler

# Ensure the logs/ folder exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "bedrock_chatbot.log")

def setup_logging():
    """
    Configures root logger to write INFO+ logs to logs/bedrock_chatbot.log,
    with a rotating file handler (max 5 MB per file, keep 3 backups).
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # If handlers are already configured, skip
    if logger.handlers:
        return

    # Create a rotating file handler
    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Also print to console at DEBUG level (optional)
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(formatter)
    logger.addHandler(console)

# Call setup_logging automatically when imported
setup_logging()
