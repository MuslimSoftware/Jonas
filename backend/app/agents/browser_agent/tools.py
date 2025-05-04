import traceback
import pyotp
import logging
import os
import time
import re
from typing import Dict, Optional, Tuple, Any, List
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from browser_use import Agent as BrowserUseAgent, Browser, BrowserConfig
from browser_use.agent.views import AgentHistoryList
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from beanie import PydanticObjectId
from google.adk.tools import ToolContext

from app.config.env import settings
# Import ScreenshotRepository directly for saving within the tool
from app.features.chat.repositories import ScreenshotRepository

logger = logging.getLogger(__name__)

# --- Helper methods (Internal to this tool's logic) ---

def _get_sensitive_data() -> Dict[str, str]:
    """Loads sensitive data required for tasks."""
    credentials = {}
    if settings.TRELLO_USERNAME and settings.TRELLO_PASSWORD:
        credentials['trello_user'] = settings.TRELLO_USERNAME
        credentials['trello_pass'] = settings.TRELLO_PASSWORD
    if settings.TRELLO_TOTP_SECRET:
        credentials['trello_totp_secret'] = settings.TRELLO_TOTP_SECRET

    if settings.RESPRO_USERNAME and settings.RESPRO_PASSWORD:
        credentials['respro_user'] = settings.RESPRO_USERNAME
        credentials['respro_pass'] = settings.RESPRO_PASSWORD

    return credentials

def _get_llm_config() -> Tuple[ChatGoogleGenerativeAI, ChatGoogleGenerativeAI]:
    """Initializes LLM configurations."""
    execution_llm = ChatGoogleGenerativeAI(
        model=settings.BROWSER_EXECUTION_MODEL,
        temperature=0
    )
    planner_llm = ChatGoogleGenerativeAI(
        model=settings.BROWSER_PLANNER_MODEL,
        temperature=0
    )
    return execution_llm, planner_llm

def _construct_task_description(input_url: str) -> str:
    """Constructs the task description, including login handling instructions."""
    # This function defines the extraction goal after navigation/login.
    return f"""Your primary goal is to navigate to the target page ({input_url}), handle any necessary login, and then extract ALL meaningful text, links, and structured data elements (like lists, key-value pairs) from the main content area.

**--- Login Handling ---**
*   **General:** If you encounter a login page, use the credentials provided in the `sensitive_data` parameter (if available for the specific site) to log in *before* proceeding with extraction. The library often handles this automatically if the correct keys are present (e.g., `trello_user`, `respro_user`).
*   **Trello (`trello.com`):** If the URL is for Trello and you hit a login screen, use the `trello_user`, `trello_pass`, and `trello_totp_code` (if provided) from `sensitive_data` to complete the login.
*   **Reservations (`reservations.voyagesalacarte.ca`):** If the URL is for the reservations site and you hit a login screen, use the `respro_user` and `respro_pass` from `sensitive_data` to log in.
*   **After Login:** Once logged in (or if no login was required), check the current URL. If the login process redirected you away from the original `url` you were trying to access (e.g., to a homepage), **navigate back to the original `url` first**. Then, proceed to the extraction process on the correct page.

**--- Extraction Process (After Login/Navigation) ---**
1.  **Scan Content:** Thoroughly scan the primary content area of the page.
2.  **Identify Elements:** Identify distinct content elements such as:
    *   Main Title/Subject
    *   Headings (H1, H2, H3, etc.)
    *   Paragraphs of text
    *   Lists (ordered and unordered)
    *   Hyperlinks (URLs and their associated text)
    *   Key-value pairs (like metadata, attributes, form labels/values)
    *   Code blocks or preformatted text
    *   Explicit checklists or action items
3.  **Structure as JSON:** Organize ALL extracted elements into a single JSON object. Use descriptive keys. Examples:
    *   `"title": "Page Title"`
    *   `"headings": ["Section 1", "Subsection A"]`
    *   `"paragraphs": ["First paragraph text...", "Second paragraph text..."]`
    *   `"lists": [["Item 1", "Item 2"], ["Step A", "Step B"]]`
    *   `"links": [{{"text": "Link Text", "href": "URL"}}, ...]`
    *   `"attributes": {{ "Status": "Open", "Priority": "High" }}`
    *   `"code_blocks": ["code snippet 1", ...]`
    *   `"checklist_items": ["Do thing 1", "Do thing 2"]`

**IMPORTANT:**
- If you navigate to a https://reservations.voyagesalacarte.ca page, NEVER UNDER ANY CIRCUMSTANCES make any actions on the booking page, ONLY extract information.

**Output Requirement:**
Your *entire* response MUST be ONLY the raw string content of the single, valid JSON object you constructed. 
- Do NOT include markdown formatting like triple backticks (```json ... ```).
- Do NOT include any introductory or concluding text like "Here is the JSON:" or "The JSON data is...".
- Output ONLY the JSON object string itself, starting with {{ and ending with }} (or [ and ] if the root is an array, though an object is preferred).
"""

