from typing import List, Optional, TYPE_CHECKING
from beanie import PydanticObjectId

from ..schemas import MessageCreate, ChatCreate, MessageData
from app.features.common.exceptions import AppException
from ..models import Chat, Message

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
        new_chat = await self.chat_repository.create_chat(name=chat_data.name, owner_id=owner_id)
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
        # Convert message to the new MessageData schema
        message_broadcast_data = MessageData.model_validate(new_message)
        # Broadcast as JSON string
        await self.connection_repository.broadcast_to_chat(
            message=message_broadcast_data.model_dump_json(), 
            chat_id=str(chat_id) # Use string representation for dict key
        )
        # --- End Broadcast ---

        return new_message

    async def get_chats_for_user(self, owner_id: PydanticObjectId) -> List[Chat]:
        """Service layer function to get chats for a user."""
        # Call repository to find chats
        chats = await self.chat_repository.find_chats_by_owner(owner_id=owner_id)
        return chats

    async def get_chat_by_id(self, chat_id: PydanticObjectId, owner_id: PydanticObjectId) -> Chat:
        """Service layer function to get a specific chat by ID."""
        # Call repository to find the chat, requesting links to be fetched
        chat = await self.chat_repository.find_chat_by_id_and_owner(
            chat_id=chat_id,
            owner_id=owner_id,
            fetch_links=True
        )
        if not chat:
            # No need to check existence separately here, find_chat_by_id_and_owner handles it
             raise AppException(status_code=404, error_code="CHAT_NOT_FOUND", message="Chat not found or not owned by user")
        return chat 