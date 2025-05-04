import time
from typing import Optional, Dict, List, Any, TYPE_CHECKING
from beanie import PydanticObjectId
from google.adk.events import Event
from google.adk.sessions import Session, InMemorySessionService # Assuming InMemory for now
from google.genai.types import Content, Part
import logging

if TYPE_CHECKING:
    from app.features.chat.repositories import ChatRepository
    from app.features.chat.models import Chat, Message # Add Message import

logger = logging.getLogger(__name__)

class ADKRepository:
    """
    Handles interactions with the ADK Session Service and history loading/formatting.
    Separates ADK state management from the core agent execution logic.
    """
    def __init__(
        self,
        chat_repository: "ChatRepository",
        app_name: str = "Jonas" # Default app name, can be overridden
    ):
        """
        Initializes the repository with dependencies.
        """
        # Store ChatRepository directly
        self.chat_repository = chat_repository
        # Initialize the session service
        self.session_service = InMemorySessionService()
        self.app_name = app_name
        logger.info(f"ADKRepository initialized for app: {self.app_name}")

    async def load_or_create_session(
        self,
        chat: "Chat",
        user_id: PydanticObjectId,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Loads history into a session, creating it with the provided initial state if it doesn't exist.
        Returns the ADK Session object.
        """
        session_id = str(chat.id)
        user_id_str = str(user_id)

        session_obj = self.session_service.get_session(
            app_name=self.app_name, user_id=user_id_str, session_id=session_id
        )

        if session_obj is None:
            logger.info(f"Creating new ADK session: user_id={user_id_str}, session_id={session_id}")
            # Use provided initial state, default to empty dict if None
            state_to_use = initial_state if initial_state is not None else {}
            logger.debug(f"Initial state for session {session_id}: {state_to_use}")

            session_obj = self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id_str,
                session_id=session_id,
                state=state_to_use # Use the prepared state
            )
            # Load history only for new sessions *after* creation
            await self._load_history_into_session(chat.id, session_obj)
        else:
            logger.info(f"Found existing ADK session: user_id={user_id_str}, session_id={session_id}")
            # TODO: Decide if history/state should be updated on existing sessions

        return session_obj

    def _format_db_messages_to_adk_events(self, messages: List["Message"]) -> List[Event]:
        """Formats DB Message list to a list of ADK Event objects."""
        formatted_events: List[Event] = []
        if not messages:
            return formatted_events
        # Find the index of the first user message
        first_user_index = -1
        for i, msg in enumerate(messages):
            if msg.sender_type == 'user':
                first_user_index = i
                break
        # Process messages starting from the first user message, or all if no user message
        process_from_index = first_user_index if first_user_index != -1 else 0

        for msg in messages[process_from_index:]:
            role = 'model' if msg.sender_type == 'agent' else 'user'
            content_text = msg.content if msg.content is not None else ""
            # Create ADK Content object
            adk_content = Content(role=role, parts=[Part(text=content_text)])
            # Use message creation timestamp for the event
            event_timestamp = msg.created_at.timestamp()
            # Create ADK Event
            event = Event(author=role, content=adk_content, timestamp=event_timestamp)
            formatted_events.append(event)
        logger.debug(f"Formatted {len(formatted_events)} DB messages into ADK events.")
        return formatted_events

    async def _load_history_into_session(
        self,
        chat_id: PydanticObjectId,
        session_obj: Session
    ):
        """Loads chat history into the provided ADK session object."""
        session_id_for_log = str(chat_id)
        logger.debug(f"Loading history for session: {session_id_for_log}")
        start_time = time.time()

        # Fetch messages directly using injected chat_repository
        db_messages = await self.chat_repository.find_recent_messages_by_chat_id(
            chat_id=chat_id
        )
        # Format messages using the internal method
        adk_events = self._format_db_messages_to_adk_events(db_messages)

        if adk_events:
            for event in adk_events:
                self.session_service.append_event(session_obj, event)
            logger.info(f"Loaded {len(adk_events)} history events into session {session_id_for_log} in {time.time() - start_time:.2f}s")
        else:
            logger.info(f"No history events found to load for session {session_id_for_log}")

    def get_session_service(self) -> InMemorySessionService:
        """Returns the underlying session service instance."""
        return self.session_service

    # Potentially add methods for saving state, clearing sessions etc. if needed 