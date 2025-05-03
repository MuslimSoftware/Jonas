from typing import List, Optional
from beanie import PydanticObjectId
from app.features.chat.models.context_item_model import ContextItem
from datetime import datetime

class ContextRepository:
    """Handles database operations for the ContextItem model."""

    async def add_context_item(self, item: ContextItem) -> ContextItem:
        """Saves a new ContextItem document."""
        await item.insert()
        return item

    async def get_context_for_chat(
        self, 
        chat_id: PydanticObjectId, 
        limit: int,
        before_timestamp: Optional[datetime] = None
    ) -> List[ContextItem]:
        """Retrieves context items for a specific chat, ordered by creation time (newest first), with pagination."""
        query = ContextItem.find(ContextItem.chat_id == chat_id)
        if before_timestamp:
            query = query.find(ContextItem.created_at < before_timestamp)
            
        return await query.sort(-ContextItem.created_at).limit(limit).to_list()

    async def get_all_context_for_chat(self, chat_id: PydanticObjectId) -> List[ContextItem]:
        """Retrieves ALL context items for a specific chat, ordered by creation time (oldest first)."""
        # Sort ascending to easily get the latest if keys collide when building state
        return await ContextItem.find(ContextItem.chat_id == chat_id) \
                              .sort(+ContextItem.created_at) \
                              .to_list() 