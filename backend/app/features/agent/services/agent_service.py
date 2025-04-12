import asyncio
import json
import traceback
from typing import TYPE_CHECKING
from beanie import PydanticObjectId

from app.features.chat.models import Chat
from app.features.user.models import User
from app.features.agent.schemas import InputSourceType

# Type checking imports
if TYPE_CHECKING:
    from fastapi import WebSocket
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.chat.repositories import WebSocketRepository
    from app.features.agent.services import TaskService
    from app.features.agent.repositories import TaskRepository
    from app.features.llm.services import LlmService
    # Potentially import specific Google AI types if needed and stable


class AgentService:
    """Handles the core agent logic after a user message is received."""

    def __init__(
        self,
        chat_service: "ChatService",
        websocket_service: "WebSocketService",
        websocket_repository: "WebSocketRepository",
        task_repo: "TaskRepository",
        task_service: "TaskService",
        llm_service: "LlmService"
    ):
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        self.websocket_repository = websocket_repository
        self.task_repo = task_repo
        self.task_service = task_service
        self.llm_service = llm_service
        print("AgentService Initialized")

    async def _create_agent_message_json(self, content: str, msg_type: str = 'text') -> str:
        """Helper to create a JSON string for an agent message (moved from controller)."""
        # Reusing the helper from controller for consistency
        from app.features.chat.schemas import MessageData # Local import ok here
        from datetime import datetime, timezone
        msg_data = MessageData(
            id=PydanticObjectId(),
            sender_type='agent',
            content=content,
            created_at=datetime.now(timezone.utc),
            type=msg_type
        )
        return msg_data.model_dump_json(by_alias=True, exclude_none=True)

    async def _handle_task_command(
        self,
        command_content: str,
        chat: Chat,
        user: User,
        websocket: "WebSocket" 
    ):
        """Handles the logic for creating and starting a task from a command."""
        if not command_content:
            error_msg_json = await self._create_agent_message_json("Please provide input for the /task command.", msg_type='error')
            await self.websocket_service.send_personal_message(websocket, error_msg_json)
            return
        
        # Determine input type
        is_url = command_content.startswith("http://") or command_content.startswith("https://")
        input_type = InputSourceType.TRELLO if is_url and "trello.com" in command_content else \
                     InputSourceType.GOOGLE_DOC if is_url and "docs.google.com" in command_content else \
                     InputSourceType.TEXT
        print(f"AgentService: Detected /task command. Input type: {input_type.value}")
        
        # Send acknowledgement (personal)
        ack_message = f"Received task command. Input: {command_content[:50]}..."
        ack_msg_json = await self._create_agent_message_json(ack_message, msg_type='text')
        await self.websocket_service.send_personal_message(websocket, ack_msg_json)
        
        # Create the task
        task_create_data = { 
            "chat_id": chat.id,
            "user_id": user.id,
            "input_source_type": input_type,
            "input_data": command_content 
        }
        new_task = await self.task_repo.create_task(task_create_data)
        print(f"AgentService: Created Task {new_task.id}")
        
        # Start task execution
        self.task_service.start_task_execution(new_task.id)

    async def _handle_chat_message(
        self,
        user_content: str,
        chat: Chat,
        websocket: "WebSocket" # Keep websocket for personal error messages
    ):
        """Handles regular chat messages using the LLM, fetching history each time."""
        print(f"AgentService: Handling chat message: {user_content[:50]}...")
        connection_id = str(chat.id)

        # 1. Fetch necessary history for this request
        history_limit = 20 # Or make configurable
        recent_messages = await self.chat_service.get_recent_messages(chat.id, limit=history_limit)
        
        # 2. Create initial agent message placeholder in DB
        initial_agent_message = await self.chat_service._create_and_broadcast_message(
            chat=chat,
            sender_type='agent',
            content="",
            message_type='text'
        )
        if not initial_agent_message:
             print("AgentService: Failed to create initial agent message placeholder.")
             error_msg_json = await self._create_agent_message_json("Error processing request.", msg_type='error')
             # Use websocket passed into this method
             await self.websocket_service.send_personal_message(websocket, error_msg_json)
             return # Exit if placeholder fails
         
        agent_message_id = initial_agent_message.id
        print(f"AgentService: Initial agent message ID: {agent_message_id}")

        # 3. Generate response stream using history and current message
        full_response_content = ""
        try:
            async for chunk in self.llm_service.generate_response_stream(
                history_messages=recent_messages, # Pass fetched history
                current_message=user_content # Pass current user message
            ):
                full_response_content += chunk
                update_payload = {
                    "type": "MESSAGE_UPDATE", 
                    "message_id": str(agent_message_id),
                    "chunk": chunk
                }
                await self.websocket_repository.broadcast_to_chat(
                    message=json.dumps(update_payload), 
                    chat_id=connection_id
                )
                await asyncio.sleep(0.01)
            
            # 4. Update DB message with full content
            print(f"AgentService: Stream finished. Updating message {agent_message_id} with final content.")
            await self.chat_service.update_message_content(agent_message_id, full_response_content)
            # Send STREAM_END message
            end_payload = {"type": "STREAM_END", "message_id": str(agent_message_id)}
            await self.websocket_repository.broadcast_to_chat(
                message=json.dumps(end_payload), 
                chat_id=connection_id
            )

        except Exception as stream_error:
            print(f"AgentService: Error during stream processing: {stream_error}")
            error_db_content = "[Error during response generation]"
            await self.chat_service.update_message_content(agent_message_id, error_db_content)
            error_update_payload = {
                "type": "MESSAGE_UPDATE", 
                "message_id": str(agent_message_id),
                "chunk": " [Error processing response]",
                "is_error": True
            }
            await self.websocket_repository.broadcast_to_chat(
                message=json.dumps(error_update_payload), 
                chat_id=connection_id
            )
            end_payload = {"type": "STREAM_END", "message_id": str(agent_message_id)}
            await self.websocket_repository.broadcast_to_chat(
                message=json.dumps(end_payload), 
                chat_id=connection_id
            )
        
        # No need to return the chat session anymore

    async def process_user_input(
        self,
        user_content: str,
        chat: Chat, 
        user: User,
        websocket: "WebSocket"
        # Remove genai_chat_session parameter
    ) -> None: # Return type is now None
        """Determines action based on user input (task command or chat) and executes."""
        
        # Remove session state handling
        # original_session = genai_chat_session

        try:
            if user_content.lower().startswith("/task "):
                command_content = user_content[len("/task "):].strip()
                await self._handle_task_command(
                    command_content=command_content,
                    chat=chat,
                    user=user,
                    websocket=websocket
                )
                # No session state to return
            else:
                # Call the chat message handler, no session state involved here
                await self._handle_chat_message(
                    user_content=user_content,
                    chat=chat,
                    websocket=websocket
                )
        except Exception as e:
            # ... (Top-level error handling remains similar) ...
            error_content = "An internal error occurred while processing your request in the agent."
            print(f"AgentService: Top-level error processing input for chat {chat.id}: {e}")
            traceback.print_exc()
            try:
                 error_msg_json = await self._create_agent_message_json(error_content, msg_type='error')
                 await self.websocket_service.send_personal_message(websocket, error_msg_json)
            except Exception as send_err:
                 print(f"AgentService: Failed to send top-level error message back to user: {send_err}")
            # No session state to return