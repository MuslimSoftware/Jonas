from fastapi import Depends, HTTPException, status, WebSocket, WebSocketException, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError
from typing import TYPE_CHECKING

from app.features.user.models import User
from app.features.common.exceptions import AppException

if TYPE_CHECKING:
    from .types import AuthServiceDep
from .services import get_auth_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user( 
    token: str = Depends(oauth2_scheme), 
    auth_service: 'AuthServiceDep' = Depends(get_auth_service)
) -> User:
    """Dependency to get current user from JWT token in HTTP Authorization header."""
    try:
        user = await auth_service._get_user_from_token(token=token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid authentication credentials", 
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- WebSocket Authentication Dependency --- 
async def get_current_user_ws(
    websocket: WebSocket,
    token: str | None = Query(None), # Extract token from query param
    auth_service: 'AuthServiceDep' = Depends(get_auth_service)
) -> User:
    """Dependency to get current user for WebSocket connection using token from query param."""
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
    
    try:
        user = await auth_service._get_user_from_token(token=token)
        if not user or not user.is_active:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return user
    except (JWTError, ValidationError, AppException):
         raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
# --- End WebSocket Authentication Dependency --- 