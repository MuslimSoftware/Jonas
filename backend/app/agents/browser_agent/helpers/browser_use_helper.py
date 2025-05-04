# Helper functions for browser_use_tool
import logging
import os
import re
import json
from typing import Dict, Optional, Tuple, Any, List
import pyotp
from beanie import PydanticObjectId
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from browser_use import Browser
from browser_use.agent.views import AgentHistoryList
from browser_use.browser.context import BrowserContext
from google.adk.tools import ToolContext

from app.config.environment import environment
from app.features.chat.repositories import ScreenshotRepository 

logger = logging.getLogger(__name__) # Use a logger specific to helpers

def get_context_ids(tool_context: ToolContext) -> Tuple[Optional[str], Optional[str], str, str]:
    """Extracts user_id, session_id, invocation_id, and function_call_id from the ToolContext."""
    # Get IDs from state dictionary
    user_id = tool_context.state.get('invocation_user_id')
    session_id = tool_context.state.get('invocation_session_id')
    
    # Get IDs directly from context attributes (using getattr for safety)
    invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    function_call_id = getattr(tool_context, 'function_call_id', 'N/A')
    
    # Optional: Add logging here if needed
    logger.debug(f"Helper: Extracted IDs - User: {user_id}, Session: {session_id}, Invocation: {invocation_id}, FunctionCall: {function_call_id}")
        
    return user_id, session_id, invocation_id, function_call_id

def generate_totp_code(secret: str) -> Optional[str]:
    """Generates the current TOTP code."""
    if not secret: return None
    totp = pyotp.TOTP(secret)
    return totp.now()

def get_sensitive_data(url: str) -> Dict[str, str]:
    """Loads and filters sensitive data based on the target URL."""
    run_sensitive_data = {}
    
    # Load potential secrets (consider caching if environment vars are static)
    trello_user = environment.TRELLO_USERNAME
    trello_pass = environment.TRELLO_PASSWORD
    trello_secret = environment.TRELLO_TOTP_SECRET
    respro_user = environment.RESPRO_USERNAME
    respro_pass = environment.RESPRO_PASSWORD

    if "trello.com" in url:
        logger.info("Helper: Trello URL detected, preparing Trello credentials.")
        if trello_user:
            run_sensitive_data['trello_user'] = trello_user
        if trello_pass:
            run_sensitive_data['trello_pass'] = trello_pass
        if trello_secret:
            generated_totp_code = generate_totp_code(trello_secret)
            if generated_totp_code:
                run_sensitive_data['trello_totp_code'] = generated_totp_code
            else:
                # Log error from helper perspective
                logger.error("Helper: Failed to generate Trello 2FA code.")
                # Decide if this should raise an error or just log
    elif "reservations.voyagesalacarte.ca" in url:
        logger.info("Helper: Respro URL detected, preparing Respro credentials.")
        if respro_user:
            run_sensitive_data['respro_user'] = respro_user
        if respro_pass:
            run_sensitive_data['respro_pass'] = respro_pass
    # Add logic here if other sites need specific credentials
    
    if not run_sensitive_data:
        logger.info(f"Helper: No specific sensitive data configured for URL: {url}")
        
    return run_sensitive_data

def get_llm_config() -> Tuple[ChatGoogleGenerativeAI, ChatGoogleGenerativeAI]:
    """Initializes LLM configurations."""
    execution_llm = ChatGoogleGenerativeAI(
        model=environment.BROWSER_EXECUTION_MODEL,
        temperature=0
    )
    planner_llm = ChatGoogleGenerativeAI(
        model=environment.BROWSER_PLANNER_MODEL,
        temperature=0
    )
    return execution_llm, planner_llm

def construct_task_description(input_url: str) -> str:
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
    *   Tables
    *   Hidden elements (e.g. `display: none`)
    *   Dropdowns
    *   Input fields
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

