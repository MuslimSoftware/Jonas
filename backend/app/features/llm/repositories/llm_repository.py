from typing import List, Optional, Dict, Any
# from openai import AsyncOpenAI
from app.config.env import settings
import json

class LlmRepository:
    """Repository layer for direct interaction with LLM APIs (e.g., OpenAI)."""

    def __init__(self):
        # Initialize the client upon repository instantiation
        # self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        print("LlmRepository initialized with OpenAI client.")

    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.2,
        max_tokens: int = 150
    ) -> Optional[str]:
        """Calls the configured LLM provider's Chat Completion API."""
        try:
            # Simulate a response indicating simple chat intent
            intent = "CHAT"
            source_type = None
            input_data = None
            clarification = None
            chat_response = "Okay, I understand you sent 'test' (simulated)."
            
            # Use json.dumps for reliable JSON formatting
            response_dict = {
                "intent": intent,
                "source_type": source_type,
                "input_data": input_data,
                "clarification_needed": clarification,
                "chat_response": chat_response
            }
            response_json_str = json.dumps(response_dict)
            
            print(f"LlmRepository: Returning simulated CHAT intent response: {response_json_str}")
            return response_json_str
            
            # --- Original OpenAI Call (Commented Out) ---
            # response = await self.client.chat.completions.create(
            #     model=model,
            #     messages=messages,
            #     temperature=temperature,
            #     max_tokens=max_tokens,
            # )
            # if response.choices and len(response.choices) > 0:
            #     if response.choices[0].message:
            #         if response.choices[0].message.content is not None:
            #             return response.choices[0].message.content.strip()
            # print("LlmRepository: API call failed: OpenAI response missing expected content.")
            # return None
            # --- End Original OpenAI Call ---
        except Exception as e:
            print(f"LlmRepository: Error during simulation/call: {e}")
            return None 