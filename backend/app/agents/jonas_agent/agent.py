from google.adk.agents import LlmAgent
from google.adk.runners import InvocationContext
from google.genai.types import GenerateContentConfig
from google.adk.models import LlmRequest, LlmResponse, Gemini

from app.config.env import settings
from app.agents.database_agent.agent import database_agent
from app.agents.browser_agent.agent import browser_agent
from app.agents.browser_agent.tools import run_browser_task_tool

def before_model_callback(callback_context: InvocationContext, llm_request: LlmRequest):
    """Stores user_id and session_id into the invocation state for delegation."""
    print(f"before_model_callback {callback_context} {llm_request}")
    pass # Keep callbacks but make them no-op for now

def after_model_callback(callback_context: InvocationContext, llm_response: LlmResponse):
    """Optional: Log after LLM call (can be removed if not needed)."""
    print(f"after_model_callback {callback_context} {llm_response}")
    pass # Keep callbacks but make them no-op for now

JONAS_NAME = "Jonas"

jonas_llm = Gemini(
    model_name=settings.AI_AGENT_MODEL,
    api_key=settings.GOOGLE_API_KEY,
)

jonas_agent = LlmAgent(
    model=jonas_llm,
    name=JONAS_NAME,
    generate_content_config=GenerateContentConfig(
        temperature=0.1,
    ),
    description=(f"""
        {JONAS_NAME} is a specialized AI personal assistant designed to streamline task resolution for software engineers by efficiently gathering, integrating, and summarizing relevant contextual information.
        {JONAS_NAME} will consider the context gathered to help the engineer complete their task.
        When browsing is required, {JONAS_NAME} will delegate that task to the browser_agent.
        When database information is required, {JONAS_NAME} will delegate that task to the database_agent.
    """
    ),
    instruction=f"""
        You are {JONAS_NAME}, an AI assistant helping a software engineer analyze tasks, often from Trello cards.
        You will act as a regular software engineer assistant, providing industry standard suggestions and insights.
        You prioritize simplicity over complexity and consider business needs over technical perfection.
        
        **Delegation Workflow:**
        1. **Identify Need:** Determine if external information is needed (web via BrowserAgent for URLs, database via DatabaseAgent for IDs).
        2. **Delegate:** Call the appropriate sub-agent (`BrowserAgent` or `DatabaseAgent`) using `transfer_to_agent`.
        3. **Wait:** Remain inactive while the sub-agent works.
        4. **Receive Control Back:** A sub-agent will transfer control back to you when done.
        
        **Handling Returned Control:**
        *   **From `BrowserAgent`:** The `BrowserAgent` has already analyzed the URL, extracted information, formatted a report, and sent it directly to the user. **DO NOT send any additional message summarizing the browser findings.** Your task is complete for this turn regarding the browser action. Wait for the next user input or analyze the browser results (available in history) to see if a follow-up action like calling `DatabaseAgent` with extracted IDs is necessary.
        *   **From `DatabaseAgent`:** The `DatabaseAgent` returns raw data or results from the database. You **MUST** analyze this data and formulate a clear, concise message for the user summarizing the relevant database information.
        
        **Important Notes:**
        - Do NOT send messages to the user *while* a sub-agent is working.
        - Only send a message yourself if control returns from `DatabaseAgent`.
    """,
    sub_agents=[browser_agent, database_agent],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)

root_agent = jonas_agent