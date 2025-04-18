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
from app.features.jonas.services import JonasService

# Repository provider imports from this directory
from .repositories import (
    get_user_repository, 
    get_chat_repository, 
    get_websocket_repository,
    UserRepository, 
    ChatRepository,
    WebSocketRepository,
    get_screenshot_repository,
    ScreenshotRepository
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
    websocket_repository: Annotated[WebSocketRepository, Depends(get_websocket_repository)],
    screenshot_repository: Annotated[ScreenshotRepository, Depends(get_screenshot_repository)]  
) -> ChatService:
    return ChatService(chat_repository=chat_repo, websocket_repository=websocket_repository, screenshot_repository=screenshot_repository)

# Provider for WebSocketService (using renamed repo provider)
def get_websocket_service(
    websocket_repository: Annotated[WebSocketRepository, Depends(get_websocket_repository)]
) -> WebSocketService:
    return WebSocketService(websocket_repository=websocket_repository)


def get_jonas_service(
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    websocket_service: Annotated[WebSocketService, Depends(get_websocket_service)],
    chat_repository: Annotated[ChatRepository, Depends(get_chat_repository)]
) -> JonasService:
    return JonasService(
        chat_service=chat_service,
        websocket_service=websocket_service,
        chat_repository=chat_repository
    )
