from typing import List, Dict, Any
from beanie import PydanticObjectId

from ..models import ContextItem
from ..repositories.context_repository import ContextRepository

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

    async def fetch_chat_context(self, chat_id: PydanticObjectId) -> List[ContextItem]:
        """Fetches all context items for a chat via the repository."""
        return await self.context_repository.get_context_for_chat(chat_id)