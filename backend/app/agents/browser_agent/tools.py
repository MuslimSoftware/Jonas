import traceback
import pyotp
import logging
import os
import time
from typing import Dict, Optional, Tuple, Any, List
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from browser_use import Agent as BrowserUseAgent, Browser, BrowserConfig
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
    """Constructs the generic task description for information extraction, assuming login handled separately."""
    # This function defines the extraction goal after navigation/login.
    return f"""Your goal is to analyze the content at the current page ({input_url}) and extract key information for a developer.

**--- Content Analysis and Extraction ---**
1.  **Identify Core Information:** Examine the main content. Find and extract the primary title or subject of the page.
2.  **Extract Description:** Locate and extract the main descriptive text or body content that explains the purpose or details of the page/task.
3.  **Identify People:** Look for any listed individuals (e.g., assignees, members, authors) and extract their names.
4.  **List Links:** Find all hyperlinks within the main content area. List them clearly, perhaps grouping related links if the context makes it obvious (e.g., links to related issues, documentation).
5.  **Extract Key Attributes:** Scan the page for important metadata or attributes often associated with tasks or items (e.g., status, priority, estimates, creation/update dates, version numbers). Extract these key-value pairs but **ONLY INCLUDE attributes that have a non-empty, non-default value assigned**. Ignore fields with placeholder text like 'Select...', 'Add date...', or null/empty values.
6.  **Booking IDs:** Specifically search the page for links matching the pattern `reservations.voyagesalacarte.ca/booking/index/[numeric_id]` and list any extracted numeric IDs.
7.  **Format Output:** Present all extracted information clearly. For each piece of data, indicate what it represents (e.g., start the line with 'Title:', 'Description:', 'Assignees:', 'Links:', 'Status:', 'Booking IDs:'). Use markdown formatting for clarity (like bullet points for lists).
8.  **Brief Summary:** Conclude your response with a 1-2 sentence summary under the heading `### Brief Summary`, synthesizing the main point or topic based *only* on the information extracted in the steps above (Title, Description, etc.).

**IMPORTANT:** Focus on extracting and clearly labeling the information present on the page. Do not add extra interpretation or summarization beyond requested; just report the extracted data in a well-structured format followed by the brief summary.
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

def _extract_result(history: Any) -> str:
    """Extracts the final text result from history."""
    try:
        result_text = history.final_result()
        if not result_text:
            extracted_content = history.extracted_content()
            result_text = extracted_content if extracted_content else "Agent ran, but no specific result was extracted."
        return result_text
    except Exception as e:
        logger.error(f"Tool: Error extracting result from history: {e}")
        return "[Error extracting result from agent history]"

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
) -> dict:
    """Executes a browsing task to EXTRACT STRUCTURED INFORMATION from a specific URL.

    Handles browser setup, execution, result extraction, and screenshot saving.
    Relies on user_id and session_id being present in the ToolContext.state.
    Use this tool ONLY when the user provides a specific URL for information gathering.

    Args:
        tool_context: The ADK ToolContext (provides invocation ID and session state).
        url (str): The full URL of the website to interact with.

    Returns:
        str: A structured string containing the categorized information extracted from the page.
             Example error return: {"status": "error", "error_message": "Could not access URL."}
    """
    return """I was able to extract the following information from the Trello card:

Title: [Validation error] - Stop pax DOB errors at a form level

List: IN QA

Description: Goal: Ensure validation checks are done before displaying any modal to customer.

Problem:
We allow users to select DOBs that result in validation errors. These errors are not displayed on Justfly and are confusing on Flighthub. Mobile devices also have issues with validation.

Solutions:

Solution 1: For all INL/INS pax
Highlight immediately in red if user selects a DOB in the future (inputted DOB > CURRENT_DATE()). Error message: "Passenger date of birth must be before travel date".

