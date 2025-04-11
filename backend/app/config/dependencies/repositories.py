from app.features.user.repositories import UserRepository
from app.features.chat.repositories import ChatRepository, WebSocketRepository
from app.features.agent.repositories import TaskRepository
from app.features.llm.repositories import LlmRepository

def get_user_repository() -> UserRepository:
    return UserRepository()

def get_chat_repository() -> ChatRepository:
    return ChatRepository()

def get_websocket_repository() -> WebSocketRepository:
    return WebSocketRepository()

def get_task_repository() -> TaskRepository:
    return TaskRepository()

def get_llm_repository() -> LlmRepository:
    return LlmRepository()