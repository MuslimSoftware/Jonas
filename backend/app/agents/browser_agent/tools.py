import traceback
import logging
import os
import json
from typing import Dict, Optional, Tuple, Any, List
from browser_use import Agent as BrowserUseAgent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.agent.views import AgentOutput, AgentHistoryList, AgentBrain
from browser_use.browser.views import BrowserState
import functools
from app.features.chat.repositories.screenshot_repository import ScreenshotRepository
from app.features.chat.services.websocket_service import WebSocketService
from app.features.chat.repositories.websocket_repository import WebSocketRepository as WSRepo
from google.adk.tools import ToolContext
from beanie import PydanticObjectId

from .helpers.browser_use_helper import (
    get_context_ids,
    get_sensitive_data,
    get_llm_config,
    construct_task_description,
    get_cookie_file_path,
    extract_result,
    cleanup_resources
)

logger = logging.getLogger(__name__)

# --- Callback Implementations ---

async def new_step_callback_save_screenshot(
    state: BrowserState,
    output: AgentOutput,
    step_index: int,
    chat_id: PydanticObjectId,
    tool_context: ToolContext
) -> None:
    """Callback triggered after each step, attempts to save a screenshot."""
    logger.info(f"Callback new_step_callback_save_screenshot: Step {step_index} completed.")
    url, screenshot = state.url, state.screenshot
    current_state: AgentBrain = output.current_state

    if screenshot:
        try:
            screenshot_repo = ScreenshotRepository()
            data_uri = f"data:image/png;base64,{screenshot}"

            # Pass chat_id as PydanticObjectId as expected by create_screenshot
            created_screenshot = await screenshot_repo.create_screenshot(
                chat_id=chat_id, 
                image_data=data_uri,
                page_summary=current_state.page_summary,
                evaluation_previous_goal=current_state.evaluation_previous_goal,
                memory=current_state.memory,
                next_goal=current_state.next_goal
            )
        except Exception as e: # Catch a more general exception
            # Log the full error with traceback for better debugging
            logger.error(f"Callback: Error during screenshot saving or broadcasting for chat_id {chat_id}: {e}", exc_info=True)
            # Depending on desired behavior, you might not want to 'return' here
            # if other parts of the callback should still execute.
            # For now, we'll let it proceed if other logic exists after this block.
            # If this is the last critical operation, returning might be appropriate.
            pass # Or return, based on desired error handling for the callback

async def done_callback_log_history(history: AgentHistoryList) -> None:
    """Callback triggered when the browser_use_agent completes successfully."""
    logger.info("Callback done_callback_log_history: browser_use_agent finished successfully.")
    print(f"Done callback!")
    # You can add more detailed history logging or processing here if needed.
    # logger.debug(f"Full agent history: {history}")

async def error_callback_decide_raise() -> bool:
    """Callback for external agent status error check."""
    logger.info("Callback error_callback_decide_raise: Invoked.")
    # This callback is expected to return a boolean.
    # True would mean an error should be raised based on external status.
    # False means no error from this callback's perspective.
    # The specific logic depends on how browser_use intends this to be used.
    return False


async def browser_use_tool(
    tool_context: ToolContext,
    url: str
) -> Dict[str, Any]:
    """Executes a browsing task to EXTRACT RAW PAGE DATA AS JSON from a specific URL.

    Handles browser setup, execution, result extraction, and screenshot saving.
    Relies on user_id and session_id being present in the ToolContext.state.
    Use this tool ONLY when the user provides a specific URL for information gathering.

    Args:
        tool_context: The ADK ToolContext (provides invocation ID and session state).
        url (str): The full URL of the website to interact with.

    Returns:
        Dict[str, Any]: A dictionary containing the status and extracted raw data or an error message.
                         Example success: {"status": "success", "data": {...}}
                         Example error:   {"status": "error", "error_message": "..."}
    """
    # Use helper to get all context IDs
    user_id, session_id, invocation_id, function_call_id = get_context_ids(tool_context)

    logger.info(f"--- Tool: browser_use_tool called [Inv: {invocation_id}, Func: {function_call_id}] ---")
    logger.info(f"  URL: {url}")
    logger.info(f"  User ID (from State): {user_id}") 
    logger.info(f"  Session ID (from State): {session_id}")

    # Validate arguments and IDs from state
    if not all([url, user_id, session_id]):
        logger.error(f"Tool: Missing required arguments OR IDs from state. URL: {url}, UserID: {user_id}, SessionID: {session_id}")
        # Return dict directly
        return {"status": "error", "error_message": "Missing required arguments or context IDs from state."}

    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    try:
        # Use helper functions
        run_sensitive_data = get_sensitive_data(url)
        execution_llm, planner_llm = get_llm_config()
        task_description = construct_task_description(url)

        # Browser Setup
        cookie_path = get_cookie_file_path(user_id)
        
        browser_config = BrowserConfig(headless=True)
        context_config = BrowserContextConfig(cookies_file=cookie_path)
        browser = Browser(config=browser_config)

        logger.info(f"Tool: Creating browser context with cookie file: {cookie_path}")
        context = await browser.new_context(config=context_config)
        logger.info(f"Tool: Browser context created.")

        partial_new_step_callback = functools.partial(
            new_step_callback_save_screenshot,
            chat_id=session_id,
            tool_context=tool_context # use this to send a message to the WebSocket client
        )

        # Create and run browser-use Agent with callbacks
        browser_use_agent = BrowserUseAgent(
            task=task_description,
            llm=execution_llm,
            planner_llm=planner_llm,
            browser_context=context,
            use_vision_for_planner=False,
            sensitive_data=run_sensitive_data if run_sensitive_data else None,
            register_new_step_callback=partial_new_step_callback,
            register_done_callback=done_callback_log_history,
            register_external_agent_status_raise_error_callback=error_callback_decide_raise
        )
        history = await browser_use_agent.run()

        # Process results - expect a dict from helper now
        result_dict = extract_result(history)
        
        # Return the dictionary directly
        return result_dict
        
    except Exception as e:
        logger.error(f"Tool: Unhandled exception during execution: {e}", exc_info=True)
        # Return error dict directly
        return {"status": "error", "error_message": f"An unexpected error occurred: {e}"}
    finally:
        # Cleanup
        browser_local = locals().get('browser')
        context_local = locals().get('context')
        
        if browser_local or context_local:
            logger.info("Tool: Cleaning up browser resources...")
            # We might double-close if error happened in try, but cleanup_resources should handle that
            await cleanup_resources(browser_local, context_local)
            logger.info(f"Tool: Browser resources cleanup finished.")
        else:
             logger.info("Tool: No browser/context resources were initialized, skipping cleanup.")