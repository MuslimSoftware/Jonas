from google.adk.agents import LlmAgent
from google.adk.runners import InvocationContext
from google.adk.models import LlmRequest, LlmResponse

from .tools import run_browser_task_tool
from app.agents.jonas_agent.agent import jonas_agent
from app.config.env import settings

def before_model_callback(callback_context: InvocationContext, llm_request: LlmRequest):
    """Injects user_id and session_id into the invocation state for delegation."""
    print(f"BrowserAgent BEFORE Callback: Received callback_context: {callback_context}")
    print(f"BrowserAgent BEFORE Callback: Received llm_request: {llm_request}")
        
def after_model_callback(callback_context: InvocationContext, llm_response: LlmResponse):
    """Injects user_id and session_id into the invocation state for delegation."""
    print(f"BrowserAgent AFTER Callback: Received callback_context: {callback_context}")
    print(f"BrowserAgent AFTER Callback: Received llm_response: {llm_response}")

browser_agent = LlmAgent(
    # Potentially use a different/cheaper model if suitable for just tool use?
    model=settings.AI_MODEL, 
    name="BrowserAgent",
    description=(
        "An agent specialized in accessing web pages, extracting information based on a request, and summarizing it."
    ),
    # Instruction simplified - No mention of IDs
    instruction=(
        "You are a specialized web scraping and summarization agent. Your goal is to access a web page at a given 'url' and fulfill a specific 'user_request' about its content."
        "1. You will receive the 'url' and the 'user_request' from the calling agent."
        "2. Execute the 'run_browser_task_tool' tool using ONLY these 'url' and 'user_request' arguments to retrieve the raw information or status from the webpage."
        "3. After the tool runs, carefully analyze the result returned by the tool (which will be in the history) in the context of the original 'user_request'."
        "4. Synthesize the key information relevant to the 'user_request' into a concise, factual, bullet-point summary."
        "5. Return ONLY this bullet-point summary to the calling agent. Do not include conversational filler, apologies, or explanations of your process. If the tool returned an error, report the error concisely."
    ),
    tools=[
        run_browser_task_tool,
    ],
    parent_agent=jonas_agent,
    before_model_callback=before_model_callback, 
    after_model_callback=after_model_callback,
) 