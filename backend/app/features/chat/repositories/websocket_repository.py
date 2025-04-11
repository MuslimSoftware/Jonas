from fastapi import WebSocket
from typing import Dict, List

# Renamed class
class WebSocketRepository:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: str):
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
        print(f"WebSocket connected to chat {chat_id}. Total: {len(self.active_connections[chat_id])}")

    def disconnect(self, websocket: WebSocket, chat_id: str):
        if chat_id in self.active_connections:
            if websocket in self.active_connections[chat_id]:
                self.active_connections[chat_id].remove(websocket)
                print(f"WebSocket disconnected from chat {chat_id}. Remaining: {len(self.active_connections[chat_id])}")
                if not self.active_connections[chat_id]:
                    del self.active_connections[chat_id]
            else:
                 print(f"WS disconnect: Socket already removed from chat {chat_id}.")
        else:
             print(f"WS disconnect: Chat room {chat_id} not found.")

    async def broadcast_to_chat(self, message: str, chat_id: str):
        if chat_id in self.active_connections:
            print(f"Broadcasting to chat {chat_id}: {message[:50]}...") # Log truncated message
            connections = self.active_connections[chat_id][:]
            disconnected_sockets = []
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error sending to websocket in chat {chat_id}: {e}. Disconnecting.")
                    disconnected_sockets.append(connection)
            
            # Use self.disconnect to ensure proper cleanup and logging
            for sock in disconnected_sockets:
                self.disconnect(sock, chat_id) # Call the disconnect method 