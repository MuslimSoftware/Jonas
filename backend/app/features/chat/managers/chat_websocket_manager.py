import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from beanie import PydanticObjectId
from pydantic import ValidationError
from typing import TYPE_CHECKING

from app.features.chat.schemas import MessageCreate
from app.features.user.models import User # Assuming user model location

if TYPE_CHECKING:
    from app.features.chat.services import ChatService
    from app.features.chat.repositories import ConnectionRepository

class ChatWebSocketManager:
    """Manages a single WebSocket connection for a chat session."""

    def __init__(
        self,
        websocket: WebSocket,
        chat_id: PydanticObjectId,
        user: User,
        chat_service: "ChatService",
        connection_repo: "ConnectionRepository",
    ):
        self.websocket = websocket
        self.chat_id = chat_id
        self.user = user
        self.chat_service = chat_service
        self.connection_repo = connection_repo
        self._is_connected = False # Internal state

    async def connect(self):
        """Accepts the WebSocket connection and registers it."""
        await self.websocket.accept()
        await self.connection_repo.connect(self.websocket, str(self.chat_id))
        self._is_connected = True
        print(f"Manager: User {self.user.id} connected to chat {self.chat_id}")

    async def disconnect(self):
        """Unregisters the WebSocket connection."""
        if self._is_connected:
            self.connection_repo.disconnect(self.websocket, str(self.chat_id))
            self._is_connected = False
            print(f"Manager: Cleaned up connection for user {self.user.id} from chat {self.chat_id}")

    async def _handle_received_data(self, data: str):
        """Handles incoming data from the WebSocket."""
        print(f"Manager: Received WS message from {self.user.id} in chat {self.chat_id}: {data[:100]}...") # Log truncated
        try:
            message_in = MessageCreate.model_validate_json(data)
            await self._process_user_message(message_in)

            # --- Trigger Agent Response ---
            # Placeholder for where agent logic would be invoked
            # await self._trigger_agent_response(message_in.content) 
            # -----------------------------

        except ValidationError as e:
            print(f"Manager: WS validation error for user {self.user.id} in chat {self.chat_id}: {e}")
            # Consider sending an error message back to the client
        except Exception as e:
            print(f"Manager: Error processing WS message from {self.user.id} in chat {self.chat_id}: {e}")
            # Consider sending an error message back to the client

    async def _process_user_message(self, message_in: MessageCreate):
        """Processes a validated user message."""
        # Use the service layer to save the message and broadcast
        await self.chat_service.add_message_to_chat(
            chat_id=self.chat_id,
            message_data=message_in,
            current_user_id=self.user.id
        )

    # Placeholder for future agent response triggering
    # async def _trigger_agent_response(self, user_content: str):
    #     print(f"Manager: Triggering agent response for chat {self.chat_id}...")
    #     # Example: Send thinking indicator
    #     await self.chat_service._create_and_broadcast_message(...) # type='thinking'
    #     # ... call actual agent logic ...
    #     # await self.chat_service._create_and_broadcast_message(...) # type='text', content=agent_response
    #     pass

    async def handle_connection(self):
        """Main loop to handle the WebSocket connection lifecycle."""
        await self.connect()
        try:
            while True:
                data = await self.websocket.receive_text()
                await self._handle_received_data(data)
        except WebSocketDisconnect:
            print(f"Manager: User {self.user.id} disconnected via WebSocketDisconnect.")
        except Exception as e:
            print(f"Manager: Error in WebSocket loop for user {self.user.id} in chat {self.chat_id}: {e}")
        finally:
            await self.disconnect() 