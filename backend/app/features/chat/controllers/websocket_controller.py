from fastapi import WebSocket, WebSocketDisconnect, status
from beanie import PydanticObjectId
from pydantic import ValidationError
from typing import TYPE_CHECKING, Optional, Any
import traceback
import json
from datetime import datetime, timezone
import asyncio

# Import schemas and dependencies
from app.features.chat.schemas import MessageCreate
from app.features.user.models import User
from app.features.chat.models import Chat
if TYPE_CHECKING:
    from app.features.chat.repositories import WebSocketRepository
    from app.features.chat.services import ChatService
    from app.features.agent.services import AgentService 


class WebSocketController:
    """Handles the WebSocket connection lifecycle and delegates processing to AgentService."""

    def __init__(
        self,
        websocket: WebSocket,
        chat_id_obj: PydanticObjectId,
        current_user: User,
        websocket_repository: "WebSocketRepository",
        chat_service: "ChatService",
        agent_service: "AgentService"
    ):
        self.websocket = websocket
        self.chat_id_obj = chat_id_obj
        self.current_user = current_user
        self.websocket_repository = websocket_repository
        self.chat_service = chat_service
        self.agent_service = agent_service
        self.connection_id: str = str(chat_id_obj)
        self.genai_chat_session: Optional[Any] = None

    async def handle_connect(self):
        """Accept connection and register it."""
        await self.websocket.accept()
        await self.websocket_repository.connect(self.websocket, self.connection_id)
        print(f"WS Controller: User {self.current_user.id} connected to chat {self.connection_id}")

    def handle_disconnect(self):
        """Unregister the connection."""
        self.websocket_repository.disconnect(self.websocket, self.connection_id)
        print(f"WS Controller: Cleaned up connection for user {self.current_user.id} from chat {self.connection_id}")


    async def _process_message(self, data: str):
        """Validates input, saves user message, delegates core processing to AgentService."""
        print(f"WS Controller: Processing data from {self.current_user.id}: {data[:100]}...")
        message_in: Optional[MessageCreate] = None
        chat: Optional[Chat] = None 
        try:
            # 1. Validate incoming message format
            message_in = MessageCreate.model_validate_json(data)
            user_content = message_in.content.strip()

            # 2. Fetch the Chat object
            chat = await self.chat_service.chat_repository.find_chat_by_id(self.chat_id_obj)
            if not chat:
                print(f"WS Controller: Error - Chat {self.chat_id_obj} not found.")
                # Consider sending a personal error message via websocket_service if needed
                return

            # 3. Save and broadcast the user's message
            await self.chat_service._create_and_broadcast_message(
                chat=chat,
                sender_type='user',
                content=user_content,
                message_type='text',
                author_id=self.current_user.id
            )

            # 4. Delegate processing to AgentService
            print(f"WS Controller: Delegating processing for content: {user_content[:50]}... to AgentService")
            # Pass necessary state (websocket for personal messages, current chat session)
            updated_session = await self.agent_service.process_user_input(
                user_content=user_content,
                chat=chat,
                user=self.current_user,
                websocket=self.websocket, # Pass the socket
                genai_chat_session=self.genai_chat_session # Pass current session
            )
            # Update the controller's session state
            self.genai_chat_session = updated_session
            print(f"WS Controller: AgentService processing complete.")

        except ValidationError as e:
            # Handle validation errors locally in the controller
            error_content = f"Invalid message format: {e}"
            print(f"WS Controller: Invalid message format from {self.current_user.id}: {e}")
            # Can't use _create_agent_message_json if removed, need alternative or inject WebSocketService
            # Simplified error sending for now:
            try:
                await self.websocket.send_text(json.dumps({"type": "error", "content": error_content}))
            except Exception as send_err:
                 print(f"WS Controller: Failed to send validation error to user: {send_err}")
                 
        except Exception as e:
            # Handle other errors during initial controller processing
            error_content = "An internal error occurred processing your message."
            print(f"WS Controller: Error before delegating to AgentService: {e}")
            traceback.print_exc()
            # Simplified error sending for now:
            try:
                await self.websocket.send_text(json.dumps({"type": "error", "content": error_content}))
            except Exception as send_err:
                 print(f"WS Controller: Failed to send general error to user: {send_err}")

    async def run_message_loop(self):
        """Receive and process messages in a loop."""
        try:
            while True:
                data = await self.websocket.receive_text()
                await self._process_message(data)
        except WebSocketDisconnect:
            print(f"WS Controller: WebSocket disconnected for user {self.current_user.id} (Code: {self.websocket.client_state})")
        except Exception as e:
            print(f"WS Controller: Unhandled error in message loop for user {self.current_user.id}: {e}")
            traceback.print_exc()
            try:
                await self.websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            except RuntimeError as re:
                print(f"WS Controller: Error closing websocket after loop error: {re}")
            raise e 