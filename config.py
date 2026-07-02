"""Central configuration values for SmartPDF AI."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Default Flask configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
    TEMP_FOLDER = BASE_DIR / "data" / "temp"
    PROCESSED_FOLDER = BASE_DIR / "data" / "processed"
    EMBEDDINGS_FOLDER = BASE_DIR / "data" / "embeddings"
    CHROMA_DB_PATH = BASE_DIR / "database" / "chroma_db"
    LOG_FILE = BASE_DIR / "logs" / "smartpdf.log"

    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))
    ALLOWED_EXTENSIONS = {"pdf"}
