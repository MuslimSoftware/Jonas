from typing import Annotated
from fastapi import Depends
from app.features.user.repositories import UserRepository
from app.features.chat.repositories import ChatRepository, WebSocketRepository, ScreenshotRepository
from app.features.chat.repositories import ContextRepository
from app.features.agent.repositories import ADKRepository
from app.features.chat.services import ContextService

def get_user_repository() -> UserRepository:
    return UserRepository()

def get_chat_repository() -> ChatRepository:
    return ChatRepository()

def get_screenshot_repository() -> ScreenshotRepository:
    return ScreenshotRepository()

def get_websocket_repository() -> WebSocketRepository:
    return WebSocketRepository()

def get_context_repository() -> ContextRepository:
    return ContextRepository()

def get_adk_repository(
    chat_repository: Annotated[ChatRepository, Depends(get_chat_repository)]
) -> ADKRepository:
    return ADKRepository(chat_repository=chat_repository)
