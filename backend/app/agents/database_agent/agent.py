from google.adk.agents import LlmAgent
from app.config.env import settings
from .tools import query_sql_database, get_bookings_by_ids

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
        "Your goal is to retrieve data from the company database using the provided tools."
        "You have two main tools:"
        "  - `query_sql_database`: Use this tool ONLY when you receive a complete SQL query string to execute."
        "  - `get_bookings_by_ids`: Use this tool when asked to fetch booking details for specific booking IDs. You will receive a list of IDs."
        "Instructions:"
        "1. Determine which tool is appropriate based on the request from the calling agent ('Jonas')."
        "2. If using `query_sql_database`, pass the provided SQL string to the `query` parameter."
        "3. If using `get_bookings_by_ids`, pass the provided list of IDs to the `booking_ids` parameter."
        "4. Execute the chosen tool with the correct arguments."
        "5. Format the results returned by the tool clearly (e.g., as a list of records or a summary)."
        "6. Return ONLY the retrieved data or a confirmation/error message from the tool. Avoid conversational filler."
        "IMPORTANT: Strictly use the tools as described. Do not attempt to construct SQL queries yourself unless using `query_sql_database` with a pre-made query. Never modify data."
    ),
    tools=[query_sql_database, get_bookings_by_ids], # List available tools
    # No sub-agents needed typically for a dedicated tool-using agent
    sub_agents=[],
    # Callbacks can be added later if needed for logging/monitoring
    before_model_callback=None, 
    after_model_callback=None,
) 