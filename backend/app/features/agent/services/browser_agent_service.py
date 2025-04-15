import traceback
from typing import TYPE_CHECKING, Optional, Tuple
from beanie import PydanticObjectId
from browser_use import Agent, Browser
from browser_use.browser.context import BrowserContext
from app.features.llm.services import LlmService

# Type checking imports
if TYPE_CHECKING:
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.chat.repositories import WebSocketRepository
    from app.features.agent.repositories import BrowserAgentRepository

class BrowserAgentService:
    """Handles the core agent logic after a user message is received."""

    def __init__(
        self,
        chat_service: "ChatService",
        websocket_service: "WebSocketService",
        websocket_repository: "WebSocketRepository",
        browser_agent_repository: "BrowserAgentRepository",
        llm_service: "LlmService"
    ):
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        self.websocket_repository = websocket_repository
        self.browser_agent_repository = browser_agent_repository
        self.llm_service = llm_service
        print("BrowserAgentService Initialized")

    # --- Agent Capabilities ---

    async def execute_browser_task(
        self, chat_id: PydanticObjectId, input_url: str, user_id: PydanticObjectId
    ) -> Tuple[str, Optional[Browser], Optional[BrowserContext]]:
        """Uses browser-use library to interact with a URL and returns the result string, browser, and context."""
        if not input_url:
            print(f"BrowserAgentService: Invalid or missing URL for chat {chat_id}")
            return "[Error: Missing URL input]", None, None

        # --- Fetch the Chat object --- 
        chat = await self.chat_service.chat_repository.find_chat_by_id(chat_id)
        if not chat:
            print(f"BrowserAgentService Error: Chat {chat_id} not found.")
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
            sensitive_data = self.browser_agent_repository._get_sensitive_data()
            execution_llm, planner_llm = self.browser_agent_repository._get_llm_config()
            task_description = self.browser_agent_repository._construct_task_description(input_url)

            # --- Generate TOTP code *before* Agent init --- #
            generated_totp_code = None
            if 'trello_totp_secret' in sensitive_data and sensitive_data['trello_totp_secret']:
                generated_totp_code = self.browser_agent_repository._generate_totp_code(sensitive_data['trello_totp_secret'])
                if generated_totp_code:
                    sensitive_data['trello_totp_code'] = generated_totp_code # Add to sensitive data for agent
                    print(f"BrowserAgentService: Generated TOTP code: {generated_totp_code}")
                else:
                    print("BrowserAgentService Error: Failed to generate TOTP code, likely missing secret.")
                    # Cannot proceed without code if prompt expects it
                    return "[Error: Failed to generate Trello 2FA code]", None, None
            elif 'trello_totp_code' in task_description: # Check if prompt expects TOTP
                 print("BrowserAgentService Error: Trello TOTP secret not configured, but prompt requires it.")
                 return "[Error: Trello TOTP secret not configured for this task]", None, None
            # --- End TOTP Generation --- #

            # --- Get Browser and Context --- # Requires BrowserConfig internally
            browser, context = await self.browser_agent_repository.create_browser_context(user_id)
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
            await self.browser_agent_repository.save_screenshots_from_history(chat_id, history)
            result_text = self.browser_agent_repository.extract_result_from_history(history)
            # --- End Process Results --- #

            # Send final success message
            await self.chat_service._create_and_broadcast_message(
                 chat=chat, sender_type='agent', content=result_text, message_type='text'
            )

            return result_text, browser, context

        except Exception as e: # Catch exceptions within the task
            print(f"BrowserAgentService: Error during browser interaction for chat {chat_id}: {e}")
            error_str = traceback.format_exc()
            error_message = f"[Error during browser task: {e}]"
            # Send final error message
            await self.chat_service._create_and_broadcast_message(
                 chat=chat, sender_type='agent', content=error_message, message_type='error'
            )
            return error_message, browser, context

    async def _cleanup_browser_resources(self, browser: Optional[Browser], context: Optional[BrowserContext]):
        """Safely close browser context and browser if they exist."""
        if context:
            await context.close()
            print("BrowserAgentService: Closed BrowserContext")
        if browser:
            await browser.close()
            print("BrowserAgentService: Closed Browser")
