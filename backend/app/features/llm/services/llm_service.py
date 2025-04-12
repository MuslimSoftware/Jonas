from typing import List, TYPE_CHECKING, AsyncIterator
from google import genai
from google.genai import types

if TYPE_CHECKING:
    from ..repositories import LlmRepository
    from app.features.chat.models import Message

class LlmService:
    """Service layer for stateless interaction with Google AI, including history."""

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

    async def generate_response_stream(
        self, 
        history_messages: List["Message"], 
        current_message: str
    ) -> AsyncIterator[str]:
        """Creates a temporary chat session with history, sends the current message, 
           and yields response chunks.
        """
        if not current_message:
             print("LlmService Error: No current message provided.")
             yield "[Error: Invalid input]"
             return
        
        try:
            # Format the history
            formatted_history = self._format_history_for_google(history_messages)
            print(f"LlmService: Creating temp chat with {len(formatted_history)} history messages.")
            
            # Create a temporary, internal chat session just for this request
            temp_chat_session = self._client.chats.create(
                model=self._model_name, 
                history=formatted_history
            )
            
            print(f"LlmService: Sending message to temp chat: {current_message[:50]}...")
            # Use send_message_stream on the temporary session
            response_stream = temp_chat_session.send_message_stream(current_message)
            
            # Stream the response chunks (synchronous iteration)
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                else:
                    print(f"LlmService: Received non-text chunk or empty text: {chunk}")
                    
        except Exception as e:
            error_message = f"[Error generating response: {e}]"
            print(f"LlmService Error during temporary chat/stream: {e}")
            yield error_message # Yield an error message chunk

    # Remove old send_message_to_chat_stream if fully replaced 