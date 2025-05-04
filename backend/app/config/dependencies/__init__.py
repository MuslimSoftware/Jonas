from typing import Annotated
from fastapi import Depends

# --- Import Actual Classes --- #
# Models
from app.features.user.models import User
# Services
from app.features.user.services import UserService
from app.features.auth.services import AuthService, JWTService
from app.features.common.services import OTPService
from app.features.chat.services import ChatService, WebSocketService, ContextService
from app.features.agent.services import AgentService, ADKService
# Repositories
from app.features.user.repositories import UserRepository
from app.features.chat.repositories import ChatRepository, WebSocketRepository, ScreenshotRepository, ContextRepository
from app.features.agent.repositories import ADKRepository

# --- Import Provider Functions --- #
from .common import get_redis
from .repositories import (
    get_user_repository,
    get_chat_repository,
    get_websocket_repository,
    get_screenshot_repository,
    get_context_repository,
    get_adk_repository,
)
from .services import (
    get_user_service,
    get_jwt_service,
    get_otp_service,
    get_auth_service,
    get_chat_service,
    get_websocket_service,
    get_context_service,
    get_agent_service,
    get_adk_service,
)
from .auth import get_current_user, get_current_user_ws

# --- Define Annotated Dependency Types --- #
# Services
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
JWTServiceDep = Annotated[JWTService, Depends(get_jwt_service)]
OTPServiceDep = Annotated[OTPService, Depends(get_otp_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
WebSocketServiceDep = Annotated[WebSocketService, Depends(get_websocket_service)]
ContextServiceDep = Annotated[ContextService, Depends(get_context_service)]
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
ADKServiceDep = Annotated[ADKService, Depends(get_adk_service)]

# Repositories
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
ChatRepositoryDep = Annotated[ChatRepository, Depends(get_chat_repository)]
WebSocketRepositoryDep = Annotated[WebSocketRepository, Depends(get_websocket_repository)]
ScreenshotRepositoryDep = Annotated[ScreenshotRepository, Depends(get_screenshot_repository)]
ContextRepositoryDep = Annotated[ContextRepository, Depends(get_context_repository)]
ADKRepositoryDep = Annotated[ADKRepository, Depends(get_adk_repository)]

# User Objects
UserDep = Annotated[User, Depends(get_current_user)]
CurrentUserWsDep = Annotated[User, Depends(get_current_user_ws)]


# --- Exports --- #
__all__ = [
    # Common Providers
    "get_redis",

    # Repository Providers (Export if needed directly elsewhere, otherwise maybe not)
    # "get_user_repository",
    # "get_chat_repository",
    # "get_websocket_repository",
    # "get_screenshot_repository",
    # "get_context_repository",
    # "get_adk_repository",

    # Service Providers (Export if needed directly elsewhere, otherwise maybe not)
    # "get_user_service",
    # "get_jwt_service",
    # "get_otp_service",
    # "get_auth_service",
    # "get_chat_service",
    # "get_websocket_service",
    # "get_jonas_service",
    # "get_context_service",
    # "get_agent_service",
    # "get_adk_service",

    # Auth Providers (These ARE likely needed externally)
    "get_current_user",
    "get_current_user_ws",

    # Annotated Service Types (These ARE needed externally)
    "AuthServiceDep",
    "UserServiceDep",
    "JWTServiceDep",
    "OTPServiceDep",
    "ChatServiceDep",
    "WebSocketServiceDep",
    "ContextServiceDep",
    "AgentServiceDep",
    "ADKServiceDep",

    # Annotated Repository Types (These ARE needed externally)
    "UserRepositoryDep",
    "ChatRepositoryDep",
    "WebSocketRepositoryDep",
    "ScreenshotRepositoryDep",
    "ContextRepositoryDep",
    "ADKRepositoryDep",

    # Annotated User Types (These ARE needed externally)
    "UserDep",
    "CurrentUserWsDep",
] 