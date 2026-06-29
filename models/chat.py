"""Chat message model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    """Represents a user or assistant chat message."""

    role: str
    content: str
    created_at: datetime
