from typing import List, Optional
from beanie import PydanticObjectId, Link
from datetime import datetime

# Adjusted imports for repository level
from ..models import Chat, Message
from ..schemas import ChatReadBasic

class ChatRepository:
    """Handles database operations for Chat and Message models."""

    async def create_chat(self, name: Optional[str], owner_id: PydanticObjectId) -> Chat:
        """Creates and returns a new Chat document."""
        new_chat = Chat(name=name, owner_id=owner_id, messages=[])
        await new_chat.create()
        return new_chat

    async def find_chat_by_id(self, chat_id: PydanticObjectId) -> Optional[Chat]:
        """Finds a chat by its ID."""
        return await Chat.get(chat_id)

    async def find_chat_by_id_and_owner(
        self,
        chat_id: PydanticObjectId,
        owner_id: PydanticObjectId,
        fetch_links: bool = False # Allow specifying if links should be fetched
    ) -> Optional[Chat]:
        """Finds a chat by ID and owner ID, optionally fetching links."""
        return await Chat.find_one(
            Chat.id == chat_id,
            Chat.owner_id == owner_id,
            fetch_links=fetch_links
        )

    async def find_chats_by_owner(self, owner_id: PydanticObjectId) -> List[Chat]:
        """Finds all chats owned by a specific user."""
        return await Chat.find(Chat.owner_id == owner_id).to_list()

    async def save_chat(self, chat: Chat) -> Chat:
        """Saves changes to an existing Chat document."""
        await chat.save()
        return chat

    async def create_message(
        self,
        sender_type: str,
        content: str,
        author_id: Optional[PydanticObjectId]
    ) -> Message:
        """Creates and returns a new Message document."""
        new_message = Message(
            sender_type=sender_type,
            content=content,
            author_id=author_id
        )
        await new_message.create()
        return new_message

    async def add_message_link_to_chat(self, chat: Chat, message: Message) -> Chat:
        """Adds a message link to a chat and saves the chat."""
        chat.messages.append(message)
        chat.updated_at = datetime.utcnow()
        await chat.save()
        return chat 