from google.adk.agents import Agent
from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

# from app.config.env import settings
# from app.features.jonas.tools import execute_browser_task_tool

AGENT_MODEL = 'gemini-2.0-flash'

# # --- Callback Function to Log History --- 
# def log_agent_context(
#     callback_context: CallbackContext, llm_request: LlmRequest
# ) -> Optional[LlmResponse]:
#     """Logs the history content being sent to the LLM before the call."""
#     print("--- Running log_agent_context callback --- ")
#     # Access history via llm_request.contents, not callback_context.session
#     print(callback_context._invocation_context)
#     history_contents = llm_request.contents
#     if history_contents:
#         print(f"DEBUG (Callback): History Contents sent to LLM (Count: {len(history_contents)}):")
#         # Print details of each content item (which represents history turns)
#         for i, content_item in enumerate(history_contents):
#             try:
#                 # content_item is likely a types.Content object
#                 role = getattr(content_item, 'role', '?')
#                 preview = ""
#                 if hasattr(content_item, 'parts') and content_item.parts:
#                    preview = str(getattr(content_item.parts[0], 'text', '[non-text part]'))[:70] + '...'
#                 print(f"  Item {i}: role={role}, content_preview='{preview}'", flush=True)
#             except Exception as e:
#                 print(f"  Item {i}: Error printing details - {e}") 
#         print("-" * 20, flush=True)
#     else:
#         print("DEBUG (Callback): No history content found in llm_request.", flush=True)
    
#     # Return None to allow the LLM call to proceed normally
#     return None
# # --- End Callback --- 

jonas = Agent(
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
    # tools=[
    #     execute_browser_task_tool,
    # ], 
    # before_model_callback=log_agent_context,
    # Enable streaming responses by default
    # stream=True, 
    # TODO: Explore ADK memory options later if needed for conversational context
    # memory=...
) 

root_agent = jonas