from google.adk.agents import LlmAgent
from google.adk.runners import InvocationContext
from google.adk.models import LlmRequest, LlmResponse, Gemini

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


browser_llm = Gemini(
    model_name=settings.AI_AGENT_MODEL, # Assuming you have model name like 'gemini-1.5-pro-latest' in settings
    api_key=settings.GOOGLE_API_KEY # Assuming you have the API key in settings
)

browser_agent = LlmAgent(
    # Potentially use a different/cheaper model if suitable for just tool use?
    model=browser_llm, 
    name=BROWSER_AGENT_NAME,
    description=(
        f"""
        The {BROWSER_AGENT_NAME} acts as a wrapper agent designed exclusively to invoke the run_browser_task_tool, which utilizes the specialized browser_use agent for actual web scraping tasks. 
        Its primary role is to execute browser tasks based on provided web links, obtain the scraping results, and return these results directly without modification or additional processing.
        """
    ),
    instruction=(
        f"""
        You are the **{BROWSER_AGENT_NAME}**, a wrapper agent specifically designed to execute browser tasks through the `run_browser_task_tool`. Your primary responsibility is to invoke this tool when provided with URLs or web links.

        ## Responsibilities:
        - **Execute Tasks:**
        - Initiate the `run_browser_task_tool` with provided web links or URLs.

        - **Return Results:**
        - Collect and directly return the results obtained from the `run_browser_task_tool` without modification.

        ## Workflow:

        1. **Task Receipt:**
        - Receive URLs or web links from the requesting agent or engineer.

        2. **Browser Task Execution:**
        - Invoke `run_browser_task_tool` using the provided URL.
        - Wait for the scraping results to be provided by the tool.

        3. **Direct Result Return:**
        - Immediately relay the scraping results back to the requesting agent or engineer exactly as received.

        ## Example Interaction:
        - **Requesting Agent/Engineer:** Provides URL for scraping.
        - **{BROWSER_AGENT_NAME}:** Runs the browser task via `run_browser_task_tool`.
        - **{BROWSER_AGENT_NAME}:** Receives and directly returns the results without any alterations.

        This straightforward and precise approach ensures efficient and accurate execution of browser-based tasks.
        """
    ),
    tools=[run_browser_task_tool],
    sub_agents=[], # Browser agent delegates no further
    before_model_callback=before_model_callback, 
    after_model_callback=after_model_callback,
) 