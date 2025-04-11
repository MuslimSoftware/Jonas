from typing import List, Optional, Dict, Any
# from openai import AsyncOpenAI
from app.config.env import settings
from google import genai


class LlmRepository:
    """Repository layer for direct interaction with Google AI APIs."""

    def __init__(self):
        self.client = genai.Client(api_key=settings.AI_API_KEY)
        self.model_name = settings.AI_MODEL
        print(f"LlmRepository initialized with Google AI client for model: {self.model_name}")

    async def get_chat_completion(
        self,
        message: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """Calls the Google AI API's generate_content method with the last message content."""
        if not message:
            print("LlmRepository: No message provided for completion.")
            return None
            
        try:
            
            # Prepare configuration
            config = genai.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            # Call the API using the client with just the last content
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[message],
                config=config
            )

            print(f"LlmRepository: API call response: {response}")
            
            return response.text
                
        except Exception as e:
            print(f"LlmRepository: Error during Google AI generate_content call: {e}")
            return None 