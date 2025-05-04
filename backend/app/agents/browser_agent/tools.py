import traceback
import logging
import os
import json
from typing import Dict, Optional, Tuple, Any, List
from browser_use import Agent as BrowserUseAgent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from google.adk.tools import ToolContext

from .helpers.browser_use_helper import (
    get_context_ids,
    get_sensitive_data,
    get_llm_config,
    construct_task_description,
    get_cookie_file_path,
    process_and_save_screenshots,
    extract_result,
    cleanup_resources
)

logger = logging.getLogger(__name__)

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

        # Create and run browser-use Agent
        browser_use_agent = BrowserUseAgent(
            task=task_description,
            llm=execution_llm,
            planner_llm=planner_llm,
            browser_context=context,
            use_vision_for_planner=False,
            sensitive_data=run_sensitive_data if run_sensitive_data else None
        )
        history = await browser_use_agent.run()

        # Process results - expect a dict from helper now
        result_dict = extract_result(history)
        
        # Screenshot Saving logic moved to helper
        await process_and_save_screenshots(session_id, history)

        # Print the structured dict before dumping (optional)
        print("--- Browser Tool Structured Dict Output --- ")
        print(result_dict)
        print("---------------------------------------")
        
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