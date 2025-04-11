from typing import List, Optional, Dict, Any, TYPE_CHECKING
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

    async def send_message_to_chat(self, chat_session: Any, message: str) -> Optional[str]:
        """Sends a message to an existing Google AI chat session and gets the response."""
        if not chat_session:
             print("LlmService Error: No chat session provided.")
             return None
        try:
            # Use async sending if available and preferred, otherwise sync
            # response = await chat_session.send_message_async(message)
            # Sticking to sync send_message for now as shown in basic docs
            response = chat_session.send_message(message)
            print(f"LlmService: Received response: {response.text[:100]}...")
            return response.text.strip() if response.text else None
        except Exception as e:
            print(f"LlmService Error sending message to chat session: {e}")
            # Consider more specific error handling (e.g., API errors)
            return None

    # Remove get_chat_completion and format_messages_for_llm 