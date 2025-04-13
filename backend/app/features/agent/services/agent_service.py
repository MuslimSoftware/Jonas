import asyncio
import json
import traceback
from typing import TYPE_CHECKING
from beanie import PydanticObjectId

from app.features.chat.models import Chat
from app.features.user.models import User
# Import browser components
from browser_use import Browser, BrowserConfig, Agent
from browser_use import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
# App Settings Import
from app.config.env import settings
# Langchain LLM Import
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
# Other imports
import base64
import aiofiles

# Type checking imports
if TYPE_CHECKING:
    from fastapi import WebSocket
    # Import ScreenshotRepositoryDep for type hinting
    from app.config.dependencies import ScreenshotRepositoryDep
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.chat.repositories import WebSocketRepository
    from app.features.llm.services import LlmService
    # Potentially import specific Google AI types if needed and stable


class AgentService:
    """Handles the core agent logic after a user message is received."""

    def __init__(
        self,
        chat_service: "ChatService",
        websocket_service: "WebSocketService",
        websocket_repository: "WebSocketRepository",
        screenshot_repository: "ScreenshotRepositoryDep", # Inject new repo
        llm_service: "LlmService"
    ):
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        self.websocket_repository = websocket_repository
        self.screenshot_repository = screenshot_repository # Store repo
        self.llm_service = llm_service
        print("AgentService Initialized")

    # --- Agent Capabilities ---

    async def perform_browser_task(self, chat_id: PydanticObjectId, input_url: str) -> str:
        """Uses browser-use library to interact with a URL and returns the result string."""
        if not input_url:
            print(f"AgentService: Invalid or missing URL for chat {chat_id}")
            return "[Error: Missing URL input]"

        # --- Fetch the Chat object --- 
        chat = await self.chat_service.chat_repository.find_chat_by_id(chat_id)
        if not chat:
            print(f"AgentService Error: Chat {chat_id} not found in perform_browser_task.")
            return "[Error: Chat not found]"
        # --- End Fetch --- 

        print(f"AgentService: Starting Browser Interaction for chat {chat_id} with URL: {input_url}")
        # --- Initialize Browser for Headless --- #
        browser_config = BrowserConfig(headless=True)
        browser = Browser(config=browser_config)
        # --- Configure Context --- #
        context_config = BrowserContextConfig(
            wait_for_network_idle_page_load_time=3.0 # Increase wait time
        )
        browser_context = BrowserContext(browser=browser, config=context_config)
        # --- End Browser Init --- #

        # Send initial status message
        await self.chat_service._create_and_broadcast_message(
            chat=chat, sender_type='agent', content=f"Starting browser task for {input_url}...", message_type='text'
        )

        try:
            # --- Create LangChain LLM instance --- 
            model_name = self.llm_service.llm_repository.get_model_name()
            # Use a low temperature for deterministic browser tasks? Adjust if needed.
            langchain_llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0,
                google_api_key=settings.AI_API_KEY # Pass the API key
            )
            # --- End LLM instance --- 

            # TODO: Refine task description
            browser_task_description = f"Go to the URL {input_url} and describe the main content."
            
            print(f"AgentService: Initializing browser-use Agent with task: '{browser_task_description}' for chat {chat_id}")
            browser_agent = Agent(
                task=browser_task_description,
                llm=langchain_llm,
                browser_context=browser_context # Pass the configured context
            )

            print(f"AgentService: Running browser-use Agent for chat {chat_id}...")
            history = await browser_agent.run()
            print(f"AgentService: browser-use Agent finished for chat {chat_id}.")

            # --- Send Screenshots --- #
            screenshot_paths = history.screenshots()
            print(f"AgentService: Found {len(screenshot_paths)} screenshots.")
            for index, image_data in enumerate(screenshot_paths):
                # --- Add Debugging --- #
                print(f"AgentService: Screenshot index {index}, type: {type(image_data)}, data start: {str(image_data)[:100]}")
                # --- End Debugging --- #
                try:
                    # --- Assume image_data is already the Base64 string --- #
                    # image_data is the base64 string
                    data_uri = f"data:image/png;base64,{image_data}" # Create data URI
                    # --- Save Screenshot to DB --- #
                    await self.screenshot_repository.create_screenshot(
                        chat_id=chat_id, # Pass the ObjectId
                        image_data=data_uri
                    )
                    # --- End Save Screenshot --- #
                except Exception as img_err:
                    print(f"AgentService: Error processing/sending screenshot index {index}: {img_err}")
                    # --- Add Traceback --- #
                    traceback.print_exc()
                    # --- End Traceback --- #

            # TODO: Get and process actual results from browser_agent
            # --- Extract result from history --- #
            result_text = history.final_result()
            if not result_text:
                # Fallback or check other history methods if needed
                extracted_content = history.extracted_content()
                result_text = extracted_content if extracted_content else "Agent ran, but no specific result was extracted."
            # --- End Extract Result --- #

            # Send final success message (Moved back here)
            await self.chat_service._create_and_broadcast_message(
                 chat=chat, sender_type='agent', content=result_text, message_type='text'
            )
            return result_text

        except Exception as e: # Catch exceptions within the task
            print(f"AgentService: Error during browser interaction for chat {chat_id}: {e}")
            error_str = traceback.format_exc()
            error_message = f"[Error during browser task: {e}]"
            # Send final error message
            await self.chat_service._create_and_broadcast_message(
                 chat=chat, sender_type='agent', content=error_message, message_type='error'
            )
            return error_message

        finally:
            # --- Close Context and Browser --- #
            print(f"AgentService: Closing browser context for chat {chat_id}.")
            await browser_context.close()
            print(f"AgentService: Context closed for chat {chat_id}.")
            print(f"AgentService: Closing browser for chat {chat_id}.")
            await browser.close()
            print(f"AgentService: Browser closed for chat {chat_id}.")
            # --- End Close --- #

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
        await self.perform_browser_task(
            chat_id=chat.id,
            input_url=command_content
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
        
        # No need to return the chat session anymore

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