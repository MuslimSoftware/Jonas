from typing import TYPE_CHECKING
import json
from fastapi import WebSocket
if TYPE_CHECKING:
    from app.features.chat.repositories import WebSocketRepository

class WebSocketService:
    """Handles broadcasting messages via WebSockets."""

    def __init__(self, websocket_repository: "WebSocketRepository"):
        self.websocket_repository: WebSocketRepository = websocket_repository

    async def broadcast_to_chat(self, chat_id: str, message_type: str, payload: dict):
        """Broadcasts a structured message to all connections in a chat room."""
        # Define a standard message format
        standard_message = {
            "type": message_type,
            "payload": payload
        }
        message_json = json.dumps(standard_message)
        try:
            await self.websocket_repository.broadcast_to_chat(
                message=message_json,
                chat_id=chat_id
            )
            print(f"WebSocketService: Broadcasted {message_type} to chat {chat_id}")
        except Exception as e:
            print(f"WebSocketService: Failed to broadcast {message_type} to chat {chat_id}: {e}")

    async def send_personal_message(self, websocket: WebSocket, message_json: str):
        """Sends a pre-formatted JSON message string to a specific WebSocket connection."""
        try:
            await websocket.send_text(message_json)
            # Log truncated message for brevity
            print(f"WebSocketService: Sent personal message: {message_json[:100]}...")
        except Exception as e:
            print(f"WebSocketService: Failed to send personal message: {e}") 