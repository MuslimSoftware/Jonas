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
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.2,
        max_tokens: int = 150
    ) -> Optional[str]:
        """
        Gets a chat completion response by calling the LlmRepository.
        """
        response = await self.llm_repository.get_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response 