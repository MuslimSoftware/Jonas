from google.adk.agents import LlmAgent # Use LlmAgent for sub-agents

# Import the tool this agent uses
from .tools import run_browser_task_tool

from app.config.env import settings

browser_agent = LlmAgent(
    # Potentially use a different/cheaper model if suitable for just tool use?
    model=settings.AI_MODEL, 
    name="BrowserAgent",
    description=(
        "An agent specialized in interacting with web pages using a browser tool. "
        "Receives URL, user request, user ID, and chat ID, executes the task, and returns the result."
    ),
    instruction=(
        "You are a specialized agent that operates a web browser based on instructions provided by a parent agent. "
        "Your sole purpose is to execute the 'run_browser_task_tool'. "
        "You will receive the following arguments from the parent agent: 'url', 'user_request', 'user_id_str', and 'chat_id_str'. "
        "Use these arguments DIRECTLY when calling the 'run_browser_task_tool'. "
        "Do not attempt to find IDs from context yourself. "
        "Return the result provided by the tool directly to the parent agent."
    ),
    tools=[
        run_browser_task_tool,
    ],
    # Sub-agents typically don't need sub-agents themselves
    # sub_agents=[], 
    # stream=False # Sub-agent results might not need streaming back directly
) 