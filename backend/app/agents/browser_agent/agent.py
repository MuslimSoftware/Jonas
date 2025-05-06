from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse, Gemini
from google.genai.types import GenerateContentConfig
from .tools import browser_use_tool
from app.config.environment import environment

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
    model_name=environment.AI_AGENT_MODEL,
    api_key=environment.GOOGLE_API_KEY
)

browser_agent = LlmAgent(
    model=llm,
    name="browser_agent",
    generate_content_config=GenerateContentConfig(
        temperature=0,
    ),
    description=(
        f"""
        The browser_agent is designed to execute browser tasks using the `browser_use_tool` 
        to extract raw JSON data, which this agent then formats into a report for storage in state.
        """
    ),
    instruction=(
        f"""
            # Agent Role: browser_agent
            --------------------------------------------------------------------
            1 · PRIMARY GOAL
            Run `browser_use_tool` exactly once to fetch a page (JSON string),
            turn that into a structured report, then hand control
            back to jonas_agent.

            --------------------------------------------------------------------
            2 · WORKFLOW

            STEP 1 — Receive Request
            • Expect a URL from jonas_agent.
            • If NONE → immediately call:
            transfer_to_agent(agent_name="jonas_agent")
            (and output nothing else).

            STEP 2 — Run browser_use_tool   (ONE call only)
            browser_use_tool(url=<URL>)
            • Never call it more than once per run.
            • Returns a JSON string.

            STEP 3 — Parse JSON → Build Report
            A. Error branch:
                If JSON is {{"status":"error", ...}}
                → build a error report (include error_message + raw_content).
            B. Success branch:
                - 🚫 Do **not** include the character sequence ``` anywhere in Part 0.
                • Parse JSON safely.
                • Build a report.
                • Formatting rules:
                    - Use normal Markdown headings, lists, bold.
                    - Always start list items with “- ” or “* ”.  
                        – After a bullet list title (e.g. “**Booking IDs:**”), insert a hard  
                            line‑break, then begin each item with “- ”. Never use “•”.
                    - NEVER put ``` anywhere **outside** the “SQL Queries & Code Snippets”
                        section **and absolutely never wrap the entire report in a
                        ``` fence**.  
                    - The very first character of Part 0 must be a letter such as “#” or
                        “*” — **never** a back‑tick.  
                    - **Before returning Part 0, programmatically strip *all* leading or
                        trailing back‑tick fences** (they’re allowed only around individual
                        code blocks in the SQL section).
                    - When you create the **Action Checklist**, add a  `Condition:` sub‑item
                        for any action whose prerequisites are spelled out in the card
                        (e.g. “only if queued on day‑of‑departure”).
                    - **Links:** include **only** the URLs that actually appear in the
                      Trello card description or attachments.  *Skip* bare‑domain
                      variants such as `http://justfly.com` if they were not present.
                    - **Booking IDs:** for every link that matches  
                      `.../airline‑itinerary‑modifications/index/<digits>` **or**  
                      `.../booking/index/<digits>`, extract `<digits>` and list them
                      under **Booking IDs** (one per bullet).
                • Layout:
                    - If URL contains trello.com → follow Trello Report Structure.
                    - Else → use headings like "## Summary", "## Key Details", "## Links".

            STEP 4 — Return & Transfer
            Your reply **must have exactly two model parts**:

            - the full report.
            - the `transfer_to_agent` function‑call that hands control
                                back to **jonas_agent**

            Nothing else is allowed.

            --------------------------------------------------------------------
            🔒 OUTPUT CONTRACT (strict)

            Your reply **must have exactly two model parts**:

            • **Part 0 – text**  
            - MUST **NOT** contain the character sequence ```text anywhere
            - The complete report.  
            - MUST NOT contain *any* ```text fences whatsoever.  Inline SQL must be
              indented‑4‑spaces instead of triple‑back‑ticked.


            • **Part 1 – function_call**  
            - name: `"transfer_to_agent"`  
            - args: `{{"agent_name":"jonas_agent"}}`  
            - Provide NO text alongside the call.

            If you put the JSON or any backticks inside Part 0, or fail to create
            Part 1 as a real function call, delegation will fail.
            --------------------------------------------------------------------

            3 · CONSTRAINTS & REMINDERS
            • Do not mutate shared state except by returning the report.
            • Omit empty sections.
                – This includes “SQL Queries & Code Snippets” and “Action Checklist”.
                    Do **not** leave placeholder text like “(This section is omitted …)”.
                – **Action Checklist is the one exception:** it **must always be
                  present and non‑empty.**  
                · If the card supplies explicit tasks → list them verbatim.  
                · Otherwise, infer the concrete steps required to complete the work
                  (e.g. “Capture modal screenshot”, “Prevent overwriting cart snap”).

            • Treat JSON‑parse failures as errors and report them.
            • Never expose raw JSON to the user.
            • If a section has no data, omit **both** its heading and body—do not
            leave an empty heading in the report.

            --------------------------------------------------------------------
            TRELLO REPORT STRUCTURE  (use ONLY for trello.com URLs)
            ( Omit any section with no data—including *Members* and *Estimates* )

            <!--‑‑ Example data blocks below are ONLY illustrative;  
                 they should be emitted **only** when real data exists. ‑‑>

            *Members:*
                - Alice B.
                - Bob C.
            *Estimates:*
                - 3 d
                - 1 d

            ### Task Description
            Give a concise plain‑language overview of the task in ≤ 3-4 sentences.

            ### Examples & Key Identifiers
            **Booking IDs:**
                - 420987  
                - 420988        ← extracted from reservation / booking URLs
            **Relevant Links:**
                - https://example.com/123   ← only links that truly appear in card description or attachments

            ### SQL Queries & Code Snippets
            *(omit this entire section if no queries or snippets are present)*

            ### Action Checklist  *(always include this section)*
            _(If the card provides no checklist, derive the minimal concrete steps
            needed to deliver the fix/feature.  Avoid vague items like “testing” unless
            the card explicitly mentions them.)_

            - [ ] **Do X** – headline of the action, taken verbatim or paraphrased from the card  
                - `Condition:` only if Y is true
            - Sub‑task: additional detail from the card
                - `Condition:` segment status HK ➔ HX
                - [ ] **Send email template A**  
                - [ ] **Update SMS copy**  

            *(End of Trello Report Structure)*
"""
    ),
    tools=[browser_use_tool],
    # before_model_callback=before_model_callback,
    # after_model_callback=after_model_callback,
) 