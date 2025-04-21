import logging
from typing import Dict, Any, Optional, List
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_HOST = "your_db_host"
DB_NAME = "your_db_name"

def _execute_sql_query(query: str) -> Dict[str, Any]:
    """Placeholder for executing a read-only SQL query."""
    logger.info(f"DatabaseTool: Attempting to execute SQL query: {query[:100]}...")
    # --- SECURITY WARNING --- 
    # 1. Input Validation/Sanitization: NEVER directly execute a query string 
    #    constructed from agent input without rigorous validation and parameterization 
    #    to prevent SQL injection.
    # 2. Credentials: Use secure methods to get credentials (see above).
    # 3. Read-Only: Ensure the DB user has only read permissions.
    # 4. Error Handling: Implement robust error handling.
    
    # Example (Conceptual - Replace with your actual DB logic):
    # try:
    #    connection = connect_to_sql_db(DB_USER, DB_PASSWORD, DB_HOST, DB_NAME)
    #    cursor = connection.cursor(dictionary=True) # Fetch results as dicts
    #    # Use parameterized queries if possible!
    #    # Example if query was a template: cursor.execute(query_template, params)
    #    cursor.execute(query) 
    #    results = cursor.fetchall()
    #    cursor.close()
    #    connection.close()
    #    logger.info(f"DatabaseTool: SQL query executed successfully. Rows returned: {len(results)}")
    #    return {"status": "success", "data": results}
    # except Exception as e:
    #    logger.error(f"DatabaseTool: Error executing SQL query: {e}", exc_info=True)
    #    return {"status": "error", "error_message": f"Database query failed: {e}"}
    
    # Placeholder Response:
    logger.warning("DatabaseTool: _execute_sql_query is using placeholder data.")
    if "SELECT" in query.upper() and "FROM bookings" in query.lower() and "id = '98765'" in query.lower():
         return {"status": "success", "data": [{"id": "98765", "status": "completed", "customer_email": "test@example.com"}] }
    elif "SELECT" in query.upper():
         return {"status": "success", "data": [{"placeholder_col": "placeholder_value"}] }
    else:
         return {"status": "error", "error_message": "Placeholder only supports SELECT queries."}

# --- ADK Tool Definition --- 

async def query_sql_database(tool_context: ToolContext, query: str) -> Dict[str, Any]:
    """Executes a read-only SQL query against the company database.
    
    IMPORTANT: This tool should only be used for SELECT queries. 
    It requires the exact SQL query string to execute.
    Ensure the query is safe and does not modify data.
    
    Args:
        tool_context: The ADK ToolContext.
        query (str): The SQL query string to execute.
        
    Returns:
        dict: A dictionary containing the status and query result data or an error message.
              Example success: {"status": "success", "data": [{"col1": "val1"}, ...]}
              Example error:   {"status": "error", "error_message": "Query failed..."}
    """
    invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    logger.info(f"--- Tool: query_sql_database called [Inv: {invocation_id}] ---")
    
    # Basic check to prevent obvious modifications (enhance this significantly in production)
    if not query.strip().upper().startswith("SELECT"):
        logger.error(f"DatabaseTool: Blocked non-SELECT query: {query}")
        return {"status": "error", "error_message": "Invalid query type. Only SELECT statements are allowed."}
        
    # In production, add more robust validation/sanitization here.
    
    # Execute the query using the internal helper
    # In a real async app, consider running blocking DB calls in a separate thread 
    # using asyncio.to_thread or similar if your DB library is synchronous.
    result = _execute_sql_query(query)
    
    return result 

# --- New Tool for Specific Booking IDs --- 

async def get_bookings_by_ids(tool_context: ToolContext, booking_ids: List[int]) -> Dict[str, Any]:
    """Fetches booking details from the 'bookings' table for a list of specific booking IDs.
    
    Args:
        tool_context: The ADK ToolContext.
        booking_ids (List[int]): A list of integer booking IDs to query for.
        
    Returns:
        dict: A dictionary containing the status and query result data or an error message.
              Example success: {"status": "success", "data": [{"id": 123, ...}, {"id": 456, ...}]}
              Example error:   {"status": "error", "error_message": "Query failed..."}
    """
    invocation_id = getattr(tool_context, 'invocation_id', 'N/A')
    logger.info(f"--- Tool: get_bookings_by_ids called [Inv: {invocation_id}] with IDs: {booking_ids} ---")
    
    if not booking_ids:
        return {"status": "error", "error_message": "No booking IDs provided."}
        
    # --- IMPORTANT: Parameterization --- 
    # The following string formatting is for demonstration ONLY. 
    # In production, use parameterized queries provided by your DB library 
    # to prevent SQL injection. e.g., cursor.execute("SELECT * FROM bookings WHERE id = ANY(%s)", (booking_ids,)) for psycopg2
    try:
        # Ensure IDs are integers for safety before formatting (basic check)
        safe_ids = [int(bid) for bid in booking_ids]
        ids_string = ", ".join(map(str, safe_ids))
        query = f"SELECT * FROM bookings WHERE id IN ({ids_string})"
    except ValueError:
        logger.error(f"DatabaseTool: Invalid non-integer booking ID provided in list: {booking_ids}")
        return {"status": "error", "error_message": "Invalid booking ID format. IDs must be integers."}
        
    # Execute the query using the internal helper (which needs parameterization support ideally)
    # For now, we pass the constructed query string.
    result = _execute_sql_query(query)
    
    return result 