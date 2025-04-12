from typing import List, Optional, Dict, Any, TYPE_CHECKING, AsyncIterator
from google import genai
from google.genai import types

if TYPE_CHECKING:
    from ..repositories import LlmRepository
    from app.features.chat.models import Message

class LlmService:
    """Service layer for managing Google AI chat sessions."""

    def __init__(self, llm_repository: "LlmRepository"):
        self.llm_repository = llm_repository
        self._client: genai.Client = self.llm_repository.get_client()
        self._model_name: str = self.llm_repository.get_model_name()
        print("LlmService Initialized")

    def _format_history_for_google(self, messages: List["Message"]) -> List[types.ContentDict]:
        """Formats DB Message list to Google GenAI history format (list of ContentDict)."""
        formatted_history: List[types.ContentDict] = []
        for msg in messages:
            # Map sender_type to Google's roles ('user' or 'model')
            role = 'model' if msg.sender_type == 'agent' else 'user'
            # Ensure content is not None or empty, though history usually has content
            content = msg.content if msg.content is not None else ""
            # Ensure parts contains a dictionary with a 'text' key
            formatted_history.append({'role': role, 'parts': [{'text': content}]})
        return formatted_history

    def create_chat_session(self, history_messages: List["Message"] = []) -> Any:
        """Creates a new Google AI chat session, optionally loading history."""
        formatted_history = self._format_history_for_google(history_messages)
        print(f"LlmService: Creating new chat session with model {self._model_name} and {len(formatted_history)} history messages.")
        # Use history parameter in create call
        return self._client.chats.create(model=self._model_name, history=formatted_history)

    async def send_message_to_chat_stream(self, chat_session: Any, message: str) -> AsyncIterator[str]:
        """Sends a message to a Google AI chat session and yields response chunks."""
        if not chat_session:
             print("LlmService Error: No chat session provided.")
             # Need to yield something or raise to signal error? Empty iterator for now.
             # Proper async generators might require different error handling.
             yield "[Error: No chat session]"
             return # Stop the generator
        
        try:
            print(f"LlmService: Sending stream message: {message[:50]}...")
            # Use the correct method: send_message_stream
            response_stream = chat_session.send_message_stream(message)
            
            # Iterate through the stream (use synchronous for loop)
            for chunk in response_stream:
                if chunk.text:
                    # print(f"LlmService: Yielding chunk: {chunk.text[:30]}...") # Debug
                    yield chunk.text
                else:
                    # Handle potential empty chunks or other parts if necessary
                    print(f"LlmService: Received non-text chunk or empty text: {chunk}")
                    
        except Exception as e:
            error_message = f"[Error streaming response: {e}]"
            print(f"LlmService Error sending/streaming message to chat session: {e}")
            yield error_message # Yield an error message chunk

    # Remove get_chat_completion and format_messages_for_llm 