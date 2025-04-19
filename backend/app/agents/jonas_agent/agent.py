from google.adk.agents import LlmAgent
from google.adk.runners import InvocationContext
from google.adk.models import LlmRequest, LlmResponse

from app.config.env import settings # Make sure settings are imported if needed

JONAS_NAME = "Jonas"

def before_model_callback(callback_context: InvocationContext, llm_request: LlmRequest):
    """Stores user_id and session_id into the invocation state for delegation."""
    print(f"JonasAgent BEFORE Callback: Attempting to store IDs...")
    try:
        user_id = callback_context.user_id
        session_id = callback_context.session_id
        if user_id and session_id:
            callback_context.state['delegation_user_id'] = user_id
            callback_context.state['delegation_session_id'] = session_id
            print(f"JonasAgent BEFORE Callback: Stored IDs in state: User='{user_id}', Session='{session_id}'")
        else:
            print(f"JonasAgent BEFORE Callback Warning: user_id ('{user_id}') or session_id ('{session_id}') missing in InvocationContext. Cannot store in state.")
    except AttributeError:
         print(f"JonasAgent BEFORE Callback Error: user_id or session_id attribute not found on callback_context ({type(callback_context)}). State not updated.")
    except Exception as e:
         print(f"JonasAgent BEFORE Callback Error storing IDs in state: {e}")

def after_model_callback(callback_context: InvocationContext, llm_response: LlmResponse):
    """Optional: Log after LLM call (can be removed if not needed)."""
    print(f"JonasAgent AFTER Callback: Invocation state: {callback_context.state}")
    print(f"JonasAgent AFTER Callback: Received llm_response: {llm_response}")

jonas_agent = LlmAgent(
    model=settings.AI_MODEL, 
    name=JONAS_NAME,
    description=(
        "A helpful assistant named Jonas that can engage in general conversation "
        "or delegate tasks involving specific websites to a specialized BrowserAgent." 
    ),
    # Simplified Instructions - No mention of IDs
    instruction=(
        f"You are {JONAS_NAME}, a helpful AI assistant. Your primary goal is to answer the user's request comprehensively."
        
        "Engage in normal conversation for most requests. However, if the user's request mentions a specific URL AND requires information *from* that URL to be fully answered (e.g., summarizing a page, explaining a Trello card, finding specific details on a website):"
        "1. Identify the full 'url'."
        "2. Determine the specific 'user_request' related to that URL (e.g., 'summarize the main points', 'explain the Trello card', 'find the contact email')."
        "3. You have a sub-agent called 'BrowserAgent' that can access web pages. Delegate the task to 'BrowserAgent' by calling it with ONLY the identified 'url' and 'user_request' arguments. Do this silently without notifying the user you are delegating."
        "4. Once 'BrowserAgent' provides its result, incorporate that result into your final answer to the user, addressing their original request fully."
        "5. IMPORTANT: Only delegate if information *from the URL itself* is clearly needed. Do not delegate for general web searches or if the URL is just mentioned incidentally."
        "6. Handle potential errors returned by the BrowserAgent gracefully (e.g., 'I couldn't access that URL' or 'The browser tool encountered an error')."
    ),
    # Remove tools list if JonasAgent no longer calls tools directly
    tools=[], 
    before_model_callback=before_model_callback, 
    after_model_callback=after_model_callback,
    # stream=True, 
    # memory=...
)

root_agent = jonas_agent