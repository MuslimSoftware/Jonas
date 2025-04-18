from google.adk.agents import Agent

# Import the new tool from the browser_agent directory
from app.agents.browser_agent.tools import run_browser_task_tool

from app.config.env import settings # Make sure settings are imported if needed

jonas_agent = Agent(
    # Use the model from settings, not a hardcoded string
    model=settings.AI_MODEL, 
    name="JonasAgent",
    description=(
        "A helpful assistant named Jonas that can either engage in general conversation "
        "or use tools to interact with specific websites based on user requests. "
        "Prioritize using tools if the request involves accessing external URLs or web services." 
    ),
    instruction=(
        "You are Jonas, a helpful AI assistant. Your primary goal is to assist the user with their request. "
        "If the user asks you to interact with a specific website (providing a URL) or a task that clearly requires web access (like checking Trello), "
        "use the 'run_browser_task_tool'. Make sure to provide the 'url', 'user_request', 'user_id_str', and 'chat_id_str' arguments. You MUST extract the user ID and chat ID from the context/session information available to you. "
        "For all other requests, engage in a helpful conversation. "
        "If you are unsure whether to use the tool, ask the user for clarification."
    ),
    tools=[
        # Use the new tool
        run_browser_task_tool,
    ], 
    # before_model_callback=log_agent_context, # Example callback
    # Enable streaming responses by default
    # stream=True, 
    # TODO: Explore ADK memory options later if needed for conversational context
    # memory=...
)