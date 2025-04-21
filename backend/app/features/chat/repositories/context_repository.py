from typing import List
from beanie import PydanticObjectId
from app.features.chat.models.context_item_model import ContextItem

class ContextRepository:
    """Handles database operations for the ContextItem model."""

    async def add_context_item(self, item: ContextItem) -> ContextItem:
        """Saves a new ContextItem document."""
        await item.insert()
        return item

    async def get_context_for_chat(self, chat_id: PydanticObjectId) -> List[ContextItem]:
        """Retrieves all context items for a specific chat, ordered by creation time (newest first)."""
        return await ContextItem.find(ContextItem.chat_id == chat_id)\
                              .sort(-ContextItem.created_at)\
                              .to_list() 