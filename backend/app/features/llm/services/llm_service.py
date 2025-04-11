from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..repositories import LlmRepository

class LlmService:
    """Service layer for interacting with LLM APIs via repositories."""

    def __init__(self, llm_repository: "LlmRepository"):
        self.llm_repository = llm_repository
        print("LlmService Initialized")

    async def get_chat_completion(
        self,
        message: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """
        Gets a chat completion response by calling the LlmRepository.
        (No formatting done here anymore)
        """
        if not message:
            print("LlmService: No message provided for completion.")
            return None
            
        response = await self.llm_repository.get_chat_completion(
            message=message, # Pass original messages
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response 