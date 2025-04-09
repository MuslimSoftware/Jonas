from typing import Annotated
from app.features.user.models.user_model import User
from fastapi import Depends

# Service Imports
from app.features.user.services import UserService
from app.features.auth.services import AuthService
from app.features.auth.services import JWTService
from app.features.common.services import OTPService
from app.features.chat.services import ChatService

# Repository Imports
from app.features.user.repositories import UserRepository
from app.features.chat.repositories import ChatRepository, ConnectionRepository

# Provider Imports
from .services import (
    get_current_active_user,
    get_user_service,
    get_auth_service,
    get_jwt_service,
    get_otp_service,
    get_chat_service
)
from .repositories import (
    get_user_repository,
    get_chat_repository,
    get_connection_repository
)

# Services
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
JWTServiceDep = Annotated[JWTService, Depends(get_jwt_service)]
OTPServiceDep = Annotated[OTPService, Depends(get_otp_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
UserDep = Annotated[User, Depends(get_current_active_user)]

# Repositories
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
ChatRepositoryDep = Annotated[ChatRepository, Depends(get_chat_repository)]
ConnectionRepositoryDep = Annotated[ConnectionRepository, Depends(get_connection_repository)]
