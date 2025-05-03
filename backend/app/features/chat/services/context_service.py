from typing import List, Dict, Any, Optional
from beanie import PydanticObjectId
from datetime import datetime

from ..models import ContextItem
from ..repositories.context_repository import ContextRepository
from app.features.common.schemas.common_schemas import PaginatedResponseData

class ContextService:
    """Service layer for managing context items."""
    def __init__(self, context_repository: ContextRepository):
        self.context_repository = context_repository

    async def save_agent_context(
        self,
        chat_id: PydanticObjectId,
        source_agent: str,
        content_type: str,
        data: Dict[str, Any]
    ) -> ContextItem:
        """Creates a ContextItem instance and saves it via the repository."""
        context_item = ContextItem(
            chat_id=chat_id,
            source_agent=source_agent,
            content_type=content_type,
            data=data
        )
        return await self.context_repository.add_context_item(context_item)

    async def fetch_chat_context(
        self, 
        chat_id: PydanticObjectId,
        limit: int,
        before_timestamp: Optional[datetime] = None
    ) -> PaginatedResponseData[ContextItem]:
        """Fetches paginated context items for a chat via the repository."""
        # Fetch one extra item to determine if there are more pages
        items_to_fetch = limit + 1
        context_items = await self.context_repository.get_context_for_chat(
            chat_id=chat_id,
            limit=items_to_fetch,
            before_timestamp=before_timestamp
        )
        
        has_more = len(context_items) > limit
        items_to_return = context_items[:limit]
        
        next_cursor_timestamp = None
        if items_to_return:
             # Use the created_at of the last item returned as the next cursor
             next_cursor_timestamp = items_to_return[-1].created_at.isoformat()

        # Optionally fetch total count (can be expensive)
        # total_items = await ContextItem.find(ContextItem.chat_id == chat_id).count()
        total_items = None # Keep it simple for now

        return PaginatedResponseData(
            items=items_to_return,
            next_cursor_timestamp=next_cursor_timestamp,
            has_more=has_more,
            total_items=total_items
        )

    async def fetch_all_chat_context(self, chat_id: PydanticObjectId) -> List[ContextItem]:
        """Fetches ALL context items for a chat via the repository."""
        return await self.context_repository.get_all_context_for_chat(chat_id)