def _generate_totp_code(secret: str) -> Optional[str]:
    """Generates the current TOTP code."""
    if not secret: return None
    totp = pyotp.TOTP(secret)
    return totp.now()

def _get_cookie_file_path(unique_id: str) -> str:
    """Generates a unique file path for cookies. Accepts a string ID."""
    base_dir = "/app/cookies" # Ensure this exists
    # Create the base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True) 
    filename = f"{unique_id}_cookies.json"
    return os.path.join(base_dir, filename)

async def _save_screenshots(screenshot_repo: ScreenshotRepository, chat_id: PydanticObjectId, history: Any):
    """Processes and saves screenshots using the provided repository."""
    try:
        screenshot_data_list = history.screenshots() # Assuming returns list of base64
        logger.info(f"Tool: Found {len(screenshot_data_list)} screenshots for chat {chat_id}.")
        saved_count = 0
        for image_data in screenshot_data_list:
            try:
                # Assuming image_data is raw base64 from browser-use
                data_uri = f"data:image/png;base64,{image_data}"
                # Here we need the *actual* chat_id ObjectId for the repository
                await screenshot_repo.create_screenshot(chat_id=chat_id, image_data=data_uri)
                saved_count += 1
            except Exception as img_err:
                logger.error(f"Tool: Error saving screenshot for chat {chat_id}: {img_err}")
        logger.info(f"Tool: Saved {saved_count} screenshots for chat {chat_id}.")
    except Exception as e:
        logger.error(f"Tool: Error processing screenshots for chat {chat_id}: {e}")

def _extract_result(history: AgentHistoryList) -> Optional[str]:
    """Extracts the JSON string result from history, prioritizing extracted content."""
    try:
        extracted_content = history.extracted_content()
        final_result_text = history.final_result()

        # Try to find the JSON block within extracted_content if it's a list
        json_string = None
        if isinstance(extracted_content, list):
            logger.info(f"Tool: extracted_content is a list with {len(extracted_content)} items. Searching for JSON block.")
            for item in extracted_content:
                if isinstance(item, str):
                    # Use regex to find ```json ... ``` block
                    match = re.search(r"```json\n(.*?)\n```", item, re.DOTALL)
                    if match:
                        json_string = match.group(1).strip() # Extract content between backticks
                        logger.info("Tool: Found JSON block in extracted_content list item.")
                        break
        elif isinstance(extracted_content, str):
             # Check if the string itself is the JSON block or contains it
             match = re.search(r"```json\n(.*?)\n```", extracted_content, re.DOTALL)
             if match:
                 json_string = match.group(1).strip()
                 logger.info("Tool: Found JSON block in extracted_content string.")
             # Basic check if the string itself might be JSON
             elif extracted_content.strip().startswith('{') or extracted_content.strip().startswith('['):
                 json_string = extracted_content
                 logger.info("Tool: Treating extracted_content string as JSON.")

        if json_string:
            logger.info(f"Tool: Returning extracted JSON string: {json_string[:100]}...")
            return json_string
        elif final_result_text:
            # Fallback: Maybe the final result is the JSON?
            if isinstance(final_result_text, str) and (final_result_text.strip().startswith('{') or final_result_text.strip().startswith('[')):
                 logger.info("Tool: Using final_result as JSON (extracted_content was not JSON).")
                 return final_result_text
            else:
                 logger.info("Tool: Using final_result as fallback (non-JSON).")
                 # Don't return non-JSON fallback if we expect JSON
                 # return final_result_text 
                 pass # Let it fall through to None
        
        logger.warning("Tool: Agent ran, but no JSON content found in history.")
        return None # Return None if nothing suitable found

    except Exception as e:
        logger.error(f"Tool: Error extracting result from history: {e}", exc_info=True)
        # Return as JSON-like error string
        return f'{{"status": "error", "error_message": "Error extracting result: {e}"}}'

