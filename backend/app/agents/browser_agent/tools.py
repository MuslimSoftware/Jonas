import pyotp
import logging
import os
from typing import Dict, Optional, Tuple, Any
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from browser_use import Agent as BrowserUseAgent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from beanie import PydanticObjectId
from google.adk.tools import ToolContext

from app.config.env import settings
# Import ScreenshotRepository directly for saving within the tool
from app.features.chat.repositories import ScreenshotRepository

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
        model=settings.AI_MODEL,
        temperature=0,
        google_api_key=settings.AI_API_KEY
    )
    planner_llm = ChatGoogleGenerativeAI(
        model=settings.AI_MODEL,
        temperature=0,
        google_api_key=settings.AI_API_KEY
    )
    return execution_llm, planner_llm

def _construct_task_description(input_url: str, user_request: str) -> str:
    """Constructs the task description."""
    if "trello.com" in input_url:
        # Using triple quotes for multi-line f-string
        return f"""Your goal is to log into Trello and address the user's request regarding the content at {input_url}. The user specifically asked: '{user_request}'.
0. **Check login:** Navigate to {input_url}. If logged in and can see content, skip to Step 9. Otherwise, proceed to Step 1.
1. Navigate to trello.com/login.
2. Enter username '<secret>trello_user</secret>'. Click Continue.
3. Enter password '<secret>trello_pass</secret>'. Click Log in.
4. On verification page, find 6-digit code field.
5. Enter code '<secret>trello_totp_code</secret>'.
6. Click submit. If error, stop and report 'TOTP code failed'.
7. Wait for main boards page/dashboard.
8. Verify successful login.
9. **After confirming login**, navigate to target: {input_url}.
10. Once on the target page, execute the user's request: '{user_request}'. Analyze content, extract information, or perform actions as requested. Provide a summary of your findings or actions related to the request.
IMPORTANT: If you restart login (Step 2) twice without fulfilling the request (Step 10), stop and report 'login loop'.
"""
    else:
        return f"Log in to the site at {input_url} if necessary, then fulfill the user's request: '{user_request}'. Analyze the main content relevant to the request."

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
        saved_count = 0
        for image_data in screenshot_data_list:
            try:
                # Assuming image_data is raw base64 from browser-use
                data_uri = f"data:image/png;base64,{image_data}"
                # Here we need the *actual* chat_id ObjectId for the repository
                await screenshot_repo.create_screenshot(chat_id=chat_id, image_data=data_uri)
                saved_count += 1
            except Exception as img_err:
                print(f"Tool: Error saving screenshot for chat {chat_id}: {img_err}")
    except Exception as e:
        print(f"Tool: Error processing screenshots for chat {chat_id}: {e}")

def _extract_result(history: Any) -> str:
    """Extracts the final text result from history."""
    try:
        result_text = history.final_result()
        if not result_text:
            extracted_content = history.extracted_content()
            result_text = extracted_content if extracted_content else "Agent ran, but no specific result was extracted."
        return result_text
    except Exception as e:
        print(f"Tool: Error extracting result from history: {e}")
        return "[Error extracting result from agent history]"

async def _cleanup_resources(browser: Optional[Browser], context: Optional[BrowserContext]):
    """Safely close browser resources."""
    closed_context = False
    if context:
        try: 
            await context.close()
            closed_context = True
            print(f"Tool: Closed BrowserContext.")
        except Exception as e: print(f"Tool: Error closing context: {e}")
    if browser:
        try: 
            await browser.close()
            print(f"Tool: Closed Browser.")
        except Exception as e: print(f"Tool: Error closing browser: {e}")
    return closed_context # Return flag indicating context was closed (implies cookies *should* be saved)

# --- The ADK Tool Function ---

