from google.adk.agents import Agent
# Correct import for InvocationContext
from google.adk.runners import InvocationContext 
# Import LlmRequest from models as the potential second arg
from google.adk.models import LlmRequest
from google.genai.types import Content, Part # Keep Content/Part for callback

# Remove direct tool import
# from app.agents.browser_agent.tools import run_browser_task_tool 
# Import the sub-agent
from app.agents.browser_agent.agent import browser_agent

from app.config.env import settings # Make sure settings are imported if needed

# Update callback signature to match keyword arguments passed by ADK
def inject_context_for_delegation(callback_context: InvocationContext, llm_request: LlmRequest):
    """Injects user_id and session_id into the LLM request history for delegation."""
    try:
        user_id = callback_context.user_id
        session_id = callback_context.session_id 
        
        if user_id and session_id:
            # Use very clear delimiters and simple format
            context_message = (
                f"<<<START_CONTEXT>>>\n" # Use newline for clarity
                f"DELEGATION_CONTEXT: user_id_str='{user_id}' chat_id_str='{session_id}'\n"
                f"<<<END_CONTEXT>>>"
            )
            
            contents = llm_request.contents
            if not isinstance(contents, list):
                 contents = [contents]

            context_part = Part(text=context_message)
            # Stick with role="model" as system role might have unintended effects
            context_content = Content(role="model", parts=[context_part]) 
            
            contents.insert(0, context_content)
            llm_request.contents = contents 

            print(f"JonasAgent Callback: Injected context: user_id={user_id}, chat_id={session_id}")
        else:
            print("JonasAgent Callback Warning: Could not extract user_id or session_id from callback_context.")
            
    except AttributeError as e:
        print(f"JonasAgent Callback Error accessing context/request: {e}.")
    except Exception as e:
        print(f"JonasAgent Callback Error: {e}")

jonas_agent = Agent(
    # Use the model from settings, not a hardcoded string
    model=settings.AI_MODEL, 
    name="JonasAgent",
    description=(
        "A helpful assistant named Jonas that can engage in general conversation "
        "or delegate tasks involving specific websites to a specialized BrowserAgent." 
    ),
    # Strengthened Instructions
    instruction=(
        "You are Jonas, a helpful AI assistant. Your primary goal is to assist the user. "
        "CRITICAL: At the very beginning of the input history for this turn, there may be a context block starting with '<<<START_CONTEXT>>>' and ending with '<<<END_CONTEXT>>>'. This block contains essential IDs required for delegation. "
        
        "If the user asks you to interact with a specific website (e.g., trello.com) or requires web browsing (e.g., check Trello): "
        "1. You MUST look for the line starting with 'DELEGATION_CONTEXT:' inside the context block. "
        "2. Extract the EXACT values for 'user_id_str' and 'chat_id_str' from that line. "
        "3. You MUST delegate the task to the 'BrowserAgent' sub-agent. "
        "4. When delegating, you MUST provide the target 'url', the 'user_request', AND the extracted 'user_id_str' and 'chat_id_str'. "
        "5. ABSOLUTELY DO NOT ask the user for their user ID or chat ID. Extract them only from the context block provided. If the context block or IDs are missing, state that you cannot proceed with the delegation due to missing context. "
        
        "After BrowserAgent returns a result, present it clearly to the user. "
        "For all other requests, engage in helpful conversation directly." 
    ),
    # Remove tools list if JonasAgent no longer calls tools directly
    tools=[], 
    # Add BrowserAgent as a sub-agent
    sub_agents=[
        browser_agent,
    ],
    # Attach the callback to JonasAgent
    before_model_callback=inject_context_for_delegation, 
    # Enable streaming responses by default
    # stream=True, 
    # TODO: Explore ADK memory options later if needed for conversational context
    # memory=...
)