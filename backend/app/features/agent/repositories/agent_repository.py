import asyncio
import json
import traceback
import base64
import aiofiles
from typing import TYPE_CHECKING, Dict, Optional, Tuple, Any
from beanie import PydanticObjectId
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from app.config.env import settings
from browser_use import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
import pyotp

if TYPE_CHECKING:
    from app.config.dependencies import ScreenshotRepositoryDep
    # Import History type if available and stable from browser_use
    # from browser_use import History 

class AgentRepository:
    """Handles the execution of browser automation tasks using browser-use."""

    # No longer needs screenshot_repository directly if service handles saving
    def __init__(self, screenshot_repository: "ScreenshotRepositoryDep"):
        self.screenshot_repository = screenshot_repository
        print("AgentRepository Initialized")

    def _get_sensitive_data(self) -> Dict[str, str]:
        """Loads sensitive data (e.g., credentials) required for tasks."""
        credentials = {}
        if settings.TRELLO_USERNAME and settings.TRELLO_PASSWORD:
            credentials['trello_user'] = settings.TRELLO_USERNAME
            credentials['trello_pass'] = settings.TRELLO_PASSWORD
            print("AgentRepository: Loaded Trello credentials.")
        else:
            print("AgentRepository: Trello credentials not found in settings.")

        if settings.TRELLO_TOTP_SECRET:
            credentials['trello_totp_secret'] = settings.TRELLO_TOTP_SECRET
            print("AgentRepository: Loaded Trello TOTP secret.")

        return credentials

    def _get_llm_config(self) -> Tuple[ChatGoogleGenerativeAI, ChatGoogleGenerativeAI]:
        """Initializes and returns the LLM configurations for the agent."""
        execution_llm = ChatGoogleGenerativeAI(
            model=settings.AI_MODEL, # Use model from settings
            temperature=0,
            google_api_key=settings.AI_API_KEY # Use API key from settings
        )
        planner_llm = ChatGoogleGenerativeAI(
            model=settings.AI_MODEL, # Use model from settings
            temperature=0,
            google_api_key=settings.AI_API_KEY # Use API key from settings
        )
        return execution_llm, planner_llm

    async def create_browser_context(self) -> Tuple[Browser, BrowserContext]:
        """Creates and returns Browser and BrowserContext instances."""
        # --- Initialize Browser for Headless --- #
        browser_config = BrowserConfig(headless=True)
        browser = Browser(config=browser_config)
        
        # --- Configure Context --- #
        context_config = BrowserContextConfig(
            wait_for_network_idle_page_load_time=3.0 # Increase wait time
        )
        
        # Create a new context using the browser's new_context method
        browser_context = await browser.new_context(config=context_config)
        
        # --- End Browser Init --- #
        
        return browser, browser_context

    def _construct_task_description(self, input_url: str, credentials: Dict[str, str]) -> str:
        """Constructs the task description for Trello login with TOTP."""
        # Assuming TOTP is the primary method
        return (
            f"Your primary goal is to log into Trello and analyze the content at {input_url}. "
            f"1. Navigate to trello.com/login. "
            f"2. Enter the username **exactly** as specified by the value of '<secret>trello_user</secret>'. **Do not add '@example.com' or anything else.** Click Continue. "
            f"3. Enter the password 'trello_pass'. Click Log in. "
            f"4. The account uses 2FA. On the verification page, find the input field for the 6-digit authenticator code. "
            f"5. Enter the current 6-digit code using placeholder '<secret>trello_totp_code</secret>'. "
            f"6a. **Check the page immediately.** If you see an error message indicating the code was invalid or incorrect, **stop the task** and report 'TOTP code failed or expired'. "
            f"6. Click the button to submit the code (likely labelled 'Log in' or similar). "
            f"7. After submitting the code, **wait** for the main Trello boards page/dashboard to fully load. "
            f"8. **Verify** successful login by looking for a stable element like the main boards container, the header with user initials, or a 'Boards' button. "
            f"9. **Only after confirming successful login**, navigate to the target URL: {input_url}. "
            f"10. Once on the target URL page, thoroughly analyze its main content. Identify and summarize the key topics discussed. "
            f"IMPORTANT: Keep track of how many times you restart the login process (re-entering username). If you find yourself starting the login attempt (Step 2) for the second time without successfully reaching and analyzing the target URL (Step 10), stop the task and report that you are stuck in a login loop."
        )

    def _generate_totp_code(self, secret: str) -> Optional[str]:
        """Generates the current TOTP code using the provided secret."""
        if not secret:
            print("AgentRepository Error: TOTP secret is missing.")
            return None
        totp = pyotp.TOTP(secret)
        return totp.now()

    async def save_screenshots_from_history(self, chat_id: PydanticObjectId, history: Any):
        """Processes and saves screenshots from the browser_use History object."""
        try:
            screenshot_paths = history.screenshots()
            print(f"AgentRepository: Found {len(screenshot_paths)} screenshots for chat {chat_id}.")
            for index, image_data in enumerate(screenshot_paths):
                print(f"AgentRepository: Screenshot index {index}, type: {type(image_data)}, data start: {str(image_data)[:100]}")
                try: # Assuming image_data is base64 string
                    data_uri = f"data:image/png;base64,{image_data}"
                    await self.screenshot_repository.create_screenshot(
                        chat_id=chat_id,
                        image_data=data_uri
                    )
                except Exception as img_err:
                    print(f"AgentRepository: Error processing/saving screenshot index {index} for chat {chat_id}: {img_err}")
                    traceback.print_exc()
            print(f"AgentRepository: Finished saving screenshots for chat {chat_id}.")
        except Exception as e:
            print(f"AgentRepository: Error accessing or processing screenshots for chat {chat_id}: {e}")
            traceback.print_exc()

    def extract_result_from_history(self, history: Any) -> str:
        """Extracts the final text result from the browser_use History object."""
        try:
            result_text = history.final_result()
            if not result_text:
                extracted_content = history.extracted_content()
                result_text = extracted_content if extracted_content else "Agent ran, but no specific result was extracted."
            return result_text
        except Exception as e:
            print(f"AgentRepository: Error extracting result from history: {e}")
            traceback.print_exc()
            return "[Error extracting result from agent history]"