from typing import Annotated
from app.features.user.models.user_model import User
from fastapi import Depends
from app.config.redis_config import get_redis_client
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status

# Service imports
from app.features.user.services import UserService
from app.features.auth.services import AuthService
from app.features.auth.services import JWTService
from app.features.common.services import OTPService
# Import ChatService
from app.features.chat.services import ChatService 

# Repository provider imports from this directory
from .repositories import (
    get_user_repository, 
    get_chat_repository, 
    UserRepository, 
    ChatRepository,
    ConnectionRepository,
    get_connection_repository
)

# Define OAuth2 scheme here now
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

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
def get_chat_service(chat_repo: Annotated[ChatRepository, Depends(get_chat_repository)], connection_repo: Annotated[ConnectionRepository, Depends(get_connection_repository)]) -> ChatService:
    return ChatService(chat_repository=chat_repo, connection_repository=connection_repo)

async def get_current_active_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> User:
    """FastAPI dependency to get the current authenticated and active user."""
    user = await auth_service._get_user_from_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

