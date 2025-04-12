from typing import List, Optional, Dict, Any, TYPE_CHECKING, AsyncIterator
from google import genai

if TYPE_CHECKING:
    from ..repositories import LlmRepository

class LlmService:
    """Service layer for managing Google AI chat sessions."""

    def __init__(self, llm_repository: "LlmRepository"):
        self.llm_repository = llm_repository
        self._client: genai.Client = self.llm_repository.get_client()
        self._model_name: str = self.llm_repository.get_model_name()
        print("LlmService Initialized")

    def create_chat_session(self) -> Any:
        """Creates a new Google AI chat session."""
        print(f"LlmService: Creating new chat session with model {self._model_name}")
        # TODO: Add system prompt configuration here if needed
        return self._client.chats.create(model=self._model_name)

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