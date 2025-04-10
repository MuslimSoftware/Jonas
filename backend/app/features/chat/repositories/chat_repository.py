from typing import List, Optional
from beanie import PydanticObjectId, Link
from beanie.odm.operators.find.comparison import In
from datetime import datetime, timezone

# Adjusted imports for repository level
from ..models import Chat, Message

class ChatRepository:
    """Handles database operations for Chat and Message models."""

    async def create_chat(self, name: Optional[str], owner_id: PydanticObjectId, subtitle: Optional[str] = None) -> Chat:
        """Creates and returns a new Chat document."""
        new_chat = Chat(name=name, owner_id=owner_id, subtitle=subtitle, messages=[])
        await new_chat.create()
        return new_chat

    async def find_chat_by_id(self, chat_id: PydanticObjectId) -> Optional[Chat]:
        """Finds a chat by its ID."""
        # Fetch without links by default for efficiency unless specified
        return await Chat.get(chat_id, fetch_links=False)

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

    async def find_chats_by_owner(
        self, 
        owner_id: PydanticObjectId,
        limit: int,
        before_timestamp: Optional[datetime] = None
    ) -> List[Chat]:
        """Finds chats owned by a specific user, paginated."""
        query = Chat.find(Chat.owner_id == owner_id)
        
        # Apply cursor filter if provided
        if before_timestamp:
            query = query.find(Chat.created_at < before_timestamp)
            
        # Sort by creation time descending (latest first) and apply limit
        # Fetch without links for list view efficiency
        chats = await query.sort(-Chat.created_at).limit(limit).find(fetch_links=False).to_list()
        return chats

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
        if chat.messages is None:
             chat.messages = []
        chat.messages.append(Link(ref=message, document_class=Message))
        chat.updated_at = datetime.now(timezone.utc)
        chat.latest_message_content = message.content 
        chat.latest_message_timestamp = message.created_at
        await chat.save()
        return chat
        
    async def find_messages_by_ids(
        self,
        message_ids: List[PydanticObjectId],
        limit: int,
        before_timestamp: Optional[datetime] = None
    ) -> List[Message]:
        """Finds messages by their IDs, paginated by timestamp."""
        if not message_ids:
            return []

        query = Message.find(In(Message.id, message_ids))

        # Apply cursor filter if provided
        if before_timestamp:
            query = query.find(Message.created_at < before_timestamp)

        # Sort by creation time descending (latest first) and apply limit
        messages = await query.sort(-Message.created_at).limit(limit).to_list()
        return messages 