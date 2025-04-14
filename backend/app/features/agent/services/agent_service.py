import asyncio
import json
import traceback
from typing import TYPE_CHECKING, Optional, Tuple
from beanie import PydanticObjectId

from app.features.chat.models import Chat
from app.features.user.models import User
from browser_use import Agent, Browser
from browser_use.browser.context import BrowserContext
from app.features.llm.services import LlmService

# Type checking imports
if TYPE_CHECKING:
    from fastapi import WebSocket
    # Import ScreenshotRepositoryDep for type hinting
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.chat.repositories import WebSocketRepository
    from app.features.agent.repositories import AgentRepository # Import AgentRepository

class AgentService:
    """Handles the core agent logic after a user message is received."""

    def __init__(
        self,
        chat_service: "ChatService",
        websocket_service: "WebSocketService",
        websocket_repository: "WebSocketRepository",
        agent_repository: "AgentRepository", # Inject AgentRepository
        llm_service: "LlmService"
    ):
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        self.websocket_repository = websocket_repository
        self.agent_repository = agent_repository # Store AgentRepository
        self.llm_service = llm_service
        print("AgentService Initialized")

    # --- Agent Capabilities ---

    async def execute_browser_task(
        self, chat_id: PydanticObjectId, input_url: str, user_id: PydanticObjectId
    ) -> Tuple[str, Optional[Browser], Optional[BrowserContext]]:
        """Uses browser-use library to interact with a URL and returns the result string, browser, and context."""
        if not input_url:
            print(f"AgentService: Invalid or missing URL for chat {chat_id}")
            return "[Error: Missing URL input]", None, None

        # --- Fetch the Chat object --- 
        chat = await self.chat_service.chat_repository.find_chat_by_id(chat_id)
        if not chat:
            print(f"AgentService Error: Chat {chat_id} not found.")
            return "[Error: Chat not found]", None, None
        # --- End Fetch --- 

        # Send initial status message
        await self.chat_service._create_and_broadcast_message(
            chat=chat, sender_type='agent', content=f"Starting browser task for {input_url}...", message_type='text'
        )

        browser: Optional[Browser] = None
        context: Optional[BrowserContext] = None

        try:
            # --- Get Configuration from Repository --- #
            sensitive_data = self.agent_repository._get_sensitive_data()
            execution_llm, planner_llm = self.agent_repository._get_llm_config()
            task_description = self.agent_repository._construct_task_description(input_url)

            # --- Generate TOTP code *before* Agent init --- #
            generated_totp_code = None
            if 'trello_totp_secret' in sensitive_data and sensitive_data['trello_totp_secret']:
                generated_totp_code = self.agent_repository._generate_totp_code(sensitive_data['trello_totp_secret'])
                if generated_totp_code:
                    sensitive_data['trello_totp_code'] = generated_totp_code # Add to sensitive data for agent
                    print(f"AgentService: Generated TOTP code: {generated_totp_code}")
                else:
                    print("AgentService Error: Failed to generate TOTP code, likely missing secret.")
                    # Cannot proceed without code if prompt expects it
                    return "[Error: Failed to generate Trello 2FA code]", None, None
            elif 'trello_totp_code' in task_description: # Check if prompt expects TOTP
                 print("AgentService Error: Trello TOTP secret not configured, but prompt requires it.")
                 return "[Error: Trello TOTP secret not configured for this task]", None, None
            # --- End TOTP Generation --- #

            # --- Get Browser and Context --- # Requires BrowserConfig internally
            browser, context = await self.agent_repository.create_browser_context(user_id)
            # --- End Browser/Context Setup --- #

            browser_agent = Agent(
                task=task_description,
                llm=execution_llm, # LLM for action execution
                planner_llm=planner_llm, # LLM for planning
                browser_context=context, # Pass the created context
                use_vision_for_planner=False, # Don't use vision for planning steps
                sensitive_data=sensitive_data if sensitive_data else None
            )

            # --- Run the Agent --- #
            history = await browser_agent.run()
            # --- End Run --- #

            # --- Process Results --- #
            await self.agent_repository.save_screenshots_from_history(chat_id, history)
            result_text = self.agent_repository.extract_result_from_history(history)
            # --- End Process Results --- #

            # Send final success message
            await self.chat_service._create_and_broadcast_message(
                 chat=chat, sender_type='agent', content=result_text, message_type='text'
            )

            return result_text, browser, context

        except Exception as e: # Catch exceptions within the task
            print(f"AgentService: Error during browser interaction for chat {chat_id}: {e}")
            error_str = traceback.format_exc()
            error_message = f"[Error during browser task: {e}]"
            # Send final error message
            await self.chat_service._create_and_broadcast_message(
                 chat=chat, sender_type='agent', content=error_message, message_type='error'
            )
            return error_message, browser, context

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

    async def _cleanup_browser_resources(self, browser: Optional[Browser], context: Optional[BrowserContext]):
        """Safely close browser context and browser if they exist."""
        if context:
            await context.close()
            print("AgentService: Closed BrowserContext")
        if browser:
            await browser.close()
            print("AgentService: Closed Browser")

    async def _handle_task_command(
        self,
        command_content: str,
        chat: Chat,
        user: User,
        websocket: "WebSocket"
    ) -> None: # Return the result string or error message
        """Handles the /task command directly, runs browser interaction, returns result."""
        if not command_content:
            error_msg_json = await self._create_agent_message_json("Please provide input for the /task command.", msg_type='error')
            await self.websocket_service.send_personal_message(websocket, error_msg_json)
            return "[Error: Missing task input]"
        
        # Determine input type
        is_url = command_content.startswith("http://") or command_content.startswith("https://")

        if not is_url:
            # For now, only handle URL inputs
            error_msg = "Currently, /task command only supports URLs."
            error_msg_json = await self._create_agent_message_json(error_msg, msg_type='error')
            await self.websocket_service.send_personal_message(websocket, error_msg_json)
            return f"[Error: {error_msg}]"
            
        print(f"AgentService: Detected /task command with URL: {command_content}")
        
        # Send acknowledgement (personal)
        ack_message = f"Received task command. Input: {command_content[:50]}..."
        ack_msg_json = await self._create_agent_message_json(ack_message, msg_type='text')
        await self.websocket_service.send_personal_message(websocket, ack_msg_json)
        
        # Directly perform the browser task
        await self.execute_browser_task(
            chat_id=chat.id,
            input_url=command_content,
            user_id=user.id
        )

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

    async def process_user_input(
        self,
        user_content: str,
        chat: Chat, 
        user: User,
        websocket: "WebSocket"
    ) -> None: # No longer returns task ID
        """Determines action and executes it, sending final message if task."""
        
        try:
            if user_content.lower().startswith("/task "):
                command_content = user_content[len("/task "):].strip()
                # Run the task command handler and get the final result/error message
                await self._handle_task_command(
                    command_content=command_content,
                    chat=chat,
                    user=user,
                    websocket=websocket
                )
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