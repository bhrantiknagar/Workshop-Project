"""PDF document model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PDFDocument:
    """Represents a PDF uploaded by a user."""

    filename: str
    path: str
    uploaded_at: datetime
