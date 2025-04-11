from typing import Annotated
from fastapi import Depends
from app.config.redis_config import get_redis_client

# Service imports
from app.features.user.services import UserService
from app.features.auth.services import AuthService
from app.features.auth.services import JWTService
from app.features.common.services import OTPService
# Import ChatService
from app.features.chat.services import ChatService, WebSocketService
from app.features.agent.services import TaskService, ConversationService
from app.features.agent.repositories import TaskRepository
from app.features.llm.services import LlmService # Import LlmService
from app.features.llm.repositories import LlmRepository # Import LlmRepository

# Repository provider imports from this directory
from .repositories import (
    get_user_repository, 
    get_chat_repository, 
    get_websocket_repository,
    UserRepository, 
    ChatRepository,
    WebSocketRepository,
    get_task_repository,
    TaskRepository,
    get_llm_repository, # Add llm repo provider
    LlmRepository # Add llm repo class
)

def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(user_repository=user_repository)

def get_jwt_service() -> JWTService:
    return JWTService()

async def get_otp_service() -> OTPService:
    redis_client = await get_redis_client()
    return OTPService(redis_client=redis_client)

def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    otp_service: Annotated[OTPService, Depends(get_otp_service)]
) -> AuthService:
    return AuthService(user_repository, jwt_service, otp_service)

# Provider for ChatService (using auto-Depends for its internal repo dependency)
def get_chat_service(
    chat_repo: Annotated[ChatRepository, Depends(get_chat_repository)], 
    websocket_repository: Annotated[WebSocketRepository, Depends(get_websocket_repository)]
) -> ChatService:
    return ChatService(chat_repository=chat_repo, websocket_repository=websocket_repository)

# Provider for WebSocketService (using renamed repo provider)
def get_websocket_service(
    websocket_repository: Annotated[WebSocketRepository, Depends(get_websocket_repository)]
) -> WebSocketService:
    return WebSocketService(websocket_repository=websocket_repository)

# Provider for TaskService (previously AgentOrchestrator)
def get_task_service(
    task_repo: Annotated[TaskRepository, Depends(get_task_repository)],
    websocket_service: Annotated[WebSocketService, Depends(get_websocket_service)]
) -> TaskService:
    # TODO: Inject other necessary modules/services as they are created
    return TaskService(task_repository=task_repo, websocket_service=websocket_service)

# Provider for LlmService
def get_llm_service(
    llm_repo: Annotated[LlmRepository, Depends(get_llm_repository)] # Inject LlmRepository
) -> LlmService:
    return LlmService(llm_repository=llm_repo)

# Provider for ConversationService
def get_conversation_service(
    task_repo: Annotated[TaskRepository, Depends(get_task_repository)],
    llm_service: Annotated[LlmService, Depends(get_llm_service)] # Inject LlmService
) -> ConversationService:
    # Pass LlmService to ConversationService constructor
    return ConversationService(llm_service=llm_service)