async def _cleanup_resources(browser: Optional[Browser], context: Optional[BrowserContext]):
    """Safely close browser resources."""
    closed_context = False
    if context:
        try: 
            await context.close()
            closed_context = True
            logger.info(f"Tool: Closed BrowserContext.")
        except Exception as e: logger.warning(f"Tool: Error closing context: {e}")
    if browser:
        try: 
            await browser.close()
            logger.info(f"Tool: Closed Browser.")
        except Exception as e: logger.warning(f"Tool: Error closing browser: {e}")
    return closed_context # Return flag indicating context was closed (implies cookies *should* be saved)

# --- The ADK Tool Function ---

async def run_browser_task_tool(
    tool_context: ToolContext,
    url: str
) -> str:
    """Executes a browsing task to EXTRACT RAW PAGE DATA AS JSON from a specific URL.

    Handles browser setup, execution, result extraction, and screenshot saving.
    Relies on user_id and session_id being present in the ToolContext.state.
    Use this tool ONLY when the user provides a specific URL for information gathering.

    Args:
        tool_context: The ADK ToolContext (provides invocation ID and session state).
        url (str): The full URL of the website to interact with.

    Returns:
        str: A JSON string containing the extracted raw data from the page, or a JSON-like error string.
    """
    # --- Get IDs from ADK Session State (Stored by JonasService) --- 
    user_id = tool_context.state.get('invocation_user_id') # Use the specific key
    session_id = tool_context.state.get('invocation_session_id') # Use the specific key

    invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    function_call_id = getattr(tool_context, 'function_call_id', 'N/A')
    logger.info(f"--- Tool: run_browser_task_tool called [Inv: {invocation_id}, Func: {function_call_id}] ---")
    logger.info(f"  URL: {url}")
    logger.info(f"  User ID (from State): {user_id}") 
    logger.info(f"  Session ID (from State): {session_id}")

    # Validate arguments and IDs from state
    if not all([url, user_id, session_id]):
        logger.error(f"Tool: Missing required arguments OR IDs from state. URL: {url}, UserID: {user_id}, SessionID: {session_id}")
        return '{"status": "error", "error_message": "Missing required arguments or context IDs from state."}'

    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    screenshot_repo: Optional[ScreenshotRepository] = None
    cookie_path: Optional[str] = None # Define cookie_path here
    initial_mod_time: Optional[float] = None # Store initial mod time

    # Instantiate ScreenshotRepository here
    try:
         screenshot_repo = ScreenshotRepository()
    except Exception as repo_err:
        logger.error(f"Tool: Failed to instantiate ScreenshotRepository: {repo_err}", exc_info=True)
        return '{"status": "error", "error_message": "Internal error initializing screenshot capability."}'

    try:
        sensitive_data = _get_sensitive_data()
        execution_llm, planner_llm = _get_llm_config()
        task_description = _construct_task_description(url)

        # Prepare sensitive data specifically for this run
        run_sensitive_data = {}
        if "trello.com" in url:
            # If it's Trello, copy relevant secrets for the agent to use
            if 'trello_user' in sensitive_data:
                run_sensitive_data['trello_user'] = sensitive_data['trello_user']
            if 'trello_pass' in sensitive_data:
                run_sensitive_data['trello_pass'] = sensitive_data['trello_pass']
            if 'trello_totp_secret' in sensitive_data:
                generated_totp_code = _generate_totp_code(sensitive_data['trello_totp_secret'])
                if generated_totp_code:
                    run_sensitive_data['trello_totp_code'] = generated_totp_code
                else:
                    logger.error("Tool: Failed to generate Trello 2FA code, proceeding without it.")
                    # Decide if this is fatal:
                    # return {"status": "error", "error_message": "[Error: Failed to generate Trello 2FA code]"}
            logger.info("Tool: Trello URL detected, providing Trello credentials to BrowserUseAgent.")
        elif "reservations.voyagesalacarte.ca" in url:
            # If it's Respro, copy relevant secrets for the agent to use
            if 'respro_user' in sensitive_data:
                run_sensitive_data['respro_user'] = sensitive_data['respro_user']
            if 'respro_pass' in sensitive_data:
                run_sensitive_data['respro_pass'] = sensitive_data['respro_pass']
            logger.info("Tool: Respro URL detected, providing Respro credentials to BrowserUseAgent.")
        # Add logic here if other sites need specific credentials

        # Browser Setup - Use the state IDs for cookie path uniqueness
        cookie_id = f"user_{user_id}" # Use ONLY user_id for state persistence across sessions
        cookie_path = _get_cookie_file_path(cookie_id)
        logger.info(f"Tool: Determined cookie path: {cookie_path}")

        # Log initial cookie file state
        if os.path.exists(cookie_path):
            try:
                initial_mod_time = os.path.getmtime(cookie_path)
                logger.info(f"Tool: Cookie file exists. Initial Mod Time: {initial_mod_time}")
            except Exception as e:
                logger.warning(f"Tool: Could not get initial mod time for cookie file {cookie_path}: {e}")
        else:
            logger.info(f"Tool: Cookie file does not exist yet.")
            initial_mod_time = -1 # Indicate it didn't exist

        browser_config = BrowserConfig(headless=True)
        context_config = BrowserContextConfig(cookies_file=cookie_path)
        
        browser = Browser(config=browser_config)
        logger.info(f"Tool: Creating browser context with cookie file: {cookie_path}")
        context = await browser.new_context(config=context_config)
        logger.info(f"Tool: Browser context created.")

        # Create and run browser-use Agent
        browser_use_agent = BrowserUseAgent(
            task=task_description,
            llm=execution_llm,
            planner_llm=planner_llm,
            browser_context=context,
            use_vision_for_planner=False,
            sensitive_data=run_sensitive_data if run_sensitive_data else None # Use potentially Trello-specific creds
        )
        history = await browser_use_agent.run()

        # Process results and save screenshots 
        result_json_string = _extract_result(history)
        
        # Screenshot Saving logic (remains the same, depends on session_id conversion)
        db_chat_id: Optional[PydanticObjectId] = None
        try:
             db_chat_id = PydanticObjectId(session_id) 
             logger.info(f"Tool: Attempting screenshot save with DB Chat ID (from state session_id): {db_chat_id}")
             if screenshot_repo and history:
                 await _save_screenshots(screenshot_repo, db_chat_id, history)
        except Exception as conversion_err:
             logger.error(f"Tool: Failed to convert session_id '{session_id}' from state to PydanticObjectId for screenshot saving: {conversion_err}. Screenshots NOT saved.")

        print("--- Browser Tool Raw JSON Output --- ")
        print(f"{result_json_string}")
        print("----------------------------------")

        # Return the JSON string (or error JSON string)
        return result_json_string
    except Exception as e:
        logger.error(f"Tool: Unhandled exception during execution: {e}", exc_info=True)
        browser_local = locals().get('browser')
        context_local = locals().get('context')
        if browser_local or context_local: 
             await _cleanup_resources(browser_local, context_local)
        # Return dict for error case
        return f'{{"status": "error", "error_message": "An unexpected error occurred: {e}"}}'
    finally:
        browser_local = locals().get('browser')
        context_local = locals().get('context')
        if browser_local or context_local: 
            await _cleanup_resources(browser_local, context_local) 

        # --- Cookie Verification Logging --- 
        context_closed = False
        if browser or context:
            logger.info("Tool: Cleaning up browser resources...")
            context_closed = await _cleanup_resources(browser, context)
            logger.info(f"Tool: Browser resources cleanup finished. Context closed: {context_closed}")

            # Check cookie file state *after* closing context
            if cookie_path and context_closed:
                 if os.path.exists(cookie_path):
                     try:
                         final_mod_time = os.path.getmtime(cookie_path)
                         logger.info(f"Tool: Cookie file exists after close. Final Mod Time: {final_mod_time}")
                         if initial_mod_time is not None:
                             if initial_mod_time == -1:
                                 logger.info("Tool: Cookie file was newly created during this run.")
                             elif final_mod_time > initial_mod_time:
                                 logger.info("Tool: Cookie file modification time updated during this run.")
                             else:
                                 logger.warning("Tool: Cookie file exists, but modification time did NOT update.")
                     except Exception as e:
                         logger.warning(f"Tool: Could not get final mod time for cookie file {cookie_path}: {e}")
                 else:
                      logger.warning(f"Tool: Cookie file {cookie_path} does NOT exist after context close.")
            elif not context_closed:
                 logger.warning("Tool: Context may not have closed properly, cookie saving might not have occurred.")
        else:
             logger.info("Tool: No browser/context resources were initialized, skipping cleanup and cookie check.")
        # --- End Cookie Verification Logging --- 