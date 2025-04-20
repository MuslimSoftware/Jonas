from typing import List, Optional, TYPE_CHECKING, Literal
from beanie import PydanticObjectId, Link
from datetime import datetime, timezone

from ..models import Chat, Message, Screenshot
from ..schemas import MessageCreate, ChatCreate, ChatUpdate, MessageData, ChatData, MessageType, ScreenshotData
from app.features.common.schemas.common_schemas import PaginatedResponseData
from app.features.common.exceptions import AppException

if TYPE_CHECKING:
    from app.config.dependencies import ChatRepositoryDep, WebSocketRepositoryDep, ScreenshotRepositoryDep
    from app.features.chat.repositories import ChatRepository, WebSocketRepository, ScreenshotRepository
class ChatService:
    """Service layer for chat operations, uses ChatRepository."""
    def __init__(self,
        chat_repository: 'ChatRepositoryDep',
        screenshot_repository: 'ScreenshotRepositoryDep',
        websocket_repository: 'WebSocketRepositoryDep'
    ):
        self.chat_repository: ChatRepository = chat_repository
        self.screenshot_repository: ScreenshotRepository = screenshot_repository
        self.websocket_repository: WebSocketRepository = websocket_repository

    async def create_new_chat(self, chat_data: ChatCreate, owner_id: PydanticObjectId) -> Chat:
        """Service layer function to create a new chat."""
        new_chat = await self.chat_repository.create_chat(
            name=chat_data.name, 
            owner_id=owner_id
        )
        return new_chat

    async def _create_and_broadcast_message(
        self,
        chat: Chat,
        sender_type: Literal['user', 'agent'],
        content: str,
        message_type: MessageType = 'text',
        tool_name: Optional[str] = None,
        author_id: Optional[PydanticObjectId] = None
    ) -> Optional[Message]:
        """Internal helper: Creates message, saves (conditionally), broadcasts."""
        
        save_to_db = message_type in ['text', 'error', 'tool_use', 'action']
        new_message_model: Optional[Message] = None
        message_json: str

        if save_to_db:
            # Create and save the message model
            new_message_model = await self.chat_repository.create_message(
                sender_type=sender_type,
                content=content,
                author_id=author_id,
                message_type=message_type,
                tool_name=tool_name
            )
            # Add link to chat and update latest message fields
            await self.chat_repository.add_message_link_to_chat(chat=chat, message=new_message_model)
            # Prepare broadcast data from the saved model
            broadcast_data = MessageData.model_validate(new_message_model)
            message_json = broadcast_data.model_dump_json(by_alias=True, exclude_none=True)
        else:
            temp_timestamp = datetime.now(timezone.utc)
            broadcast_data = MessageData(
                id=PydanticObjectId(), # Generate a temporary ObjectId for broadcast
                sender_type=sender_type,
                content=content,
                author_id=author_id,
                created_at=temp_timestamp,
                type=message_type,
                tool_name=tool_name
            )
            message_json = broadcast_data.model_dump_json(by_alias=True, exclude_none=True)

        await self.websocket_repository.broadcast_to_chat(
            message=message_json, 
            chat_id=str(chat.id) 
        )
        
        return new_message_model

    async def get_chats_for_user(
        self, 
        owner_id: PydanticObjectId,
        limit: int,
        before_timestamp: Optional[datetime]
    ) -> PaginatedResponseData[ChatData]:
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

        chat_items = [ChatData.model_validate(chat) for chat in items_to_return]

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

    async def update_chat_details(
        self,
        chat_id: PydanticObjectId,
        update_data: ChatUpdate,
        owner_id: PydanticObjectId
    ) -> Chat:
        """Updates a chat's name and/or subtitle."""
        chat = await self.chat_repository.find_chat_by_id_and_owner(chat_id, owner_id)
        if not chat:
             raise AppException(status_code=404, error_code="CHAT_NOT_FOUND", message="Chat not found or not owned by user")

        # Check if at least one field is provided for update
        update_payload = update_data.model_dump(exclude_unset=True)
        if not update_payload:
             raise AppException(status_code=400, error_code="NO_UPDATE_DATA", message="No fields provided for update")

        # Update fields if they are provided in the payload
        if "name" in update_payload:
            chat.name = update_payload["name"]
        
        # Use timezone-aware UTC timestamp
        chat.updated_at = datetime.now(timezone.utc) 
        updated_chat = await self.chat_repository.save_chat(chat)
        updated_chat.messages = [] 
        return updated_chat
    
    async def update_message_content(self, message_id: PydanticObjectId, new_content: str):
        """Service layer method to update message content."""
        print(f"ChatService: Updating content for message {message_id}")
        updated_message = await self.chat_repository.update_message_content(message_id, new_content)
        if not updated_message:
             print(f"ChatService Warning: Message {message_id} not found for content update.")
             # Optionally raise an exception here if needed
        # No broadcast needed for content update after stream usually

    async def get_recent_messages(self, chat_id: PydanticObjectId, limit: int = 20) -> List[Message]:
        """Service layer method to get recent messages for history."""
        # Add validation? Check if user owns chat_id first?
        # For now, directly call repository
        return await self.chat_repository.find_recent_messages_by_chat_id(chat_id, limit)

    async def get_screenshots_for_chat(
        self,
        chat_id: PydanticObjectId,
        owner_id: PydanticObjectId,
        limit: int,
        before_timestamp: Optional[datetime] = None
    ) -> PaginatedResponseData[ScreenshotData]:
        """Service layer function to get paginated screenshots for a specific chat."""
        # 1. Verify chat ownership
        chat = await self.chat_repository.find_chat_by_id_and_owner(
            chat_id=chat_id,
            owner_id=owner_id,
            fetch_links=False
        )
        if not chat:
            raise AppException(status_code=404, error_code="CHAT_NOT_FOUND", message="Chat not found or not owned by user")

        # 2. Fetch total count and screenshots from repository with pagination logic
        total_count = await self.screenshot_repository.count_screenshots_by_chat_id(chat_id)
        
        fetch_limit = limit + 1
        screenshots = await self.screenshot_repository.find_screenshots_by_chat_id(
            chat_id=chat_id,
            limit=fetch_limit,
            before_timestamp=before_timestamp
        )

        # 3. Calculate pagination details
        has_more = len(screenshots) == fetch_limit
        items_to_return = screenshots[:limit] if has_more else screenshots

        # Determine the next cursor timestamp based on the last item returned
        next_cursor_timestamp = items_to_return[-1].created_at if items_to_return and has_more else None

        # 4. Convert to response schema
        screenshot_items = [ScreenshotData.model_validate(ss) for ss in items_to_return]

        # 5. Return paginated response including total count
        return PaginatedResponseData(
            items=screenshot_items,
            has_more=has_more,
            next_cursor_timestamp=next_cursor_timestamp,
            total_items=total_count
        ) 