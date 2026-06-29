"""History record model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class HistoryRecord:
    """Represents a past user action."""

    action: str
    detail: str
    created_at: datetime