def get_cookie_file_path(user_id: str) -> str:
    """Generates a unique cookie file path based on user_id."""
    if not user_id: # Basic validation
        raise ValueError("user_id cannot be empty for cookie path generation")
        
    cookie_id = f"user_{user_id}" # Construct the ID here
    base_dir = "/app/data/cookies" # Ensure this exists
    # Create the base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True) 
    filename = f"{cookie_id}_cookies.json"
    full_path = os.path.join(base_dir, filename)
    logger.info(f"Helper: Determined cookie path for user {user_id}: {full_path}")
    return full_path

async def save_screenshots(screenshot_repo: ScreenshotRepository, chat_id: PydanticObjectId, history: AgentHistoryList):
    """Processes and saves screenshots using the provided repository."""
    try:
        screenshot_data_list = history.screenshots() # Assuming returns list of base64
        logger.info(f"Helper (save_screenshots): Found {len(screenshot_data_list)} screenshots for chat {chat_id}.")
        saved_count = 0
        for image_data in screenshot_data_list:
            try:
                # Assuming image_data is raw base64 from browser-use
                data_uri = f"data:image/png;base64,{image_data}"
                # Here we need the *actual* chat_id ObjectId for the repository
                await screenshot_repo.create_screenshot(chat_id=chat_id, image_data=data_uri)
                saved_count += 1
            except Exception as img_err:
                logger.error(f"Helper (save_screenshots): Error saving individual screenshot for chat {chat_id}: {img_err}")
        logger.info(f"Helper (save_screenshots): Saved {saved_count} screenshots for chat {chat_id}.")
    except Exception as e:
        logger.error(f"Helper (save_screenshots): Error processing screenshots for chat {chat_id}: {e}")

async def process_and_save_screenshots(session_id: Optional[str], history: Optional[AgentHistoryList]):
    """Instantiates repo, converts ID, and saves screenshots from history."""
    if not session_id or not history:
        logger.warning("Helper (process_and_save): Missing session_id or history, cannot save screenshots.")
        return

    screenshot_repo: Optional[ScreenshotRepository] = None
    db_chat_id: Optional[PydanticObjectId] = None

    # 1. Instantiate Repository
    try:
        screenshot_repo = ScreenshotRepository()
        logger.info("Helper (process_and_save): ScreenshotRepository instantiated.")
    except Exception as repo_err:
        logger.error(f"Helper (process_and_save): Failed to instantiate ScreenshotRepository: {repo_err}", exc_info=True)
        # Decide if we should return or allow proceeding without screenshots
        return # Stop if repo cannot be created

    # 2. Convert Session ID
    try:
        db_chat_id = PydanticObjectId(session_id)
        logger.info(f"Helper (process_and_save): Converted session_id to DB Chat ID: {db_chat_id}")
    except Exception as conversion_err:
        logger.error(f"Helper (process_and_save): Failed to convert session_id '{session_id}' to PydanticObjectId: {conversion_err}. Screenshots NOT saved.")
        return # Stop if ID conversion fails

    # 3. Call the saving logic (only if repo and ID are valid)
    if screenshot_repo and db_chat_id:
        await save_screenshots(screenshot_repo, db_chat_id, history)
    else:
        # This case should technically be covered by the returns above, but added for clarity
        logger.warning("Helper (process_and_save): Skipping screenshot saving due to missing repo or db_chat_id.")

