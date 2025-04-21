from fastapi import WebSocket, WebSocketDisconnect, status
from beanie import PydanticObjectId
from pydantic import ValidationError
from typing import TYPE_CHECKING, Optional
import traceback
import json

from app.features.chat.schemas.chat_schemas import MessageCreate
from app.features.user.models import User
from app.features.chat.models import Chat

# Import JonasService for type hinting and JonasServiceDep for injection
from app.features.jonas.services import JonasService

if TYPE_CHECKING:
    from app.features.chat.repositories import WebSocketRepository
    from app.features.chat.services import ChatService, WebSocketService


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
        jonas_service: "JonasService", # Inject JonasService
    ):
        self.websocket = websocket
        self.chat_id_obj = chat_id_obj
        self.current_user = current_user
        self.websocket_repository = websocket_repository
        self.chat_service = chat_service
        self.websocket_service = websocket_service  # Store injected service
        self.jonas_service = jonas_service # Store injected JonasService
        self.connection_id: str = str(chat_id_obj)

    async def handle_connect(self):
        """Accept connection and register it."""
        await self.websocket.accept()
        await self.websocket_repository.connect(self.websocket, self.connection_id)

    def handle_disconnect(self):
        """Unregister the connection."""
        self.websocket_repository.disconnect(self.websocket, self.connection_id)

    async def _process_message(self, data: str):
        """Validates input, saves user message, delegates processing to Jonas."""
        message_in: Optional[MessageCreate] = None
        chat: Optional[Chat] = None
        
        try:
            # 1. Validate incoming message format
            message_in = MessageCreate.model_validate_json(data)
            user_content = message_in.content.strip()

            # 2. Fetch the Chat object
            chat = await self.chat_service.chat_repository.find_chat_by_id(
                self.chat_id_obj
            )
            if not chat:
                print(
                    f"WS Controller: Error - Chat {self.chat_id_obj} not found."
                )
                raise Exception(f"Chat {self.chat_id_obj} not found.")
                return

            # 3. Save and broadcast the user's message
            await self.chat_service._create_and_broadcast_message(
                chat=chat,
                sender_type='user',
                content=user_content,
                message_type='text',
                author_id=self.current_user.id,
            )
            
            # 4. Process input via Jonas Service
            await self.jonas_service.process_chat_message(
                chat=chat,
                user_content=user_content,
                user_id=self.current_user.id
            )

        except ValidationError as e:
            error_content = f"Invalid message format: {e}"
            print(
                f"WS Controller: Invalid message format from {self.current_user.id}: {e}"
            )
            try:
                await self.websocket.send_text(
                    json.dumps({"type": "error", "content": error_content})
                )
            except Exception as send_err:
                print(
                    f"WS Controller: Failed to send validation error to user: {send_err}"
                )

        except Exception as e:
            error_content = "An internal error occurred processing your message."
            print(
                f"WS Controller: Error during agent processing or message handling: {e}"
            )
            traceback.print_exc()
            # Attempt to send an error message back via WS
            try:
                # Try creating a final error message in the chat if possible
                if chat:
                    await self.chat_service._create_and_broadcast_message(
                        chat=chat,
                        sender_type='agent',
                        content=error_content,
                        message_type='error',
                    )
                else: # Fallback if chat object wasn't available
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
            print(
                f"WS Controller: WebSocket disconnected for user {self.current_user.id} (Code: {self.websocket.client_state})"
            )
        except Exception as e:
            print(
                f"WS Controller: Unhandled error in message loop for user {self.current_user.id}: {e}"
            )
            traceback.print_exc()
            # Ensure disconnection cleanup happens even after loop error
            self.handle_disconnect()
            # Attempt to close gracefully if possible
            try:
                if self.websocket.client_state != status.WS_STATE_DISCONNECTED:
                     await self.websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            except RuntimeError as re:
                print(
                    f"WS Controller: Error closing websocket after loop error: {re}"
                )
            # Optionally re-raise e if the main endpoint should handle it
            # raise e # Commented out to prevent double handling if main endpoint catches too

# --- Chat Controller Endpoint (No changes needed here) --- 