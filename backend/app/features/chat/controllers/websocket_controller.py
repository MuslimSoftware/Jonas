from fastapi import WebSocket, WebSocketDisconnect, status
from beanie import PydanticObjectId
from pydantic import ValidationError
from typing import TYPE_CHECKING, Optional, Any
import traceback
import json
from datetime import datetime, timezone
import asyncio

# Import schemas and dependencies
from app.features.chat.schemas import MessageCreate, MessageData
from app.features.agent import InputSourceType
from app.features.user.models import User
from app.features.chat.models import Chat
from app.features.agent.repositories import TaskRepository
from app.features.llm.services import LlmService

if TYPE_CHECKING:
    from app.features.chat.repositories import WebSocketRepository
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.agent.services import TaskService
    from app.features.agent.repositories import TaskRepository
    from app.features.llm.services import LlmService


class WebSocketController:
    """Handles the logic for an active WebSocket connection."""

    def __init__(
        self,
        websocket: WebSocket,
        chat_id_obj: PydanticObjectId,
        current_user: User,
        websocket_repository: "WebSocketRepository",
        chat_service: "ChatService",
        websocket_service: "WebSocketService",
        task_repo: "TaskRepository",
        task_service: "TaskService",
        llm_service: "LlmService"
    ):
        self.websocket = websocket
        self.chat_id_obj = chat_id_obj
        self.current_user = current_user
        self.websocket_repository = websocket_repository
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        self.task_repo = task_repo
        self.task_service = task_service
        self.llm_service = llm_service
        self.connection_id: str = str(chat_id_obj)
        self.genai_chat_session: Optional[Any] = None

    async def handle_connect(self):
        """Accept connection and register it."""
        await self.websocket.accept()
        await self.websocket_repository.connect(self.websocket, self.connection_id)
        print(f"WS Controller: User {self.current_user.id} connected to chat {self.connection_id}")

    def handle_disconnect(self):
        """Unregister the connection."""
        # Note: disconnect logic in repo is synchronous
        self.websocket_repository.disconnect(self.websocket, self.connection_id)
        print(f"WS Controller: Cleaned up connection for user {self.current_user.id} from chat {self.connection_id}")

    async def _create_agent_message_json(self, content: str, msg_type: str = 'text') -> str:
        """Helper to create a JSON string for an agent message."""
        # Create a MessageData-like structure for consistency
        msg_data = MessageData(
            id=PydanticObjectId(), # Temporary ID for frontend
            sender_type='agent',
            content=content,
            created_at=datetime.now(timezone.utc),
            type=msg_type # Use MessageType literal here
        )
        return msg_data.model_dump_json(by_alias=True, exclude_none=True)

    async def _process_message(self, data: str):
        """Processes incoming messages: validates, saves user msg, shows thinking, handles command/response/LLM chat."""
        print(f"WS Controller: Processing data from {self.current_user.id}: {data[:100]}...")
        message_in: Optional[MessageCreate] = None
        chat: Optional[Chat] = None # DB Chat model
        try:
            # 1. Validate incoming message format
            message_in = MessageCreate.model_validate_json(data)
            user_content = message_in.content.strip()

            # 2. Fetch the Chat object (needed for broadcasting)
            chat = await self.chat_service.chat_repository.find_chat_by_id(self.chat_id_obj)
            if not chat:
                print(f"WS Controller: Error - Chat {self.chat_id_obj} not found.")
                # Maybe send personal error? Depends on desired behavior.
                return

            # 3. Save and broadcast the user's message immediately
            await self.chat_service._create_and_broadcast_message(
                chat=chat,
                sender_type='user',
                content=user_content,
                message_type='text',
                author_id=self.current_user.id
            )

            # 4. Check if it's a task command
            if user_content.lower().startswith("/task "):
                # --- Handle Task Creation --- 
                command_content = user_content[len("/task "):].strip()
                if not command_content:
                    error_msg_json = await self._create_agent_message_json("Please provide input for the /task command.", msg_type='error')
                    await self.websocket_service.send_personal_message(self.websocket, error_msg_json)
                    return
                is_url = command_content.startswith("http://") or command_content.startswith("https://")
                input_type = InputSourceType.TRELLO if is_url and "trello.com" in command_content else \
                             InputSourceType.GOOGLE_DOC if is_url and "docs.google.com" in command_content else \
                             InputSourceType.TEXT
                ack_message = f"Received task command. Input: {command_content[:50]}..."
                ack_msg_json = await self._create_agent_message_json(ack_message, msg_type='text')
                await self.websocket_service.send_personal_message(self.websocket, ack_msg_json)
                task_create_data = {} # TODO: Populate task data
                new_task = await self.task_repo.create_task(task_create_data)
                print(f"WS Controller: Created Task {new_task.id}")
                self.task_service.start_task_execution(new_task.id)

            else:
                # --- Handle Regular Chat Message using Google AI Chat Session --- 
                print(f"WS Controller: Regular message. Using GenAI chat for: {user_content[:50]}...")

                # 1. Ensure chat session exists
                if not self.genai_chat_session:
                    print("WS Controller: No active GenAI chat session, creating one...")
                    self.genai_chat_session = self.llm_service.create_chat_session()

                # 2. Create initial agent message in DB to get an ID
                initial_agent_message = await self.chat_service._create_and_broadcast_message(
                    chat=chat, # DB Chat model
                    sender_type='agent',
                    content="", # Start with empty content
                    message_type='text' # Still a text message, just streamed
                )
                if not initial_agent_message:
                     print("WS Controller: Failed to create initial agent message placeholder.")
                     # Send an error back to the user?
                     error_msg_json = await self._create_agent_message_json("Error starting stream.", msg_type='error')
                     await self.websocket_service.send_personal_message(self.websocket, error_msg_json)
                     return
                 
                agent_message_id = initial_agent_message.id
                print(f"WS Controller: Initial agent message ID: {agent_message_id}")

                # 3. Stream response chunks and broadcast updates
                full_response_content = ""
                try:
                    async for chunk in self.llm_service.send_message_to_chat_stream(
                        chat_session=self.genai_chat_session, 
                        message=user_content
                    ):
                        full_response_content += chunk
                        # Broadcast chunk update message
                        update_payload = {
                            "type": "MESSAGE_UPDATE", 
                            "message_id": str(agent_message_id),
                            "chunk": chunk
                        }
                        await self.websocket_repository.broadcast_to_chat(
                            message=json.dumps(update_payload), 
                            chat_id=self.connection_id
                        )
                        # Optional small delay to allow frontend processing
                        await asyncio.sleep(0.01) 

                    # 4. Update the message in the DB with the full content
                    print(f"WS Controller: Stream finished. Updating message {agent_message_id} with final content.")
                    await self.chat_service.update_message_content(agent_message_id, full_response_content)

                except Exception as stream_error:
                    print(f"WS Controller: Error during stream processing: {stream_error}")
                    # Update the message in the DB with an error message
                    error_db_content = "[Error during response generation]"
                    await self.chat_service.update_message_content(agent_message_id, error_db_content)
                    # Send final error update broadcast
                    error_update_payload = {
                        "type": "MESSAGE_UPDATE", 
                        "message_id": str(agent_message_id),
                        "chunk": " [Error processing response]",
                        "is_error": True # Add flag for frontend
                    }
                    await self.websocket_repository.broadcast_to_chat(
                        message=json.dumps(error_update_payload), 
                        chat_id=self.connection_id
                    )
        except ValidationError as e:
            error_content = f"Invalid message format: {e}"
            print(f"WS Controller: Invalid message format from {self.current_user.id}: {e}")
            message_json = await self._create_agent_message_json(error_content, msg_type='error')
            await self.websocket_service.send_personal_message(self.websocket, message_json)
        except Exception as e:
            error_content = "An internal error occurred processing your message."
            print(f"WS Controller: Error processing message from {self.current_user.id}: {e}")
            traceback.print_exc()
            message_json = await self._create_agent_message_json(error_content, msg_type='error')
            await self.websocket_service.send_personal_message(self.websocket, message_json)

    async def run_message_loop(self):
        """Receive and process messages in a loop."""
        try:
            while True:
                data = await self.websocket.receive_text()
                await self._process_message(data)
        except WebSocketDisconnect:
            print(f"WS Controller: WebSocket disconnected for user {self.current_user.id} (Code: {self.websocket.client_state})")
            # Disconnect handled in the main endpoint's finally block
        except Exception as e:
            # Log errors happening during receive/processing loop
            print(f"WS Controller: Unhandled error in message loop for user {self.current_user.id}: {e}")
            traceback.print_exc()
            # Attempt to close gracefully from server-side if possible
            try:
                await self.websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            except RuntimeError as re:
                print(f"WS Controller: Error closing websocket after loop error: {re}")
            # Re-raise the exception so the main endpoint's finally block runs
            raise e 