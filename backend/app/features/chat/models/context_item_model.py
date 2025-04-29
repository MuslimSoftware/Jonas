from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel
from datetime import datetime, timezone
from typing import Dict, Any

class ContextItem(Document):
    """Model to store contextual information gathered by agents during a chat."""
    chat_id: PydanticObjectId = Field(..., index=True)
    source_agent: str = Field(..., index=True) # e.g., "browser_agent", "database_agent"
    content_type: str = Field(...) # e.g., "summary", "extracted_ids", "booking_details", "error", "raw_tool_output"
    data: Dict[str, Any] = Field(...) # Flexible dictionary to store structured data
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "context_items"
        indexes = [
            # Compound index for efficient querying by chat and optionally source/type
            [ ("chat_id", 1), ("source_agent", 1), ("content_type", 1), ("created_at", -1) ], 
            [ ("created_at", -1) ] # Index for potential cleanup or TTL later
        ]

# Explicitly rebuild model
ContextItem.model_rebuild() 