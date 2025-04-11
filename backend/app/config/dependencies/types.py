from typing import Annotated
from app.features.user.models.user_model import User
from fastapi import Depends

# Service Imports
from app.features.user.services import UserService
from app.features.auth.services import AuthService
from app.features.auth.services import JWTService
from app.features.common.services import OTPService
from app.features.chat.services import ChatService, WebSocketService
from app.features.agent.services import TaskService
from app.features.llm.services import LlmService

# Repository Imports
from app.features.user.repositories import UserRepository
from app.features.chat.repositories import ChatRepository, WebSocketRepository
from app.features.agent.repositories import TaskRepository
from app.features.llm.repositories import LlmRepository

# Provider Imports
from .services import (
    get_user_service,
    get_auth_service,
    get_jwt_service,
    get_otp_service,
    get_chat_service,
    get_task_service,
    get_websocket_service,
    get_llm_service,
)
from .repositories import (
    get_user_repository,
    get_chat_repository,
    get_websocket_repository,
    get_task_repository,
    get_llm_repository,
)
from .auth import (
    get_current_user_ws,
    get_current_user
)

# Services
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
JWTServiceDep = Annotated[JWTService, Depends(get_jwt_service)]
OTPServiceDep = Annotated[OTPService, Depends(get_otp_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
UserDep = Annotated[User, Depends(get_current_user)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
WebSocketServiceDep = Annotated[WebSocketService, Depends(get_websocket_service)]
LlmServiceDep = Annotated[LlmService, Depends(get_llm_service)]

# Repositories
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
ChatRepositoryDep = Annotated[ChatRepository, Depends(get_chat_repository)]
WebSocketRepositoryDep = Annotated[WebSocketRepository, Depends(get_websocket_repository)]
TaskRepositoryDep = Annotated[TaskRepository, Depends(get_task_repository)]
LlmRepositoryDep = Annotated[LlmRepository, Depends(get_llm_repository)]

# Current User (for WebSockets)
CurrentUserWsDep = Annotated[User, Depends(get_current_user_ws)]
