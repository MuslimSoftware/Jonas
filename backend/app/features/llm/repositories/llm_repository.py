from typing import List, Optional, Dict, Any
# from openai import AsyncOpenAI
from app.config.env import settings
from google import genai


class LlmRepository:
    """Repository layer providing access to the configured Google AI client."""

    def __init__(self):
        self.client = genai.Client(api_key=settings.AI_API_KEY)
        self.model_name = settings.AI_MODEL
        print(f"LlmRepository initialized with Google AI client for model: {self.model_name}")

    def get_client(self) -> genai.Client:
        """Returns the initialized genai.Client instance."""
        return self.client

    def get_model_name(self) -> str:
        """Returns the configured model name."""
        return self.model_name