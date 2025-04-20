from google.adk.agents import LlmAgent
from google.adk.runners import InvocationContext
from google.adk.models import LlmRequest, LlmResponse

from .tools import run_browser_task_tool
from app.config.env import settings

BROWSER_AGENT_NAME = "BrowserAgent"

def before_model_callback(callback_context: InvocationContext, llm_request: LlmRequest):
    """Injects user_id and session_id into the invocation state for delegation."""
    # print(f"BrowserAgent BEFORE Callback: Received callback_context: {callback_context._invocation_context.session}")
    # print(f"BrowserAgent BEFORE Callback: Received llm_request: {llm_request}")
    pass

def after_model_callback(callback_context: InvocationContext, llm_response: LlmResponse):
    """Injects user_id and session_id into the invocation state for delegation."""
    # print(f"BrowserAgent AFTER Callback: Received callback_context: {callback_context._invocation_context.session}")
    # print(f"BrowserAgent AFTER Callback: Received llm_response: {llm_response}")
    pass

browser_agent = LlmAgent(
    # Potentially use a different/cheaper model if suitable for just tool use?
    model=settings.AI_MODEL, 
    name=BROWSER_AGENT_NAME,
    description=(
        "An agent specialized in executing detailed web browsing and scraping tasks "
        "based on instructions from a parent agent. It uses a tool to interact with web pages."
    ),
    instruction=(
        f"You are {BROWSER_AGENT_NAME}, a specialized web interaction agent."
        "Your ONLY goal is to execute the specific web task requested by the parent 'Jonas' agent using the provided tool."
        "1. You will receive the target 'url' and a detailed 'user_request' describing the exact steps to perform on that URL from the Jonas agent."
        "2. Execute the 'run_browser_task_tool' using ONLY the 'url' and 'user_request' arguments provided by Jonas."
        "3. DO NOT attempt to interpret the user's original request or decide the browsing steps yourself. Follow the instructions in the 'user_request' argument precisely."
        "4. After the tool finishes (successfully or with an error), return the result provided by the tool DIRECTLY back to the Jonas agent."
        "5. Do NOT summarize the tool's result or add any conversational text. Simply return the tool's output."
    ),
    tools=[run_browser_task_tool],
    sub_agents=[], # Browser agent delegates no further
    before_model_callback=before_model_callback, 
    after_model_callback=after_model_callback,
) 