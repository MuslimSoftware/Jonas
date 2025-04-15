from typing import Annotated
from fastapi import Depends
from app.features.user.repositories import UserRepository
from app.features.chat.repositories import ChatRepository, WebSocketRepository, ScreenshotRepository
from app.features.llm.repositories import LlmRepository
from app.features.agent.repositories import BrowserAgentRepository
from app.features.jonas.repositories import JonasRepository

def get_user_repository() -> UserRepository:
    return UserRepository()

def get_chat_repository() -> ChatRepository:
    return ChatRepository()

def get_screenshot_repository() -> ScreenshotRepository:
    return ScreenshotRepository()

def get_websocket_repository() -> WebSocketRepository:
    return WebSocketRepository()

def get_llm_repository() -> LlmRepository:
    return LlmRepository()

def get_browser_agent_repository(screenshot_repo: Annotated[ScreenshotRepository, Depends(get_screenshot_repository)]) -> BrowserAgentRepository:
    return BrowserAgentRepository(screenshot_repository=screenshot_repo)

def get_jonas_repository() -> JonasRepository:
    return JonasRepository()