async def run_browser_task_tool(
    tool_context: ToolContext,
    url: str,
    user_request: str
) -> dict:
    """Executes a browsing task on a specific URL using the browser-use library.

    Handles browser setup, execution, result extraction, and screenshot saving.
    Relies on user_id and session_id being present in the ToolContext.state.
    Use this tool ONLY when the user provides a specific URL AND describes a task.

    Args:
        tool_context: The ADK ToolContext (provides invocation ID and session state).
        url (str): The full URL of the website to interact with.
        user_request (str): The specific task the user wants to perform.

    Returns:
        dict: A dictionary containing the status and result text.
              Example success: {"status": "success", "result": "Summary..."}
              Example error:   {"status": "error", "error_message": "Could not access URL."}
              (Screenshots are saved internally, not returned in the dict)
    """
    # --- Get IDs from ADK Session State (Stored by JonasService) --- 
    user_id = tool_context.state.get('invocation_user_id') # Use the specific key
    session_id = tool_context.state.get('invocation_session_id') # Use the specific key
    
    # Log invocation details using context
    # invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    # function_call_id = getattr(tool_context, 'function_call_id', 'N/A')

    # Validate arguments and IDs from state
    if not all([url, user_request, user_id, session_id]):
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
        print(f"Tool: Failed to instantiate ScreenshotRepository: {repo_err}", exc_info=True)
        return {"status": "error", "error_message": "Internal error initializing screenshot capability."}

    try:
        sensitive_data = _get_sensitive_data()
        execution_llm, planner_llm = _get_llm_config()
        task_description = _construct_task_description(url, user_request)

        # Handle TOTP
        if 'trello_totp_secret' in sensitive_data:
            generated_totp_code = _generate_totp_code(sensitive_data['trello_totp_secret'])
            if generated_totp_code:
                sensitive_data['trello_totp_code'] = generated_totp_code
            else:
                return {"status": "error", "error_message": "[Error: Failed to generate Trello 2FA code]"}
        elif '<secret>trello_totp_code</secret>' in task_description:
             return {"status": "error", "error_message": "[Error: Trello TOTP secret not configured]"}

        # Browser Setup - Use the state IDs for cookie path uniqueness
        cookie_id = f"user_{user_id}_adk_session_{session_id}" # Use state IDs
        cookie_path = _get_cookie_file_path(cookie_id)
        print(f"Tool: Determined cookie path: {cookie_path}")

        # Log initial cookie file state
        if os.path.exists(cookie_path):
            try:
                initial_mod_time = os.path.getmtime(cookie_path)
                print(f"Tool: Cookie file exists. Initial Mod Time: {initial_mod_time}")
            except Exception as e:
                print(f"Tool: Could not get initial mod time for cookie file {cookie_path}: {e}")
        else:
            print(f"Tool: Cookie file does not exist yet.")
            initial_mod_time = -1 # Indicate it didn't exist

        browser_config = BrowserConfig(headless=True)
        context_config = BrowserContextConfig(cookies_file=cookie_path)
        
        browser = Browser(config=browser_config)
        print(f"Tool: Creating browser context with cookie file: {cookie_path}")
        context = await browser.new_context(config=context_config)
        print(f"Tool: Browser context created.")

        # Create and run browser-use Agent
        browser_use_agent = BrowserUseAgent(
            task=task_description,
            llm=execution_llm,
            planner_llm=planner_llm,
            browser_context=context,
            use_vision_for_planner=False,
            sensitive_data=sensitive_data if sensitive_data else None
        )
        history = await browser_use_agent.run()

        # Process results and save screenshots 
        result_text = _extract_result(history)
        # result_text = "Test"
        
        # --- Screenshot Saving Challenge --- 
        # We need the *database* chat_id (as PydanticObjectId) to save screenshots correctly.
        # The session_id from ADK context might NOT be the database ID.
        # How to get the database chat ID here? 
        # Option 1: Assume session_id IS the DB ID string (might break)
        # Option 2: Modify tool signature to require DB chat_id (means JonasAgent needs it)
        # Option 3: Don't save screenshots from the tool, return data (back to previous approach)
        
        # Let's try Option 1 for now, converting ONLY when saving:
        db_chat_id: Optional[PydanticObjectId] = None
        try:
             # Use the session_id from state directly 
             db_chat_id = PydanticObjectId(session_id) 
             print(f"Tool: Attempting screenshot save with DB Chat ID (from state session_id): {db_chat_id}")
             if screenshot_repo:
                 # Pass history object if browser_use_agent was run
                 # await _save_screenshots(screenshot_repo, db_chat_id, history) # history is commented out above
                 print("Tool: browser_use_agent run is commented out, skipping screenshot save.")
        except Exception as conversion_err:
             print(f"Tool: Failed to convert session_id '{session_id}' from state to PydanticObjectId for screenshot saving: {conversion_err}. Screenshots NOT saved.")
        # --- End Screenshot Saving Challenge ---

        print(f"Tool: Task completed. Result chars: {len(result_text)}")

        # Return only status and text result to the ADK Agent
        if result_text.startswith("[Error"):
             return {"status": "error", "error_message": result_text}
        else:
             return {"status": "success", "result": result_text}

    except Exception as e:
        print(f"Tool: Unhandled exception during execution: {e}", exc_info=True)
        browser_local = locals().get('browser')
        context_local = locals().get('context')
        if browser_local or context_local: 
             await _cleanup_resources(browser_local, context_local)
        return {"status": "error", "error_message": f"An unexpected error occurred in the browser tool: {e}"}
    finally:
        browser_local = locals().get('browser')
        context_local = locals().get('context')
        if browser_local or context_local: 
            await _cleanup_resources(browser_local, context_local) 

        # --- Cookie Verification Logging --- 
        context_closed = False
        if browser or context:
            print("Tool: Cleaning up browser resources...")
            context_closed = await _cleanup_resources(browser, context)
            print(f"Tool: Browser resources cleanup finished. Context closed: {context_closed}")

            # Check cookie file state *after* closing context
            if cookie_path and context_closed:
                 if os.path.exists(cookie_path):
                     try:
                         final_mod_time = os.path.getmtime(cookie_path)
                         print(f"Tool: Cookie file exists after close. Final Mod Time: {final_mod_time}")
                         if initial_mod_time is not None:
                             if initial_mod_time == -1:
                                 print("Tool: Cookie file was newly created during this run.")
                             elif final_mod_time > initial_mod_time:
                                 print("Tool: Cookie file modification time updated during this run.")
                             else:
                                 print("Tool: Cookie file exists, but modification time did NOT update.")
                     except Exception as e:
                         print(f"Tool: Could not get final mod time for cookie file {cookie_path}: {e}")
                 else:
                      print(f"Tool: Cookie file {cookie_path} does NOT exist after context close.")
            elif not context_closed:
                 print("Tool: Context may not have closed properly, cookie saving might not have occurred.")
        else:
             print("Tool: No browser/context resources were initialized, skipping cleanup and cookie check.")
        # --- End Cookie Verification Logging --- 