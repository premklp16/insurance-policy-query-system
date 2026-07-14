import os
import logging

# Root directory of the backend folder
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Temp folder for holding uploaded PDFs (if needed for processing)
UPLOAD_DIR = os.path.join(BACKEND_DIR, "uploads")

# Debug mode flag
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Centralized logging configuration
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def ensure_directories() -> None:
    """Ensures that the temp uploads directory exists."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

