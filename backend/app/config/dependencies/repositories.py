from app.features.user.repositories import UserRepository
from app.features.chat.repositories import ChatRepository, ConnectionRepository

def get_user_repository() -> UserRepository:
    return UserRepository()

def get_chat_repository() -> ChatRepository:
    return ChatRepository()

def get_connection_repository() -> ConnectionRepository:
    return ConnectionRepository()