import logging
import os
from typing import Dict, Any
import asyncio
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from google.adk.tools import ToolContext
from decimal import Decimal # Import the Decimal type
from datetime import datetime # Import datetime

# Import the engine factory function from app.config
from app.infrastructure.database.external import get_external_mongo_db, get_sql_engine

# Import PyMongo related types and errors
from pymongo.errors import PyMongoError
from bson import ObjectId
import json

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
            
            # Convert RowMapping to plain dicts AND handle Decimal and datetime types
            plain_results = []
            for row in results:
                plain_row = {}
                for key, value in row.items():
                    if isinstance(value, Decimal):
                        # Convert Decimal to float for JSON compatibility
                        plain_row[key] = float(value) 
                    elif isinstance(value, datetime):
                        # Convert datetime to ISO format string for JSON compatibility
                        plain_row[key] = value.isoformat()
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

def _default_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj) # Or str(obj) if precision is critical
    raise TypeError ("Type %s not serializable" % type(obj))

def _execute_mongo_query(query_dict: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
    """Executes a read-only MongoDB find query against the 'debug_logs' collection using PyMongo."""
    db = get_external_mongo_db()
    if db is None:
        return {"status": "error", "error_message": "External MongoDB database is not initialized or configured."}

    collection_name = "debug_logs" # Hardcode collection name
    logger.info(f"DatabaseTool: Attempting to execute MongoDB query on collection '{collection_name}': {query_dict}, limit: {limit}")

    try:
        # Get the collection object
        mongo_collection = db[collection_name]

        # Execute the find query with a limit
        # Note: For more complex queries (aggregations, projections), adjust this part.
        cursor = mongo_collection.find(query_dict).limit(limit)

        # Fetch results and serialize
        results = list(cursor)
        
        # Serialize results to handle non-JSON types like ObjectId
        # Using json.dumps with a default handler is a common way
        serializable_results = json.loads(json.dumps(results, default=_default_serializer))

        logger.info(f"DatabaseTool: MongoDB query executed successfully. Documents returned: {len(serializable_results)}")
        return {"status": "success", "data": serializable_results}

    except PyMongoError as e:
        logger.error(f"DatabaseTool: PyMongo Error executing query on collection '{collection_name}': {e}", exc_info=True)
        return {"status": "error", "error_message": f"MongoDB query failed: {e}"}
    except Exception as e:
        logger.error(f"DatabaseTool: Non-PyMongo error during MongoDB query execution: {e}", exc_info=True)
        return {"status": "error", "error_message": "An unexpected error occurred during MongoDB query execution."}

async def query_mongodb_database(tool_context: ToolContext, query_dict: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
    """Executes a read-only query against the 'debug_logs' MongoDB collection using PyMongo.
    
    Args:
        tool_context: The ADK ToolContext.
        query_dict (Dict[str, Any]): The MongoDB query document (filter). Should target 'transaction_id'.
        limit (int): The maximum number of documents to return (default 25).
        
    Returns:
        dict: A dictionary containing the status and query result data or an error message.
              Example success: {"status": "success", "data": [{"..."}, {"..."}]}
              Example error:   {"status": "error", "error_message": "..."}
    """
    invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    logger.info(f"--- Tool: query_mongodb_database called [Inv: {invocation_id}] with query: {query_dict}, limit: {limit} ---")
    
    if not isinstance(query_dict, dict):
         return {"status": "error", "error_message": "MongoDB query must be a valid dictionary."}
    if "transaction_id" not in query_dict:
        logger.error(f"DatabaseTool: query_mongodb_database called without 'transaction_id' in query_dict: {query_dict}")
        return {"status": "error", "error_message": "MongoDB query for debug_logs requires 'transaction_id' in the query dictionary."}
        
    if not isinstance(limit, int) or limit <= 0:
         logger.warning(f"DatabaseTool: Invalid limit '{limit}' provided, using default 25.")
         limit = 25
        
    # In production, add more robust validation/sanitization here.

    # Execute the synchronous PyMongo function in a separate thread
    try:
        result = await asyncio.to_thread(_execute_mongo_query, query_dict, limit)
    except Exception as e:
         logger.error(f"DatabaseTool: Error running _execute_mongo_query in thread: {e}", exc_info=True)
         result = {"status": "error", "error_message": f"Failed to execute MongoDB query asynchronously."}
    
    return result 