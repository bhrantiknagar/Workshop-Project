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
    CHROMA_DB_PATH = BASE_DIR / "database" / "chroma_db"
    LOG_FILE = BASE_DIR / "logs" / "smartpdf.log"

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "60"))
    # GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    # GOOGLE_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/gemini-embedding-001")
    ALLOWED_EXTENSIONS = {"pdf"}
