from typing import TYPE_CHECKING, Optional, Dict, Any, AsyncGenerator
from beanie import PydanticObjectId
import logging
from enum import Enum
from pydantic import BaseModel

# Import the specific agent instance we want to use for now
from app.agents.jonas_agent import jonas_agent

# Import schemas from the new file (one level up)
from ..schemas import AgentOutputType, AgentOutputEvent

if TYPE_CHECKING:
    from app.features.chat.models import Chat
    # Add WebSocketService here
    from app.features.chat.services import ChatService, WebSocketService
    # Correct the import path if services/repositories are in different subdirs
    from .adk_service import ADKService
    from ..repositories.adk_repository import ADKRepository

logger = logging.getLogger(__name__)

class AgentService:
    """Service layer for managing and interacting with different agents, handles broadcasting."""

    def __init__(
        self,
        adk_service: "ADKService",
        websocket_service: "WebSocketService",
    ):
        self.adk_service = adk_service
        self.websocket_service = websocket_service
        logger.info(f"AgentService initialized.")

    async def process_user_message(
        self,
        chat: "Chat",
        user_id: PydanticObjectId,
        user_content: str,
        connection_id: str,
    ) -> None: # No longer an async generator
        """
        Processes a user message using the jonas_agent via ADKService,
        handles the output events, and broadcasts updates via WebSocketService.
        """
        # Use agent name directly in log for clarity
        agent_name = jonas_agent.name # Get name from the instance
        logger.info(f"Processing message for chat {chat.id} (connection: {connection_id}) with agent '{agent_name}'")

        # Agent instance check is removed as we use the imported one directly

        # 2. Run the agent turn via ADKService and handle events internally
        try:
            # Directly use the imported jonas_agent instance
            async for event in self.adk_service.run_agent_turn(
                chat=chat,
                user_id=user_id,
                user_content=user_content
            ):
                logger.debug(f"AgentService Handling Event: Type={event.type}, MsgId={event.message_id}, Content='{str(event.content)[:50]}...'")
                # Handle broadcasting based on event type
                if event.type == AgentOutputType.STREAM_START:
                    if event.message_id and event.content:
                         await self.websocket_service.broadcast_message_update(
                             chat_id=connection_id,
                             message_id=str(event.message_id),
                             chunk=event.content,
                             is_error=False
                         )
                elif event.type == AgentOutputType.STREAM_CHUNK:
                    if event.message_id and event.content:
                         await self.websocket_service.broadcast_message_update(
                             chat_id=connection_id,
                             message_id=str(event.message_id),
                             chunk=event.content,
                             is_error=False
                         )
                elif event.type == AgentOutputType.STREAM_END:
                    if event.message_id:
                         if event.content:
                             await self.websocket_service.broadcast_message_update(
                                 chat_id=connection_id,
                                 message_id=str(event.message_id),
                                 chunk=event.content,
                                 is_error=False
                             )
                         await self.websocket_service.broadcast_stream_end(
                             chat_id=connection_id,
                             message_id=str(event.message_id)
                         )
                elif event.type == AgentOutputType.FINAL_MESSAGE:
                     # Message already created and broadcasted by ChatService via ADKService
                     logger.debug(f"AgentService: Final message event (ID: {event.message_id}). Broadcast handled.")
                     pass
                elif event.type == AgentOutputType.DELEGATION:
                     # Action message already created and broadcasted by ChatService via ADKService
                     logger.debug(f"AgentService: Delegation event (MsgID: {event.message_id}). Broadcast handled.")
                     pass
                elif event.type == AgentOutputType.ERROR:
                     # Error message already created and broadcasted by ChatService via ADKService
                     logger.error(f"AgentService: Error event from ADKService: {event.content}")
                     # Potentially stop processing further events if needed?
                     pass

            logger.info(f"Finished processing message for chat {chat.id} (connection: {connection_id}) with agent '{agent_name}'")

        except Exception as e:
            logger.exception(f"AgentService: Unhandled error during agent processing for chat {chat.id}: {e}")
            # How to report this error back to the specific user?
            # ADKService already tries to create a DB message and yields an ERROR event handled above.
            # This catches errors within AgentService itself or the loop.
            # Maybe broadcast a generic error via websocket_service?
            try:
                 error_text = "An unexpected error occurred in the agent service."
                 # Use broadcast_message_update for errors, potentially without message_id for general errors
                 # Or create a dedicated error broadcast method in WebSocketService
                 await self.websocket_service.broadcast_message_update(
                     chat_id=connection_id,
                     message_id=None, # No specific message ID for this general error
                     chunk=error_text, # Send error text as the chunk
                     is_error=True
                 )
            except Exception as broadcast_err:
                 logger.error(f"AgentService: Failed to broadcast unhandled exception to {connection_id}: {broadcast_err}")