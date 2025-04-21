import time
from typing import Optional, Dict, List, Any, TYPE_CHECKING
from beanie import PydanticObjectId
from google.adk.events import Event
from google.genai.types import Content, Part

if TYPE_CHECKING:
    from app.features.chat.repositories import ChatRepository
    from app.features.chat.models import Message


class ChatHistoryLoader:
    """
    Loads and formats chat history from the database for use with ADK.
    """
    def __init__(self, chat_repository: "ChatRepository"):
        """
        Initializes the loader with a ChatRepository dependency.
        """
        self.chat_repository = chat_repository

    def _format_db_messages_to_adk_events(self, messages: List["Message"]) -> List[Event]:
        """Formats DB Message list to a list of ADK Event objects."""
        formatted_events: List[Event] = []
        if not messages:
            return formatted_events
        first_user_index = -1
        for i, msg in enumerate(messages):
            if msg.sender_type == 'user':
                first_user_index = i
                break
        if first_user_index == -1:
            process_from_index = 0
        else:
            process_from_index = first_user_index
        for msg in messages[process_from_index:]:
            role = 'model' if msg.sender_type == 'agent' else 'user'
            content_text = msg.content if msg.content is not None else ""
            adk_content = Content(role=role, parts=[Part(text=content_text)])
            event_timestamp = msg.created_at.timestamp()
            event = Event(author=role, content=adk_content, timestamp=event_timestamp)
            formatted_events.append(event)
        return formatted_events

    async def get_adk_formatted_events(self, chat_id: PydanticObjectId) -> List[Event]:
        """
        Fetches recent messages for a chat and returns them as ADK Events.
        """
        db_messages = await self.chat_repository.find_recent_messages_by_chat_id(
            chat_id=chat_id
        )
        adk_events = self._format_db_messages_to_adk_events(db_messages)
        return adk_events 