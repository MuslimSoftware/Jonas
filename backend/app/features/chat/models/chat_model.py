from beanie import Document, Link, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .message_model import Message
    from app.features.user.models import User

class Chat(Document):
    """Chat model for MongoDB using Beanie ODM."""
    name: Optional[str] = Field(default=None)
    subtitle: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Link["Message"]] = Field(default_factory=list)
    owner_id: PydanticObjectId = Field(...)

    class Settings:
        name = "chats"
        indexes = [
            [ ("owner_id", 1) ]
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "User's Chat",
                "subtitle": "A description or last message preview",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z",
                "messages": [],
                "owner_id": "60d5ec49abf8a7b6a0f3e8f1"
            }
        }