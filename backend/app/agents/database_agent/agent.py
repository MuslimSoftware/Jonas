from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from app.config.env import settings
from .tools import query_sql_database, get_bookings_by_ids

database_llm = Gemini(
    model_name=settings.AI_AGENT_MODEL,
    api_key=settings.GOOGLE_API_KEY
)

database_agent = LlmAgent(
    model=database_llm, 
    name="database_agent",
    description=(
        "An agent specialized in querying company databases (SQL, potentially MongoDB later) "
        "to retrieve information based on specific IDs or criteria provided by the calling agent."
    ),
    instruction=f"""
        You are database_agent, a database agent
        when asked for data you will return fake SQL database records
    """,
    tools=[query_sql_database, get_bookings_by_ids],
    sub_agents=[],
    before_model_callback=None, 
    after_model_callback=None,
) 