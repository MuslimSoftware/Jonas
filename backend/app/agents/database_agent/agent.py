from google.adk.agents import LlmAgent
from app.config.env import settings
from .tools import query_sql_database # Import the tool

DATABASE_AGENT_NAME = "DatabaseAgent"

database_agent = LlmAgent(
    model=settings.AI_MODEL, 
    name=DATABASE_AGENT_NAME,
    description=(
        "An agent specialized in querying company databases (SQL, potentially MongoDB later) "
        "to retrieve information based on specific IDs or criteria provided by the calling agent."
    ),
    instruction=(
        f"You are {DATABASE_AGENT_NAME}, a specialized data retrieval agent."
        "Your goal is to execute database queries based on requests from the main 'Jonas' agent."
        "1. You will receive specific instructions, usually including IDs (like booking IDs) and the type of query needed."
        "2. Use the appropriate database query tool provided (e.g., 'query_sql_database') to fetch the data."
        "3. Pass the necessary parameters (like the query string or filter criteria) to the tool."
        "4. Once the tool returns the results, format them clearly (e.g., as a list of records or a summary if requested)."
        "5. Return ONLY the retrieved data or a confirmation/error message from the tool. Do not add conversational filler."
        "IMPORTANT: Never attempt to modify data (no INSERT, UPDATE, DELETE). Only use tools for read operations."
    ),
    tools=[query_sql_database], # List the query tool(s)
    # No sub-agents needed typically for a dedicated tool-using agent
    sub_agents=[],
    # Callbacks can be added later if needed for logging/monitoring
    before_model_callback=None, 
    after_model_callback=None,
) 