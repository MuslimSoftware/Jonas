from beanie import Document, Link, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from .chat_model import Chat
    from app.features.user.models import User

class Message(Document):
    """Message model for MongoDB using Beanie ODM."""
    # chat_id: Link["Chat"] # Direct link to Chat document - REMOVED: Chat will link to Messages
    sender_type: Literal['user', 'agent'] = Field(default='user')
    content: str = Field(...)
    author_id: Optional[PydanticObjectId] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: Literal['text', 'thinking', 'tool_use', 'error'] = Field(default='text')
    tool_name: Optional[str] = Field(default=None)

    class Settings:
        name = "messages"

    class Config:
        # Example for documentation / testing
        json_schema_extra = {
            "example": {
                "sender_type": "user",
                "content": "Hello there!",
                "author_id": "60d5ec49abf8a7b6a0f3e8f1",
                "created_at": "2023-01-01T12:00:00Z",
            }
        } 