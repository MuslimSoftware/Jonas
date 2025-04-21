from typing import Annotated
from app.features.user.models.user_model import User
from fastapi import Depends

# Service Imports
from app.features.user.services import UserService
from app.features.auth.services import AuthService
from app.features.auth.services import JWTService
from app.features.common.services import OTPService
from app.features.chat.services import ChatService, WebSocketService, ContextService
from app.features.jonas.services import JonasService

# Repository Imports
from app.features.user.repositories import UserRepository
from app.features.chat.repositories import ChatRepository, WebSocketRepository, ScreenshotRepository, ContextRepository

# Provider Imports
from .services import (
    get_user_service,
    get_auth_service,
    get_jwt_service,
    get_otp_service,
    get_chat_service,
    get_websocket_service,
    get_jonas_service,
    get_screenshot_repository,
    get_context_service,
)
from .repositories import (
    get_user_repository,
    get_chat_repository,
    get_websocket_repository,
    get_screenshot_repository,
    get_context_repository,
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
WebSocketServiceDep = Annotated[WebSocketService, Depends(get_websocket_service)]
JonasServiceDep = Annotated[JonasService, Depends(get_jonas_service)]
# Context Service Dep
ContextServiceDep = Annotated[ContextService, Depends(get_context_service)]
# Repositories
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
ChatRepositoryDep = Annotated[ChatRepository, Depends(get_chat_repository)]
ScreenshotRepositoryDep = Annotated[ScreenshotRepository, Depends(get_screenshot_repository)]
WebSocketRepositoryDep = Annotated[WebSocketRepository, Depends(get_websocket_repository)]
# Context Repository Dep
ContextRepositoryDep = Annotated[ContextRepository, Depends(get_context_repository)]
# Current User (for WebSockets)
CurrentUserWsDep = Annotated[User, Depends(get_current_user_ws)]
