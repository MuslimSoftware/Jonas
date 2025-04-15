from google.adk.agents import LlmAgent

from app.config.env import settings
from app.features.jonas.tools import execute_browser_task_tool

AGENT_MODEL = 'gemini-2.0-flash'

jonas_agent = LlmAgent(
    model=AGENT_MODEL,
    name="JonasAgent",
    description=(
        "A helpful assistant named Jonas that can either engage in general conversation "
        "or use tools to interact with specific websites based on user requests. "
        "Prioritize using tools if the request involves accessing external URLs or web services." 
    ),
    instruction=(
        "You are Jonas, a helpful AI assistant. Your primary goal is to assist the user with their request. "
        "If the user asks you to interact with a specific website (providing a URL) or a task that clearly requires web access (like checking Trello), "
        "use the 'execute_browser_task_tool'. "
        "For all other requests, engage in a helpful conversation. "
        "If you are unsure whether to use the tool, ask the user for clarification."
    ),
    tools=[
        execute_browser_task_tool,
    ], 
    # Enable streaming responses by default
    # stream=True, 
    # TODO: Explore ADK memory options later if needed for conversational context
    # memory=...
) 