def extract_result(history: AgentHistoryList) -> Dict[str, Any]:
    """Extracts the JSON result from history, parses it, and returns a dictionary."""
    try:
        extracted_content = history.extracted_content()
        print(f"Helper: extracted_content: ================")
        print(f"{extracted_content}")
        print(f"Helper: extracted_content: ================")
        final_result_text = history.final_result()
        print(f"Helper: final_result_text: ================")
        print(f"{final_result_text}")
        print(f"Helper: final_result_text: ================")

        # Debug logging
        # logger.debug(f"Helper: raw extracted_content: {extracted_content}")
        # logger.debug(f"Helper: raw final_result_text: {final_result_text}")

        raw_json_string = None

        # Prioritize extracted_content if it looks like JSON or contains a JSON block
        if isinstance(extracted_content, list):
            logger.info(f"Helper: extracted_content is a list with {len(extracted_content)} items. Searching for JSON block or string.")
            for item in extracted_content:
                if isinstance(item, str):
                    # Check for ```json ... ``` block first
                    match = re.search(r"```json\n(.*?)\n```", item, re.DOTALL)
                    if match:
                        raw_json_string = match.group(1).strip()
                        logger.info("Helper: Found JSON block in extracted_content list item.")
                        break
                    # Check if the item itself looks like JSON
                    elif item.strip().startswith('{') or item.strip().startswith('['):
                         raw_json_string = item
                         logger.info("Helper: Found JSON-like string in extracted_content list item.")
                         break
        elif isinstance(extracted_content, str):
             # Check if the string itself is the JSON block or contains it
             match = re.search(r"```json\n(.*?)\n```", extracted_content, re.DOTALL)
             if match:
                 raw_json_string = match.group(1).strip()
                 logger.info("Helper: Found JSON block in extracted_content string.")
             # Basic check if the string itself might be JSON
             elif extracted_content.strip().startswith('{') or extracted_content.strip().startswith('['):
                 raw_json_string = extracted_content
                 logger.info("Helper: Treating extracted_content string as potential JSON.")

        # Fallback to final_result if no JSON found in extracted_content
        if not raw_json_string and isinstance(final_result_text, str):
             if final_result_text.strip().startswith('{') or final_result_text.strip().startswith('['):
                 raw_json_string = final_result_text
                 logger.info("Helper: Using final_result as JSON source (extracted_content was not suitable).")
             else:
                 logger.warning(f"Helper: final_result_text did not appear to be JSON: {final_result_text[:100]}...")
        
        # If we found a potential JSON string, try to parse it
        if raw_json_string:
            try:
                parsed_json = json.loads(raw_json_string)
                # Assuming success means the page content itself
                logger.info(f"Helper: Successfully parsed JSON string. Keys: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'N/A (List)'}")
                # Return the parsed dictionary directly with a success status
                # Check if the parsed content already has a 'status' key (e.g., from an error within browser-use)
                if isinstance(parsed_json, dict) and 'status' in parsed_json:
                    return parsed_json # Return as-is if status is already present
                else:
                    # Wrap the successfully parsed content
                    return {"status": "success", "data": parsed_json}
            except json.JSONDecodeError as json_err:
                logger.error(f"Helper: Failed to decode JSON string: {json_err}. String was: {raw_json_string[:500]}...", exc_info=True)
                # Return error dictionary
                return {"status": "error", "error_message": f"Failed to parse extracted content as JSON: {json_err}", "raw_content": raw_json_string[:1000]} # Include partial raw content for debugging
            except Exception as parse_err: # Catch other potential errors during parsing
                 logger.error(f"Helper: Unexpected error parsing JSON string: {parse_err}. String was: {raw_json_string[:500]}...", exc_info=True)
                 return {"status": "error", "error_message": f"Unexpected error parsing JSON: {parse_err}", "raw_content": raw_json_string[:1000]}

        # If no JSON string was found anywhere
        logger.warning("Helper: Agent ran, but no suitable JSON content found in history.")
        # Return error dictionary indicating missing data
        return {"status": "error", "error_message": "No JSON content found in the browser task result."}

    except Exception as e:
        logger.error(f"Helper: Error extracting result from history: {e}", exc_info=True)
        # Return error dictionary for exceptions during history access
        return {"status": "error", "error_message": f"Error extracting result data from history: {e}"}

async def cleanup_resources(browser: Optional[Browser], context: Optional[BrowserContext]):
    """Safely close browser resources."""
    closed_context = False
    if context:
        try: 
            await context.close()
            closed_context = True
            logger.info(f"Helper: Closed BrowserContext.")
        except Exception as e: logger.warning(f"Helper: Error closing context: {e}")
    if browser:
        try: 
            await browser.close()
            logger.info(f"Helper: Closed Browser.")
        except Exception as e: logger.warning(f"Helper: Error closing browser: {e}")
    return closed_context # Return flag indicating context was closed (implies cookies *should* be saved) 