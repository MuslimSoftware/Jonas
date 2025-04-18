from typing import Annotated
from fastapi import Depends
from app.features.user.repositories import UserRepository
from app.features.chat.repositories import ChatRepository, WebSocketRepository, ScreenshotRepository

def get_user_repository() -> UserRepository:
    return UserRepository()

def get_chat_repository() -> ChatRepository:
    return ChatRepository()

def get_screenshot_repository() -> ScreenshotRepository:
    return ScreenshotRepository()

def get_websocket_repository() -> WebSocketRepository:
    return WebSocketRepository()
