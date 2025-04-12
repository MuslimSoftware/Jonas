import asyncio
import json
import traceback
from typing import TYPE_CHECKING, Optional, Any
from beanie import PydanticObjectId
from pydantic import ValidationError

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

    async def process_user_input(
        self,
        user_content: str,
        chat: Chat, # DB chat object
        user: User,
        websocket: "WebSocket", # Needed for personal messages
        genai_chat_session: Optional[Any] # Pass current session
    ) -> Optional[Any]: # Return potentially updated session
        """Determines action based on user input (task command or chat) and executes."""
        
        updated_genai_chat_session = genai_chat_session # Start with the passed session
        connection_id = str(chat.id) # Get connection ID from chat
        
        try:
            if user_content.lower().startswith("/task "):
                # --- Handle Task Creation --- 
                command_content = user_content[len("/task "):].strip()
                if not command_content:
                    error_msg_json = await self._create_agent_message_json("Please provide input for the /task command.", msg_type='error')
                    await self.websocket_service.send_personal_message(websocket, error_msg_json)
                    return updated_genai_chat_session # Return original session
                
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
                
                # Create the task (TODO: Populate task data properly)
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
                # Task path doesn't modify the genai session
                return updated_genai_chat_session

            else:
                # --- Handle Regular Chat Message using Google AI Chat Session --- 
                print(f"AgentService: Regular message. Using GenAI chat for: {user_content[:50]}...")

                # 1. Ensure chat session exists, loading history if first time
                if not updated_genai_chat_session:
                    print("AgentService: No active GenAI chat session. Fetching history and creating...")
                    history_limit = 20 # Or make configurable
                    recent_messages = await self.chat_service.get_recent_messages(chat.id, limit=history_limit)
                    updated_genai_chat_session = self.llm_service.create_chat_session(history_messages=recent_messages)
                
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
                     await self.websocket_service.send_personal_message(websocket, error_msg_json)
                     return updated_genai_chat_session # Return potentially created session
                 
                agent_message_id = initial_agent_message.id
                print(f"AgentService: Initial agent message ID: {agent_message_id}")

                # 3. Send current message to session & stream response chunks
                full_response_content = ""
                try:
                    async for chunk in self.llm_service.send_message_to_chat_stream(
                        chat_session=updated_genai_chat_session, 
                        message=user_content
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
                    # Also send STREAM_END on error
                    end_payload = {"type": "STREAM_END", "message_id": str(agent_message_id)}
                    await self.websocket_repository.broadcast_to_chat(
                        message=json.dumps(end_payload), 
                        chat_id=connection_id
                    )
                
                # Return the session (might be newly created)
                return updated_genai_chat_session
                
        except Exception as e:
            # Catch-all for errors within agent processing
            error_content = "An internal error occurred while processing your request in the agent."
            print(f"AgentService: Error processing input for chat {chat.id}: {e}")
            traceback.print_exc()
            # Send error back to the specific user
            try:
                 error_msg_json = await self._create_agent_message_json(error_content, msg_type='error')
                 await self.websocket_service.send_personal_message(websocket, error_msg_json)
            except Exception as send_err:
                 print(f"AgentService: Failed to send error message back to user: {send_err}")
            # Return the session state we had before the error
            return genai_chat_session 