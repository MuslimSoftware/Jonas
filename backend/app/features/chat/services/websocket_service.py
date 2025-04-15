import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.features.chat.repositories import WebSocketRepository

class WebSocketService:
    """Service responsible for formatting and broadcasting WebSocket messages."""
    def __init__(self, websocket_repository: "WebSocketRepository"):
        self.websocket_repository = websocket_repository
        print("WebSocketService Initialized")

    async def broadcast_message_update(
        self,
        chat_id: str,
        message_id: str,
        chunk: str,
        is_error: bool = False
    ):
        """Formats and broadcasts a message chunk update."""
        payload = {
            "type": "MESSAGE_UPDATE",
            "message_id": message_id,
            "chunk": chunk,
            "is_error": is_error
        }
        try:
            await self.websocket_repository.broadcast_to_chat(
                message=json.dumps(payload),
                chat_id=chat_id
            )
        except Exception as e:
            print(f"WebSocketService: Error broadcasting message update to chat {chat_id}: {e}")
            # Consider re-raising or logging more formally

    async def broadcast_stream_end(
        self,
        chat_id: str,
        message_id: str
    ):
        """Formats and broadcasts a stream end signal."""
        payload = {
            "type": "STREAM_END",
            "message_id": message_id
        }
        try:
            await self.websocket_repository.broadcast_to_chat(
                message=json.dumps(payload),
                chat_id=chat_id
            )
        except Exception as e:
            print(f"WebSocketService: Error broadcasting stream end to chat {chat_id}: {e}")
            # Consider re-raising or logging more formally 