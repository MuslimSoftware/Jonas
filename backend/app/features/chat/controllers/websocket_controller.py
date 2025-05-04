from fastapi import WebSocket, WebSocketDisconnect, status
from beanie import PydanticObjectId
from pydantic import ValidationError
from typing import TYPE_CHECKING, Optional
import traceback
import json
import logging # Add logging

from app.features.chat.schemas.chat_schemas import MessageCreate
from app.features.user.models import User
from app.features.chat.models import Chat

# Import AgentService instead of JonasService
from app.features.agent.services import AgentService, AgentOutputEvent, AgentOutputType

if TYPE_CHECKING:
    from app.features.chat.repositories import WebSocketRepository
    from app.features.chat.services import ChatService, WebSocketService
    # Remove JonasService import from TYPE_CHECKING if it was there

logger = logging.getLogger(__name__) # Setup logger

class WebSocketController:

    def __init__(
        self,
        websocket: WebSocket,
        chat_id_obj: PydanticObjectId,
        current_user: User,
        websocket_repository: "WebSocketRepository",
        chat_service: "ChatService",
        # Inject WebSocketService
        websocket_service: "WebSocketService",
        # Inject AgentService instead of JonasService
        agent_service: "AgentService",
    ):
        self.websocket = websocket
        self.chat_id_obj = chat_id_obj
        self.current_user = current_user
        self.websocket_repository = websocket_repository
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        # Store injected AgentService
        self.agent_service = agent_service
        self.connection_id: str = str(chat_id_obj)
        logger.info(f"WebSocketController initialized for chat {self.connection_id}") # Add log

    async def handle_connect(self):
        """Accept connection and register it."""
        await self.websocket.accept()
        await self.websocket_repository.connect(self.websocket, self.connection_id)
        logger.info(f"WebSocket connected for user {self.current_user.id} on chat {self.connection_id}") # Add log

    def handle_disconnect(self):
        """Unregister the connection."""
        self.websocket_repository.disconnect(self.websocket, self.connection_id)
        logger.info(f"WebSocket disconnected for user {self.current_user.id} on chat {self.connection_id}") # Add log

    async def _process_message(self, data: str):
        """Validates input, saves user message, delegates processing to AgentService and handles output events."""
        message_in: Optional[MessageCreate] = None
        chat: Optional[Chat] = None
        
        try:
            # 1. Validate incoming message format
            message_in = MessageCreate.model_validate_json(data)
            user_content = message_in.content.strip()
            logger.debug(f"WS Controller: Received valid message from user {self.current_user.id} for chat {self.chat_id_obj}: '{user_content[:50]}...'")

            # 2. Fetch the Chat object
            chat = await self.chat_service.chat_repository.find_chat_by_id(
                self.chat_id_obj
            )
            if not chat:
                # Log and send error back to client
                logger.error(f"WS Controller: Error - Chat {self.chat_id_obj} not found for user {self.current_user.id}.")
                await self.websocket.send_text(
                    json.dumps({"type": "error", "content": f"Chat {self.chat_id_obj} not found."})
                )
                return # Stop processing if chat not found

            # 3. Save and broadcast the user's message (No change here)
            logger.debug(f"WS Controller: Saving user message for chat {chat.id}")
            await self.chat_service._create_and_broadcast_message(
                chat=chat,
                sender_type='user',
                content=user_content,
                message_type='text',
                author_id=self.current_user.id,
            )
            
            # 4. Process input via Agent Service (AgentService now handles broadcasting)
            logger.info(f"WS Controller: Calling agent_service.process_user_message for chat {chat.id}")
            await self.agent_service.process_user_message(
                chat=chat,
                user_content=user_content,
                user_id=self.current_user.id,
                connection_id=self.connection_id
            )
            logger.info(f"WS Controller: agent_service.process_user_message completed for chat {chat.id}")

        except ValidationError as e:
            error_content = f"Invalid message format: {e}"
            logger.warning( # Log as warning, it's a client issue
                f"WS Controller: Invalid message format from {self.current_user.id} on chat {self.chat_id_obj}: {e}"
            )
            try:
                await self.websocket.send_text(
                    json.dumps({"type": "error", "content": error_content})
                )
            except Exception as send_err:
                logger.error(
                    f"WS Controller: Failed to send validation error to user {self.current_user.id}: {send_err}"
                )

        except Exception as e:
            error_content = "An internal error occurred processing your message."
            logger.exception( # Use logger.exception to include traceback
                f"WS Controller: Unhandled error during message processing for user {self.current_user.id} on chat {self.chat_id_obj}: {e}"
            )
            # Attempt to send an error message back via WS
            try:
                # We already created/broadcasted error messages from AgentService if possible.
                # This sends a direct WS message as a fallback.
                 await self.websocket.send_text(json.dumps({"type": "error", "content": error_content}))
            except Exception as send_err:
                 logger.error(f"WS Controller: Failed to send general error to user {self.current_user.id}: {send_err}")

    async def run_message_loop(self):
        """Receive and process messages in a loop."""
        try:
            while True:
                data = await self.websocket.receive_text()
                logger.debug(f"WS Controller: Raw message received on chat {self.connection_id}") # Log raw receive
                await self._process_message(data)
        except WebSocketDisconnect as e: # Catch disconnect specifically
            # Log the disconnect reason/code
            logger.info(
                f"WS Controller: WebSocket disconnected for user {self.current_user.id} on chat {self.connection_id} (Code: {e.code}, Reason: {e.reason})"
            )
            # Disconnect handled in finally block now
        except Exception as e:
            logger.exception( # Log exception with traceback
                f"WS Controller: Unhandled error in message loop for user {self.current_user.id} on chat {self.connection_id}: {e}"
            )
            # Ensure disconnection cleanup happens even after loop error
            # self.handle_disconnect() # Moved to finally
            # Attempt to close gracefully if possible
            try:
                if self.websocket.client_state != status.WS_STATE_DISCONNECTED:
                     logger.warning(f"WS Controller: Attempting to close websocket due to loop error.")
                     await self.websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            except RuntimeError as re:
                # This might happen if the connection is already closing
                 logger.warning(
                     f"WS Controller: Error closing websocket after loop error (might be expected if already closing): {re}"
                 )
            # Optionally re-raise e if the main endpoint should handle it
            # raise e # Commented out to prevent double handling

# --- Chat Controller Endpoint (No changes needed here) --- 