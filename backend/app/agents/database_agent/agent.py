from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from app.config.env import settings
from .tools import query_sql_database, get_bookings_by_ids

DATABASE_AGENT_NAME = "DatabaseAgent"

database_llm = Gemini(
    model_name=settings.AI_AGENT_MODEL,
    api_key=settings.GOOGLE_API_KEY
)

database_agent = LlmAgent(
    model=database_llm, 
    name=DATABASE_AGENT_NAME,
    description=(
        "An agent specialized in querying company databases (SQL, potentially MongoDB later) "
        "to retrieve information based on specific IDs or criteria provided by the calling agent."
    ),
    instruction=(
        f"You are {DATABASE_AGENT_NAME}, a specialized data retrieval agent."
        "Your primary goal is to retrieve data from the company database based on requests from the 'Jonas' agent."
        "Instructions:"
        "1. Analyze the incoming request from Jonas."
        "2. **If the request asks to fetch booking details and provides a list of booking IDs:**"
        "   a. Identify the list of booking IDs from the request message."
        "   b. Use the `get_bookings_by_ids` tool."
        "   c. Pass the extracted list of IDs to the `booking_ids` parameter of the tool."
        "3. **If the request provides a complete SQL query string to execute:**"
        "   a. Use the `query_sql_database` tool."
        "   b. Pass the exact SQL query string from the request to the `query` parameter of the tool."
        "4. Execute the appropriate tool."
        "5. Format the results returned by the tool clearly (e.g., as a list of records or a summary)."
        "6. Return ONLY the retrieved data or a confirmation/error message from the tool. Avoid conversational filler."
        "IMPORTANT: Only use the tools provided. If the request doesn't match the capabilities of your tools (fetching booking details by ID or executing a provided SQL query), state that you cannot fulfill the request. Never attempt to modify data."
    ),
    tools=[query_sql_database, get_bookings_by_ids],
    sub_agents=[],
    before_model_callback=None, 
    after_model_callback=None,
) 