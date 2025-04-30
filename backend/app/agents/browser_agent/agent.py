from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse, Gemini
from google.genai.types import GenerateContentConfig
from .tools import run_browser_task_tool
from app.config.env import settings

BROWSER_AGENT_NAME = "browser_agent"

def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest):
    """Injects user_id and session_id into the invocation state for delegation."""
    # print(f"BrowserAgent BEFORE Callback: Received callback_context: {callback_context._invocation_context.session}")
    # print(f"BrowserAgent BEFORE Callback: Received llm_request: {llm_request}")
    pass

def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse):  
    """Extracts the report text from the LLM response and stores it in the invocation state."""  
    print(f"--- BrowserAgent AFTER Callback START ---")
    print(f"Received llm_response: {llm_response}")
    print(f"Initial State: {callback_context.state.to_dict()}")
      
    report_text = None  
    if llm_response.content and llm_response.content.parts:  
        print(f"LLM response has {len(llm_response.content.parts)} part(s).")
        # Assuming the report text is the first part if multiple parts exist (e.g., text + function call)  
        for i, part in enumerate(llm_response.content.parts):  
            print(f"Processing part {i}: {part}")
            if part.text:  
                report_text = part.text  
                print(f"Found text in part {i}: '{report_text[:100]}...'") # Print first 100 chars
                break # Take the first text part found  
  
    if report_text:  
        # Store the report in the state for the root agent (Jonas) to access  
        # Make sure the key is unique and descriptive  
        key = "browser_agent_report"
        print(f"Attempting to store report in state with key: '{key}'")  
        callback_context.state[key] = report_text  
        print(f"State after setting '{key}': {callback_context.state.to_dict()}")
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
    name=BROWSER_AGENT_NAME,
    generate_content_config=GenerateContentConfig(
        temperature=0.1, # Lower temperature for more deterministic report generation
    ),
    description=(
        f"""
        The {BROWSER_AGENT_NAME} is designed to execute browser tasks using the `run_browser_task_tool` 
        to extract raw JSON data, which this agent then formats into a report for storage in state.
        """
    ),
    instruction=(
        f"""
        You are the **{BROWSER_AGENT_NAME}**. Your goal is to use the `run_browser_task_tool` to get raw page data as a JSON string, parse the JSON, and then format a Markdown report.

        **Workflow:**
        1.  **Receive Request:** You'll be given a URL.
        2.  **Run Browser Tool:** Call the `run_browser_task_tool` with the provided `url`. This tool returns a JSON *string* containing the extracted raw data (or a JSON error string).
        3.  **Parse JSON & Generate Report:** 
            *   Receive the JSON string result from the tool.
            *   Parse the JSON string into an internal data structure. Handle potential JSON errors.
            *   Analyze the parsed data structure.
            *   Generate a Markdown report based on the parsed data. **Use Markdown formatting for headings, lists, bolding, etc., but DO NOT wrap the entire report output in markdown code fences (like ```markdown ... ```).**
            *   **Conditional Formatting:**
                *   **IF** the original input `url` contains 'trello.com': Format the report *strictly* following the structure in the **Trello Report Example** below, using the parsed JSON data.
                *   **ELSE** (for any other URL): Create a well-structured Markdown report summarizing the key information from the parsed JSON data. Use clear headings (like `## Summary`, `## Key Details`, `## Links`, etc.) based on your best judgment of the content.
        4.  **Output Report and Transfer Call:** Your final response MUST contain BOTH:
            1.  The complete Markdown report text you generated.
            2.  A function call to `transfer_to_agent` with the argument `agent_name="Jonas"`.
            *   **Important:** The system will use a callback to save the report text to shared state *before* executing the transfer. Your report text is necessary for this callback.

        **Trello Report Example (Use ONLY for trello.com URLs):**
        *(This example shows the desired final MARKDOWN structure, not wrapped in code fences)*
        *(Optional: Include **Assignees:** [List] ONLY IF assignees were found in the JSON data)*
        *(Optional: Include **Estimates:** [List] ONLY IF estimates were found in the JSON data)*

        ## Problem Description
        [Insert the extracted description/summary from the JSON data here. Focus on clearly stating the core issue or things to implement.]

        ## Examples & Key Identifiers (List the following ONLY if found in JSON data)
        *   **Booking IDs:** 
            - [List extracted Booking IDs from JSON data. If none are found, omit this entire 'Booking IDs' line.]
        *   **Other IDs:** 
            - [List any other relevant IDs from JSON data. If none are found, omit this entire 'Other IDs' line.]
        *   **Relevant Links:** 
            - [List key URLs from JSON data. If none found, omit this line.]

        ## Action Checklist
        [If a checklist exists in the JSON data, list its items *exactly* here.]
        [If **no** checklist exists in the JSON data, generate one by identifying the main Solutions or Problem areas described in the JSON data. For each Solution/Area, create a main bullet point. Underneath each main point, use indented bullet points (-) to list the specific requirements, validation rules, error messages, or conditions associated with that Solution/Area based on the description.]
        [If a checklist is extracted or generated, include this section with the items listed below. Otherwise, omit this entire section.]
        - [ ] Item 1
          - **Condition**: [Describe the condition under which this action applies IF applicable] 
          - item 1 sub-item a
          - item 1 sub-item b

        - [ ] Item 2
          - **Condition**: [Describe the condition under which this action applies IF applicable]
          - item 2 sub-item c
        ...
        *(End of Trello Report Example)*

        **Error Handling:** If the JSON string received from the tool indicates an error (e.g., contains `{{"status": "error"...}}`), the Markdown report you generate should state the error message clearly.
        """
    ),
    tools=[run_browser_task_tool],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
) 