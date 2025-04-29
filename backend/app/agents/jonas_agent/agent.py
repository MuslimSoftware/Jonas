from google.adk.agents import LlmAgent
from google.adk.runners import InvocationContext
from google.genai.types import GenerateContentConfig
from google.adk.models import LlmRequest, LlmResponse, Gemini

from app.config.env import settings
from app.agents.database_agent.agent import database_agent
from app.agents.browser_agent.agent import browser_agent

def before_model_callback(callback_context: InvocationContext, llm_request: LlmRequest):
    """Stores user_id and session_id into the invocation state for delegation."""
    # print(f"before_model_callback {callback_context} {llm_request}")
    pass # Keep callbacks but make them no-op for now

def after_model_callback(callback_context: InvocationContext, llm_response: LlmResponse):
    """Optional: Log after LLM call (can be removed if not needed)."""
    # print(f"after_model_callback {callback_context} {llm_response}")
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
        1. **Identify Need:** Determine if external information is needed (web via `browser_agent` for URLs, database via `database_agent` for IDs).
        2. **Delegate:** Call the appropriate sub-agent (`browser_agent` or `database_agent`) using `transfer_to_agent`.
        3. **Wait:** Remain inactive while the sub-agent works.
        4. **Receive Control Back:** A sub-agent will transfer control back to you when done.
        
        **Handling Returned Control:**
        *   **From `browser_agent`:** Control returns *after* the `browser_agent` has finished processing. Check the session state for a key named `browser_agent_report`. 
            *   **If `browser_agent_report` key exists in the state:** Retrieve the string value associated with the `browser_agent_report` key. Your response for this turn MUST be that exact string value, outputted verbatim. **Treat the retrieved value as pre-formatted Markdown and preserve all characters, including headings (`##`), asterisks (`*`), brackets (`[]`), etc.** Do not attempt to summarize, rephrase, or alter the formatting in any way.
            *   **If `browser_agent_report` key does NOT exist in the state:** Respond with a message indicating that the browser report could not be retrieved from the state.
        *   **From `database_agent`:** The `database_agent` returns raw data or results from the database. You **MUST** analyze this data and formulate a clear, concise message for the user summarizing the relevant database information.
        
        **Important Notes:**
        - Do NOT send messages to the user *while* a sub-agent is working.
    """,
    sub_agents=[browser_agent, database_agent],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)

root_agent = jonas_agent