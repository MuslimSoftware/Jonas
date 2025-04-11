import asyncio
from typing import TYPE_CHECKING, Dict, Any, List, Optional

# Assuming Message model is in chat features
# We might need Task model later if conversation needs task context
from app.features.chat.models import Message

# Use LlmService now
# from app.llm import get_chat_completion 
from app.features.agent.schemas import InputSourceType # Correct import for Enum

# Placeholder for actions
class ConversationAction:
    SAVE_MESSAGE_ONLY = "SAVE_MESSAGE_ONLY"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    # PROPOSE_TASK = "PROPOSE_TASK" # Skipping explicit proposal for now
    CREATE_AND_START_TASK = "CREATE_AND_START_TASK"
    ERROR = "ERROR" # Action for when analysis fails

if TYPE_CHECKING:
    from ..repositories import TaskRepository # If needed
    from app.features.llm.services import LlmService

class ConversationService:
    """
    Analyzes conversation messages to determine user intent regarding task creation.
    Handles the conversational flow before a formal task is created.
    """
    def __init__(self,
        llm_service: "LlmService",
        # TODO: Inject TaskRepository if needed later
        # task_repo: "TaskRepository"
    ):
        self.llm_service = llm_service # Store injected LlmService
        # self.task_repo = task_repo
        print("ConversationService initialized")

    async def _analyze_intent_with_llm(self, user_message: str, history: Optional[List[Message]]) -> Dict[str, Any]:
        """Uses LLM to determine intent and extract details."""
        system_prompt = ( # Updated Prompt
            f"You are an assistant helping manage software development tasks. "
            f"Analyze the user's message in the context of the conversation history. "
            f"Determine the user's primary intent: CHAT, ASK_CLARIFICATION, or CREATE_TASK. "
            f"If the intent is CREATE_TASK, identify the input source (TRELLO, GOOGLE_DOC, TEXT) and extract the relevant input data (URL or description). "
            f"If the intent is ASK_CLARIFICATION, explain what information is missing. "
            f"If the intent is CHAT, provide a brief, relevant, and acknowledging chat response (e.g., 'Got it.', 'Okay, I see.'). " # Added instruction for CHAT response
            f"Respond ONLY with JSON containing 'intent' (CHAT, ASK_CLARIFICATION, CREATE_TASK), 'source_type' (if CREATE_TASK, else null), 'input_data' (if CREATE_TASK, else null), 'clarification_needed' (if ASK_CLARIFICATION, else null), and 'chat_response' (if CHAT, else null)."
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history (simplified example - needs better formatting)
        if history:
             for msg in history[-5:]: # Limit history length
                 role = "user" if msg.sender_type == "user" else "assistant"
                 messages.append({"role": role, "content": msg.content})

        messages.append({"role": "user", "content": user_message})

        print(f"ConversationService: Sending to LLM Service: {messages}")
        # Use injected LlmService
        response_content = await self.llm_service.get_chat_completion(messages=messages, max_tokens=250) # Slightly increased tokens
        print(f"ConversationService: Received LLM response: {response_content}")

        if not response_content:
            return {"intent": "ERROR", "error_message": "LLM call failed or returned empty content."} 

        try:
            # Attempt to parse the JSON response from the LLM
            import json
            parsed_response = json.loads(response_content)
            # Basic validation of expected keys
            if not isinstance(parsed_response, dict) or "intent" not in parsed_response:
                print(f"ConversationService: LLM response missing 'intent' key.")
                return {"intent": "ERROR", "error_message": "LLM response format incorrect (missing intent)."} 
            
            # Ensure required fields are present based on intent
            intent = parsed_response.get("intent")
            if intent == "CREATE_TASK" and ("source_type" not in parsed_response or "input_data" not in parsed_response):
                 print(f"ConversationService: LLM CREATE_TASK response missing source_type or input_data.")
                 return {"intent": "ERROR", "error_message": "LLM response format incorrect (missing task details)."} 
            if intent == "ASK_CLARIFICATION" and "clarification_needed" not in parsed_response:
                 print(f"ConversationService: LLM ASK_CLARIFICATION response missing clarification_needed.")
                 return {"intent": "ERROR", "error_message": "LLM response format incorrect (missing clarification)."} 
            if intent == "CHAT" and "chat_response" not in parsed_response:
                 print(f"ConversationService: LLM CHAT response missing chat_response.")
                 # Default to a simple ack if LLM forgets
                 parsed_response["chat_response"] = "Okay."

            return parsed_response # Return validated dict
        except json.JSONDecodeError:
            print(f"ConversationService: LLM response was not valid JSON: {response_content}")
            # Fallback or error handling - maybe treat as chat?
            return {"intent": "ERROR", "error_message": "LLM response was not valid JSON."} 
        except Exception as e:
             print(f"ConversationService: Error processing LLM response: {e}")
             return {"intent": "ERROR", "error_message": f"Error processing LLM response: {e}"} 

    async def determine_next_action(
        self,
        user_message_content: str,
        chat_id: str, 
        user_id: str, 
        chat_history: Optional[List[Message]] = None
    ) -> Dict[str, Any]:
        """Analyzes message using LLM and maps result to ConversationAction."""
        print(f"ConversationService: Analyzing message: '{user_message_content[:50]}...'")
        
        llm_analysis = await self._analyze_intent_with_llm(user_message_content, chat_history)
        intent = llm_analysis.get("intent")

        if intent == "CREATE_TASK":
            source_type_str = llm_analysis.get("source_type", "TEXT").upper()
            # Map LLM string output to Enum
            try:
                source_type = InputSourceType[source_type_str]
            except KeyError:
                 print(f"ConversationService: LLM returned invalid source_type: {source_type_str}. Defaulting to TEXT.")
                 source_type = InputSourceType.TEXT

            input_data = llm_analysis.get("input_data")
            if not input_data:
                 # Handle case where LLM decided CREATE_TASK but didn't extract data
                 print("ConversationService: CREATE_TASK intent but no input_data from LLM. Asking clarification.")
                 return {
                     "action": ConversationAction.ASK_CLARIFICATION,
                     "response_content": "Okay, I think you want me to start a task, but could you please provide the specific details or link again?",
                     "task_details": None
                 }

            return {
                "action": ConversationAction.CREATE_AND_START_TASK,
                "response_content": f"Okay, I'll start working on the task from {source_type.value}: {str(input_data)[:50]}...",
                "task_details": {
                    "input_source_type": source_type.value, # Pass the enum value
                    "input_data": input_data
                }
            }
        elif intent == "ASK_CLARIFICATION":
             clarification = llm_analysis.get("clarification_needed", "Could you please provide more details?")
             return {
                 "action": ConversationAction.ASK_CLARIFICATION,
                 "response_content": clarification,
                 "task_details": None
             }
        elif intent == "CHAT":
             # Extract the chat response generated by the LLM
             chat_response = llm_analysis.get("chat_response", "Got it.") # Default if missing
             return {
                 "action": ConversationAction.SAVE_MESSAGE_ONLY,
                 "response_content": chat_response, # Pass the chat response back
                 "task_details": None
             }
        else: # Handle ERROR case from LLM analysis
             print(f"ConversationService: Error during LLM analysis: {llm_analysis.get('error_message')}")
             return {
                 "action": ConversationAction.ERROR,
                 "response_content": llm_analysis.get('error_message', "Sorry, I encountered an error trying to understand that."),
                 "task_details": None
             } 