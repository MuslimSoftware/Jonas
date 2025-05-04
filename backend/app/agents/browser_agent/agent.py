from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse, Gemini
from google.genai.types import GenerateContentConfig
from .tools import run_browser_task_tool
from app.config.env import settings

def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest):
    """Injects user_id and session_id into the invocation state for delegation."""
    # print(f"BrowserAgent BEFORE Callback: Received callback_context: {callback_context._invocation_context.session}")
    # print(f"BrowserAgent BEFORE Callback: Received llm_request: {llm_request}")
    pass

def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse):  
    """Extracts the report text from the LLM response and stores it in the invocation state."""  
    print(f"--- BrowserAgent AFTER Callback START ---")
    print(f"Received llm_response: {llm_response}")
      
    report_text = None  
    if llm_response.content and llm_response.content.parts:  
        print(f"LLM response has {len(llm_response.content.parts)} part(s).")
        # Assuming the report text is the first part if multiple parts exist (e.g., text + function call)  
        for i, part in enumerate(llm_response.content.parts):  
            print(f"Processing part {i}: {part}")
            if part.text:  
                report_text = part.text  
                print(f"Found text in part {i}: '{report_text[:50]}...'") # Print first 100 chars
                break # Take the first text part found  
  
    if report_text:  
        key = "browser_agent_report"
        print(f"Attempting to store report in state with key: '{key}'")
        callback_context.state[key] = report_text
    else:  
        print("No text report found in LLM response parts to store in state.")  
      
    # We don't modify the original llm_response, just the state.  
    # Return None to indicate we're not replacing the response  
    print(f"--- BrowserAgent AFTER Callback END ---")
    return None

llm = Gemini(
    model_name=settings.AI_AGENT_MODEL,
    api_key=settings.GOOGLE_API_KEY
)

browser_agent = LlmAgent(
    model=llm,
    name="browser_agent",
    generate_content_config=GenerateContentConfig(
        temperature=0,
    ),
    description=(
        f"""
        The browser_agent is designed to execute browser tasks using the `run_browser_task_tool` 
        to extract raw JSON data, which this agent then formats into a report for storage in state.
        """
    ),
    instruction=(
        f"""
        # Agent Role: browser_agent

        ## Primary Goal:
        Use the `run_browser_task_tool` to extract raw page data (as a JSON string) from a given URL. Parse this JSON, generate a structured Markdown report, and prepare for transfer to the "Jonas" agent.

        ## Workflow Steps:

        ### 1. Receive Request:
        - Input: A URL.

        ### 2. Run Browser Tool:
        - Action: Call `run_browser_task_tool` with the input `url`. You MUST run this tool exactly one time.
        - **Constraint: Under no circumstances should you call `run_browser_task_tool` more than once in your execution.**
        - Tool Output: A JSON *string* containing either the extracted raw data or an error message.

        ### 3. Parse JSON & Generate Report:
        - **Input:** JSON string from the `run_browser_task_tool` function.
        - **Actions:**
            - Parse the JSON string from the `run_browser_task_tool` function. Handle potential JSON parsing errors gracefully.
            - Analyze the parsed data structure.
            - Generate a Markdown report based on the parsed data.
        - **Markdown Formatting Rules:**
            - **Use** standard Markdown (headings, lists, bold, etc.).
            - **DO NOT** wrap the *entire* report output in markdown code fences (e.g., ```markdown ... ```).
        - **Conditional Report Structure:**
            - **IF** the original input `url` contains 'trello.com':
                - Follow the **"Trello Report Structure"** section below *strictly*.
            - **ELSE** (for any other URL):
                - Create a well-structured Markdown report summarizing key information.
                - Use clear headings (e.g., `## Summary`, `## Key Details`, `## Links`) based on the content.

        ### 4. Output Report and Initiate Transfer:
        - **Final Response MUST contain BOTH:**
            1. The *complete* report text generated in Step 3.
            2. A function call: `transfer_to_agent(agent_name="Jonas")`.
        - **Important Note:** A system callback will automatically save your report text to shared state *before* the transfer call is executed. Ensure the report text is present in your response.

        ---

        ## Trello Report Structure (Strictly for trello.com URLs):

        **General Rule: Omit Empty Sections.** If the JSON data does not contain information corresponding to any section or sub-section below (e.g., Members, Estimates, Task Description, specific checklist items), **completely omit that section, including its heading or bullet point,** from the final Markdown report.

        *(Note: The following shows the required structure ONLY for sections where data exists. Follow the General Rule above.)*
        
        **Members:** [List Members from JSON if there are members assigned to the task]
        
        **Estimates:** [List Estimates from JSON if there are estimates for the task]

        ### Task Description
        [Insert description/summary from JSON. Clearly state the core issue/task.]

        ### Examples & Key Identifiers
        *   **Booking IDs:** (Typically at the end of reservation.voyage.com URLs, e.g., .../273869091)
            - 420987
            - 420988
            - 420989
        *   **Relevant Links:**
            - https://reservation.voyagesalacarte.com/273869091
            - https://reservation.voyagesalacarte.com/273869092
            - https://docs.google.com/document/d/1234567890/edit
            - https://www.figma.com/design/1234567890/1234567890
        ### Action Checklist
        [Analyze the Trello card description and content provided in the JSON data. Create a checklist outlining the specific, concrete actions required to complete the task as described in the card. **Extract only explicitly mentioned actions.** Do *not* add generic tasks like 'testing' or 'deployment' unless the card specifically requests them. If the card mentions conditions under which an action should be performed, include them using the `Condition` sub-item.]
        [If the JSON data contains a pre-existing checklist, replicate its items and structure accurately here, including any conditions.]
        - [ ] [Action item derived *directly* from card description]
          - `Condition`: [Include only if the card specifies a condition for this action]
          - [Optional: Sub-item derived *directly* from card description]
        - [ ] [Another action item derived *directly* from card description]
          - `Condition`: [Include only if the card specifies a condition for this action]
        ...

        *(End of Trello Report Structure)*

        ---
        """
    ),
    tools=[run_browser_task_tool],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
) 