Solution 2: For INL/INS passengers
If the infant will be over 2 years old before the departure of the return flight, throw a validation error (highlight in red) with the message: "Infant fare passengers must be under the age of 2 at the departure time of the last flight. Please book this passenger as 'child'".

Solution 3: For 1 adult pax itineraries (Transborder/International only)
If the DOB makes them lower than 16 before the departure date of the last segment of the itinerary, throw a validation error (highlight in red).
Error message: "All bookings must contain at least one passenger over the age of 16"

Solution 5: For multi-adt-pax itineraries (regardless of domestic/int)
If one of the passengers will be lower than age of 12 for the entire duration, highlight in red as the customer moves through the form.
Error message: Adult fare passengers must be over the age of 12 at the departure time of the last flight. Please book this passenger as 'child'.

Solution 6: For all child passengers
If the child will be over age of 12 by the IB departure, but at OB dep time he is below 12, throw validation error (highlight in red).
Error message: "Passenger must be between the ages of 2 and 12 for the entire duration of the trip to travel as an child. Please book this passenger as an adult"

Attachments:
image.png (Added Apr 22, 2025, 2:51 PM)
image.png (Added Apr 22, 2025, 2:31 PM)

Custom Fields:
Estimate - SH (Days): 3
Estimate - Devs (Days): 4

Github Pull Requests:
mventures/genesis Pull Request #47221

Debug Log Example: https://reservations.voyagesalacarte.ca/debug-logs/log-group/787e61e3d5098331d974e6c43ed44a24

Validation Error Examples:
Validation input['p3_dob_month']['server_age'] = Infant fare passengers must be under the age of 2 at the departure time of the last flight.
Validation input['p3_dob_day']['server_age'] = Infant fare passengers must be under the age of 2 at the departure time of the last flight.
Validation input['p3_dob_year']['server_age'] = Infant fare passengers must be under the age of 2 at the departure time of the last flight.
Validation input['p4_dob_month']['server_age'] = Infant fare passengers must be under the age of 2 at the departure time of the last flight.
Validation input['p4_dob_day']['server_age'] = Infant fare passengers must be under the age of 2 at the departure time of the last flight.
Validation input['p4_dob_year']['server_age'] = Infant fare passengers must be under the age of 2 at the departure time of the last flight.

I was unable to extract the booking ID because I could not log in to the debug log page. The login attempt failed with an "Invalid Email/Password" error.

### Brief Summary
The Trello card discusses validation errors related to passenger dates of birth and proposes solutions to ensure validation checks are done before displaying any modal to the customer. The card includes a link to debug logs, but access was denied due to invalid credentials."""
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
        return {"status": "error", "error_message": "Missing required arguments or context IDs from state."}

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
        return {"status": "error", "error_message": "Internal error initializing screenshot capability."}

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
        result_text = _extract_result(history)
        
        # Screenshot Saving logic (remains the same, depends on session_id conversion)
        db_chat_id: Optional[PydanticObjectId] = None
        try:
             db_chat_id = PydanticObjectId(session_id) 
             logger.info(f"Tool: Attempting screenshot save with DB Chat ID (from state session_id): {db_chat_id}")
             if screenshot_repo and history:
                 await _save_screenshots(screenshot_repo, db_chat_id, history)
        except Exception as conversion_err:
             logger.error(f"Tool: Failed to convert session_id '{session_id}' from state to PydanticObjectId for screenshot saving: {conversion_err}. Screenshots NOT saved.")

        print("--------------------------------")
        print(f"{result_text}")
        print("--------------------------------")

        # Return the structured text directly
        return result_text
    except Exception as e:
        logger.error(f"Tool: Unhandled exception during execution: {e}", exc_info=True)
        browser_local = locals().get('browser')
        context_local = locals().get('context')
        if browser_local or context_local: 
             await _cleanup_resources(browser_local, context_local)
        # Return dict for error case
        return {"status": "error", "error_message": f"An unexpected error occurred in the browser tool: {e}"}
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