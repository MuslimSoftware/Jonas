from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone

class Screenshot(Document):
    """Screenshot model for MongoDB."""
    chat_id: PydanticObjectId = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    image_data: str = Field(...) # Store the full data URI (data:image/png;base64,...)

    class Settings:
        name = "screenshots"
        indexes = [
            [ ("chat_id", 1), ("created_at", 1) ] # Index for fetching by chat
        ]

# Explicitly rebuild model
Screenshot.model_rebuild() 