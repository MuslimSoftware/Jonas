from fastapi import WebSocket, WebSocketDisconnect, status
from beanie import PydanticObjectId
from pydantic import ValidationError
from typing import TYPE_CHECKING
import traceback
import json
from datetime import datetime, timezone

# Import schemas and dependencies
from app.features.chat.schemas import MessageCreate, MessageData
from app.features.agent import ConversationAction, InputSourceType, TaskData
from app.features.user.models import User

if TYPE_CHECKING:
    from app.features.chat.repositories import WebSocketRepository
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.agent.services import ConversationService, TaskService
    from app.features.agent.repositories import TaskRepository


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
        conversation_service: "ConversationService",
        task_repo: "TaskRepository",
        task_service: "TaskService"
    ):
        self.websocket = websocket
        self.chat_id_obj = chat_id_obj
        self.current_user = current_user
        self.websocket_repository = websocket_repository
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        self.conversation_service = conversation_service
        self.task_repo = task_repo
        self.task_service = task_service
        self.connection_id: str = str(chat_id_obj) # Store string version for repo

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
        """Processes a single incoming WebSocket message."""
        print(f"WS Controller: Processing data from {self.current_user.id}: {data[:100]}...")
        try:
            # 1. Validate incoming message format
            message_in = MessageCreate.model_validate_json(data)

            # 2. Broadcast "thinking" indicator immediately
            await self.chat_service.send_agent_thinking_message(self.chat_id_obj)

            # 3. Analyze message intent (potentially slow LLM call)
            # TODO: Pass actual chat history if needed
            action_result = await self.conversation_service.determine_next_action(
                user_message_content=message_in.content,
                chat_id=self.connection_id,
                user_id=self.current_user.id,
                chat_history=None
            )
            action = action_result.get("action")
            response_content = action_result.get("response_content")
            task_details = action_result.get("task_details")

            # 4. Act based on the determined action
            if action == ConversationAction.SAVE_MESSAGE_ONLY:
                # Save the user message (broadcast happens via ChatService)
                await self.chat_service.add_message_to_chat(
                    chat_id=self.chat_id_obj,
                    message_data=message_in,
                    current_user_id=self.current_user.id
                )
                
                # Check if ConversationService provided a chat response
                if response_content:
                    # Create JSON string matching MessageData format
                    message_json = await self._create_agent_message_json(response_content, msg_type='text')
                    await self.websocket_service.send_personal_message(self.websocket, message_json)
                # else: No explicit chat response from LLM, do nothing extra
            
            elif action == ConversationAction.ASK_CLARIFICATION:
                await self.chat_service.add_message_to_chat(
                    chat_id=self.chat_id_obj,
                    message_data=message_in,
                    current_user_id=self.current_user.id
                )
                if response_content:
                    message_json = await self._create_agent_message_json(response_content, msg_type='text')
                    await self.websocket_service.send_personal_message(self.websocket, message_json)
            elif action == ConversationAction.CREATE_AND_START_TASK:
                await self.chat_service.add_message_to_chat(
                    chat_id=self.chat_id_obj,
                    message_data=message_in,
                    current_user_id=self.current_user.id
                )
                if response_content:
                    message_json = await self._create_agent_message_json(response_content, msg_type='text')
                    await self.websocket_service.send_personal_message(self.websocket, message_json)
                if task_details:
                    task_create_data = {
                        "chat_id": self.chat_id_obj,
                        "user_id": self.current_user.id,
                        "input_source_type": InputSourceType(task_details.get("input_source_type", "TEXT")),
                        "input_data": task_details.get("input_data")
                    }
                    new_task = await self.task_repo.create_task(task_create_data)
                    print(f"WS Controller: Created Task {new_task.id}")
                    self.task_service.start_task_execution(new_task.id)
                else:
                    print("WS Controller: Error - CREATE_AND_START_TASK missing task_details.")
                    message_json = await self._create_agent_message_json("Internal error: Could not extract task details.", msg_type='error')
                    await self.websocket_service.send_personal_message(self.websocket, message_json) 
            elif action == ConversationAction.ERROR:
                error_content = response_content or "An error occurred during analysis."
                print(f"WS Controller: ConversationService analysis failed. Error: {error_content}")
                message_json = await self._create_agent_message_json(error_content, msg_type='error')
                await self.websocket_service.send_personal_message(self.websocket, message_json)

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