from google.adk.agents import LlmAgent
from google.adk.runners import InvocationContext
from google.adk.models import LlmRequest, LlmResponse

from app.config.env import settings
from app.agents.browser_agent.agent import browser_agent
from app.agents.database_agent.agent import database_agent

JONAS_NAME = "Jonas"

def before_model_callback(callback_context: InvocationContext, llm_request: LlmRequest):
    """Stores user_id and session_id into the invocation state for delegation."""
    # Print session history length to verify it's available
    try:
        history_events = callback_context._invocation_context.session.events
        print(f"JonasAgent BEFORE Callback: Found {len(history_events)} events in session history.")
        # Optional: Print last few events for more detail
        # if history_events:
        #     print(f"  Last event: {history_events[-1]}") 
    except Exception as e:
        print(f"JonasAgent BEFORE Callback: Error accessing session events: {e}")

    pass # Keep callbacks but make them no-op for now

def after_model_callback(callback_context: InvocationContext, llm_response: LlmResponse):
    """Optional: Log after LLM call (can be removed if not needed)."""
    # print(f"JonasAgent AFTER Callback: Invocation state: {callback_context._invocation_context.session}")
    # print(f"JonasAgent AFTER Callback: Received llm_response: {llm_response}")
    pass # Keep callbacks but make them no-op for now

jonas_agent = LlmAgent(
    model=settings.AI_MODEL, 
    name=JONAS_NAME,
    description=(
        "A helpful assistant named Jonas that orchestrates web browsing and database queries "
        "to analyze software engineering tasks, typically originating from Trello cards."
    ),
    instruction=f"""You are {JONAS_NAME}, a helpful AI assistant acting as an orchestrator.
Your primary goal is to analyze a software engineering task, usually provided via a Trello card URL, by coordinating with sub-agents.

Workflow Steps:
1. Receive the user request (likely containing a Trello URL and a task like 'analyze' or 'explain').
2. **Delegate to BrowserAgent:** Construct a detailed 'user_request' for BrowserAgent. This request should instruct it to:
    a. Navigate to the main URL (e.g., Trello card).
    b. Extract key information (description, comments, etc.).
    c. Identify ALL links within the card (GDocs, Figma, Respro, etc.).
    d. For GDocs/Figma links: Navigate and extract/summarize content.
    e. **For Respro links: DO NOT NAVIGATE.** Extract ONLY the booking ID (usually the number at the end of the URL).
    f. Explicitly identify and list any other potential Booking IDs or other relevant identifiers found anywhere.
    g. Call BrowserAgent using `transfer_to_agent` with the original main URL and this detailed 'user_request'.
3. **Receive BrowserAgent Result:** Get the structured information back (summaries, list of extracted IDs).
4. **Delegate to DatabaseAgent (If Needed):** If BrowserAgent returned relevant IDs (like Booking IDs), construct a request for DatabaseAgent:
    a. Formulate the necessary SQL query (e.g., 'SELECT * FROM bookings WHERE id = [BookingID]').
    b. Call DatabaseAgent using `transfer_to_agent` with the query details (e.g., passing the SQL query as an argument).
    c. Receive the database results.
5. **Synthesize Final Response:** Combine the information from BrowserAgent and DatabaseAgent into a structured summary for the user. Use sections like:
    - **Overview:** Summary of the Trello card itself.
    - **Linked Resources:** Summaries from GDocs/Figma.
    - **Database Info:** Details retrieved for relevant IDs (e.g., Booking ID details).
    - **Checklist/Key Points:** If applicable, derive a checklist or highlight key aspects of the task.
6. **Error Handling:** If any sub-agent returns an error, report it clearly to the user.

IMPORTANT: Only delegate tasks appropriate for each sub-agent based on their descriptions. Pass only the required arguments to the sub-agents.
""",
    # JonasAgent itself doesn't directly use tools; it delegates.
    tools=[],
    sub_agents=[browser_agent, database_agent], # Define the agents Jonas can delegate to
    before_model_callback=before_model_callback, # Keep callback hook
    after_model_callback=after_model_callback,   # Keep callback hook
    # stream=True, # Consider enabling streaming later if needed
    # memory=...   # Consider adding memory later if needed
)

root_agent = jonas_agent