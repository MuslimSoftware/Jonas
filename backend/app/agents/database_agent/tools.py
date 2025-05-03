import logging
import os
from typing import Dict, Any
import asyncio
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from google.adk.tools import ToolContext
from decimal import Decimal # Import the Decimal type

# Import the engine factory function from app.config
from app.config import get_sql_engine 

logger = logging.getLogger(__name__)

def _execute_sql_query_with_engine(sql_engine: Engine, query: str) -> Dict[str, Any]:
    """Executes a read-only SQL query using a pooled SQLAlchemy connection."""
    if sql_engine is None:
        return {"status": "error", "message": "Database engine is not initialized."}

    logger.info(f"DatabaseTool: Attempting to execute SQL query via SQLAlchemy: '{query[:100]}...'")

    try:
        with sql_engine.connect() as connection:
            # IMPORTANT: Wrap raw SQL in text() for safety and compatibility
            # Use .mappings().fetchmany(25) to get results as list of dict-like objects
            result_proxy = connection.execute(text(query))
            
            # Fetch all results returned by the (potentially limited) SQL query
            results = result_proxy.mappings().all()
            
            # Convert RowMapping to plain dicts AND handle Decimal types
            plain_results = []
            for row in results:
                plain_row = {}
                for key, value in row.items():
                    if isinstance(value, Decimal):
                        # Convert Decimal to float for JSON compatibility
                        plain_row[key] = float(value) 
                    else:
                        plain_row[key] = value
                plain_results.append(plain_row)
                
            logger.info(f"DatabaseTool: SQLAlchemy query executed successfully. Rows returned: {len(plain_results)}")
            return {"status": "success", "result": plain_results}

    except SQLAlchemyError as e:
        # Catch specific SQLAlchemy errors
        logger.error(f"DatabaseTool: SQLAlchemy Error executing query: {e}", exc_info=True)
        error_code = getattr(e.orig, 'errno', 'N/A') # Try to get original DB error code
        error_msg = getattr(e.orig, 'msg', str(e))  # Try to get original DB error message
        return {"status": "error", "message": f"Database query failed (Code: {error_code}, Msg: {error_msg})"}
    except Exception as e:
        # Catch other potential errors
        logger.error(f"DatabaseTool: Non-SQLAlchemy error during query execution: {e}", exc_info=True)
        return {"status": "error", "message": f"An unexpected error occurred during database query execution."}

async def query_sql_database(tool_context: ToolContext, query: str) -> Dict[str, Any]:
    """Executes a read-only SQL query string against the company database using SQLAlchemy.

    IMPORTANT: Only safe, read-only SELECT queries should be passed to this tool.

    Args:
        tool_context: The ADK ToolContext.
        query (str): The exact SQL SELECT query string to execute.

    Returns:
        dict: A dictionary containing the status and query result data or an error message.
              Example success: {"status": "success", "data": [{...}, {...}]}
              Example error:   {"status": "error", "message": "..."}
    """
    invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    logger.info(f"--- Tool: query_sql_database called [Inv: {invocation_id}] with query: '{query[:100]}...' ---")

    sql_engine = get_sql_engine()
    if sql_engine is None:
        # Engine initialization failed earlier
        return {"status": "error", "message": "Database engine is not available."}

    if not query or not isinstance(query, str):
        return {"status": "error", "message": "Invalid SQL query provided."}

    # Basic check (agent should ensure only SELECT, but double-check here)
    if not query.strip().upper().startswith("SELECT"):
        logger.error(f"DatabaseTool: Tool received non-SELECT query: {query}")
        return {"status": "error", "message": "Invalid query type passed to tool. Only SELECT statements should be executed."}

    # Execute the synchronous DB function using the engine in a separate thread
    try:
        result = await asyncio.to_thread(_execute_sql_query_with_engine, sql_engine, query)
    except Exception as e:
         logger.error(f"DatabaseTool: Error running _execute_sql_query_with_engine in thread: {e}", exc_info=True)
         result = {"status": "error", "message": f"Failed to execute database query asynchronously."}

    return result

# --- New Tool for MongoDB --- 

async def query_mongodb_database(tool_context: ToolContext, collection: str, query_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Executes a read-only query against a MongoDB collection.
    
    Args:
        tool_context: The ADK ToolContext.
        collection (str): The name of the MongoDB collection to query.
        query_dict (Dict[str, Any]): The MongoDB query document (filter).
        
    Returns:
        dict: A dictionary containing the status and query result data or an error message.
              Example success: {"status": "success", "data": [{"_id": "abc", ...}, ...]}
              Example error:   {"status": "error", "error_message": "Query failed..."}
    """
    invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    logger.info(f"--- Tool: query_mongodb_database called [Inv: {invocation_id}] on collection '{collection}' with query: {query_dict} ---")
    
    if not collection:
        return {"status": "error", "error_message": "MongoDB collection name not specified."}
    if not isinstance(query_dict, dict):
         return {"status": "error", "error_message": "MongoDB query must be a valid dictionary."}
        
    # In production, add more robust validation/sanitization here.

    # Execute the query using the internal helper
    # Consider asyncio.to_thread if using a synchronous library like pymongo
    result = _execute_mongo_query(collection, query_dict)
    
    return result 

def _execute_mongo_query(collection: str, query_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder: Executes a read-only MongoDB query."""
    logger.warning("DatabaseTool: _execute_mongo_query is using placeholder data.")
    return {"status": "success", "data": [{"_id": "abc", "name": "Fake Customer", "email": "placeholder@example.com"}]}