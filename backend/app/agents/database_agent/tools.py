import logging
import os
from typing import Dict, Any, cast
import asyncio
import json
from google.adk.tools import ToolContext

# Import helper functions
from .helpers.database_helper import (
    execute_sql_query_with_engine,
    execute_mongo_query
)

# Import engine factory directly for passing to helper
from app.infrastructure.database.external import get_sql_engine 

logger = logging.getLogger(__name__)

async def query_sql_database(tool_context: ToolContext, query: str) -> Dict[str, Any]:
    """Executes a read-only SQL query string against the company database using SQLAlchemy.

    IMPORTANT: Only safe, read-only SELECT queries should be passed to this tool.

    Args:
        tool_context: The ADK ToolContext.
        query (str): The exact SQL SELECT query string to execute.

    Returns:
        Dict[str, Any]: A dictionary containing the status and query result data or an error message.
                         Example success: {"status": "success", "result": [{...}, {...}]}
                         Example error:   {"status": "error", "message": "..."}
    """
    invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    logger.info(f"--- Tool: query_sql_database called [Inv: {invocation_id}] with query: '{query[:100]}...' ---")

    sql_engine = get_sql_engine()
    if sql_engine is None:
        logger.error("Tool: Database engine is not available.")
        # Return dict directly
        return {"status": "error", "message": "Database engine is not available."}

    if not query or not isinstance(query, str):
        logger.error("Tool: Invalid SQL query provided.")
        # Return dict directly
        return {"status": "error", "message": "Invalid SQL query provided."}

    if not query.strip().upper().startswith("SELECT"):
        logger.error(f"Tool: Received non-SELECT query: {query}")
        # Return dict directly
        return {"status": "error", "message": "Invalid query type passed to tool. Only SELECT statements should be executed."}

    # Execute the synchronous helper function in a separate thread
    result_dict: Dict[str, Any]
    try:
        # Helper now returns a dict
        result_dict = await asyncio.to_thread(execute_sql_query_with_engine, sql_engine, query)
        # No need to parse JSON anymore
        # result_dict = json.loads(result_str) 
    except json.JSONDecodeError: # Keep this? Maybe helper could raise instead? For now, keep
        logger.error(f"Tool: Failed to decode JSON response from SQL helper (SHOULD NOT HAPPEN):", exc_info=True)
        result_dict = {"status": "error", "message": "Failed to decode response from database execution (Internal Error)."}
    except Exception as e:
         logger.error(f"Tool: Error running execute_sql_query_with_engine in thread: {e}", exc_info=True)
         # Return dict directly
         result_dict = {"status": "error", "message": "Failed to execute database query asynchronously."}

    # Return the dictionary directly
    return result_dict

# --- New Tool for MongoDB --- 

async def query_mongodb_database(tool_context: ToolContext, query_dict: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
    """Executes a read-only query against the 'debug_logs' MongoDB collection using PyMongo.
    
    Args:
        tool_context: The ADK ToolContext.
        query_dict (Dict[str, Any]): The MongoDB query document (filter). Should target 'transaction_id'.
        limit (int): The maximum number of documents to return (default 25).
        
    Returns:
        Dict[str, Any]: A dictionary containing the status and query result data or an error message.
                         Example success: {"status": "success", "data": [{"..."}, {"..."}]}
                         Example error:   {"status": "error", "error_message": "..."}
    """
    invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    logger.info(f"--- Tool: query_mongodb_database called [Inv: {invocation_id}] with query: {query_dict}, limit: {limit} ---")
    
    if not isinstance(query_dict, dict):
         logger.error("Tool: MongoDB query must be a valid dictionary.")
         # Return dict directly
         return {"status": "error", "error_message": "MongoDB query must be a valid dictionary."}
    if "transaction_id" not in query_dict:
        logger.error(f"Tool: query_mongodb_database called without 'transaction_id' in query_dict: {query_dict}")
        # Return dict directly
        return {"status": "error", "error_message": "MongoDB query for debug_logs requires 'transaction_id' in the query dictionary."}
        
    if not isinstance(limit, int) or limit <= 0:
         logger.warning(f"Tool: Invalid limit '{limit}' provided, using default 25.")
         limit = 25
        
    # Execute the synchronous helper function in a separate thread
    result_dict: Dict[str, Any]
    try:
        # Helper now returns a dict
        result_dict = await asyncio.to_thread(execute_mongo_query, query_dict, limit)
        # No need to parse JSON anymore
        # result_dict = json.loads(result_str)
    except json.JSONDecodeError: # Keep this? Maybe helper could raise instead? For now, keep
        logger.error(f"Tool: Failed to decode JSON response from Mongo helper (SHOULD NOT HAPPEN):", exc_info=True)
        result_dict = {"status": "error", "message": "Failed to decode response from database execution (Internal Error)."}
    except Exception as e:
         logger.error(f"Tool: Error running execute_mongo_query in thread: {e}", exc_info=True)
         # Return dict directly
         result_dict = {"status": "error", "error_message": "Failed to execute MongoDB query asynchronously."}
    
    # Return the dictionary directly
    return result_dict 