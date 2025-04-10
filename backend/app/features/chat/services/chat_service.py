from typing import List, Optional, TYPE_CHECKING
from beanie import PydanticObjectId, Link

from ..schemas import MessageCreate, ChatCreate, MessageData, ChatListItemData
from app.features.common.schemas.common_schemas import PaginatedResponseData
from app.features.common.exceptions import AppException
from ..models import Chat, Message
from datetime import datetime

# Import dependency types only for type checking to break circular import
if TYPE_CHECKING:
    from app.config.dependencies import ChatRepositoryDep, ConnectionRepositoryDep

class ChatService:
    """Service layer for chat operations, uses ChatRepository."""
    def __init__(self,
        chat_repository: 'ChatRepositoryDep',
        connection_repository: 'ConnectionRepositoryDep'
    ):
        self.chat_repository = chat_repository
        self.connection_repository = connection_repository

    async def create_new_chat(self, chat_data: ChatCreate, owner_id: PydanticObjectId) -> Chat:
        """Service layer function to create a new chat."""
        new_chat = await self.chat_repository.create_chat(
            name=chat_data.name, 
            owner_id=owner_id,
            subtitle=chat_data.subtitle
        )
        return new_chat

    async def add_message_to_chat(
        self,
        chat_id: PydanticObjectId,
        message_data: MessageCreate,
        current_user_id: PydanticObjectId
    ) -> Message:
        """Service layer function to add a message to a chat."""
        # Verify chat exists and belongs to the user
        chat = await self.chat_repository.find_chat_by_id_and_owner(chat_id, current_user_id)
        if not chat:
            # Check if chat exists at all for better error message
            chat_exists = await self.chat_repository.find_chat_by_id(chat_id)
            if chat_exists:
                 raise AppException(status_code=403, error_code="FORBIDDEN", message="User does not own this chat")
            else:
                 raise AppException(status_code=404, error_code="CHAT_NOT_FOUND", message="Chat not found")

        # Determine author_id based on sender_type and current user
        author_id: Optional[PydanticObjectId] = None
        if message_data.sender_type == 'user':
             author_id = current_user_id

        # Call repository to create the message document
        new_message = await self.chat_repository.create_message(
            sender_type=message_data.sender_type,
            content=message_data.content,
            author_id=author_id
        )

        # Call repository to add message link to chat and save
        await self.chat_repository.add_message_link_to_chat(chat=chat, message=new_message)

        # --- Broadcast the new message --- 
        message_broadcast_data = MessageData.model_validate(new_message)
        await self.connection_repository.broadcast_to_chat(
            message=message_broadcast_data.model_dump_json(by_alias=True), 
            chat_id=str(chat_id) 
        )
        # --- End Broadcast ---

        return new_message

    async def get_chats_for_user(
        self, 
        owner_id: PydanticObjectId,
        limit: int,
        before_timestamp: Optional[datetime]
    ) -> PaginatedResponseData[ChatListItemData]:
        """Service layer function to get chats for a user, paginated."""
        fetch_limit = limit + 1
        chats = await self.chat_repository.find_chats_by_owner(
            owner_id=owner_id,
            limit=fetch_limit,
            before_timestamp=before_timestamp
        )

        has_more = len(chats) == fetch_limit
        items_to_return = chats[:limit] if has_more else chats
        
        next_cursor_timestamp = items_to_return[-1].created_at if items_to_return and has_more else None

        chat_items = [ChatListItemData.model_validate(chat) for chat in items_to_return]

        return PaginatedResponseData(
            items=chat_items,
            has_more=has_more,
            next_cursor_timestamp=next_cursor_timestamp
        )

    async def get_chat_by_id(self, chat_id: PydanticObjectId, owner_id: PydanticObjectId) -> Chat:
        """DEPRECATED: Use get_messages_for_chat for messages. Gets chat details without messages."""
        chat = await self.chat_repository.find_chat_by_id_and_owner(
            chat_id=chat_id,
            owner_id=owner_id,
            fetch_links=False
        )
        if not chat:
             raise AppException(status_code=404, error_code="CHAT_NOT_FOUND", message="Chat not found or not owned by user")
        
        chat.messages = []

        return chat
        
    async def get_messages_for_chat(
        self,
        chat_id: PydanticObjectId,
        owner_id: PydanticObjectId,
        limit: int,
        before_timestamp: Optional[datetime]
    ) -> PaginatedResponseData[MessageData]:
        """Service layer function to get messages for a specific chat, paginated."""
        chat = await self.chat_repository.find_chat_by_id_and_owner(
            chat_id=chat_id,
            owner_id=owner_id,
            fetch_links=False
        )
        if not chat:
            raise AppException(status_code=404, error_code="CHAT_NOT_FOUND", message="Chat not found or not owned by user")
        
        message_ids = [link.to_ref().id for link in chat.messages] if chat.messages else []
        if not message_ids:
            return PaginatedResponseData(items=[], has_more=False, next_cursor_timestamp=None)

        fetch_limit = limit + 1
        messages = await self.chat_repository.find_messages_by_ids(
            message_ids=message_ids,
            limit=fetch_limit,
            before_timestamp=before_timestamp
        )

        has_more = len(messages) == fetch_limit
        items_to_return = messages[:limit] if has_more else messages

        next_cursor_timestamp = items_to_return[-1].created_at if items_to_return and has_more else None

        message_items = [MessageData.model_validate(msg) for msg in items_to_return]

        return PaginatedResponseData(
            items=message_items,
            has_more=has_more,
            next_cursor_timestamp=next_cursor_timestamp
        ) 