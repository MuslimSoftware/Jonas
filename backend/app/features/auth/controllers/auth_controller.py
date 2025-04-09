from fastapi import APIRouter
from starlette.requests import Request
from app.config.rate_limit import limiter
from app.features.auth.schemas import (
    CheckEmailRequest,
    CheckEmailResponse,
    RequestOTPRequest,
    RequestOTPResponse,
    ValidateOTPRequest,
    ValidateOTPResponse,
    AuthRequest,
    AuthResponse,
    RefreshTokenRequest,
    RefreshTokenResponse
)
from app.features.common.schemas import ServiceResult
from app.config.dependencies import AuthServiceDep

prefix = "/auth"
tags = ["Authentication"]

router = APIRouter(
    prefix=prefix,
    tags=tags
)

@router.post("/check-email", response_model=CheckEmailResponse)
async def check_email_availability(
    request: CheckEmailRequest,
    auth_service: AuthServiceDep
) -> CheckEmailResponse:
    """Check if email exists and get verification token."""
    result = await auth_service.check_email_availability(request.email)

    return CheckEmailResponse(
        success=result.success,
        message=result.message,
        data={"exists": result.data["exists"]}
    )

@router.post("/request-otp", response_model=RequestOTPResponse)
@limiter.limit("5/minute")
async def request_otp(
    body: RequestOTPRequest,
    auth_service: AuthServiceDep,
    request: Request
) -> RequestOTPResponse:
    """Request OTP using verification token."""
    result: ServiceResult = await auth_service.request_otp(body.email)
    
    return RequestOTPResponse(
        success=result.success,
        message=result.message,
        data={"expires_in": result.data["expires_in"]}
    )

@router.post("/validate-otp", response_model=ValidateOTPResponse)
@limiter.limit("5/minute")
async def validate_otp(
    body: ValidateOTPRequest,
    auth_service: AuthServiceDep,
    request: Request
) -> ValidateOTPResponse:
    """Validate OTP and get completion token."""
    result = await auth_service.validate_otp(
        body.email,
        body.otp
    )
    
    return ValidateOTPResponse(
        success=result.success,
        message=result.message,
        data={"token": result.data["token"]}
    )

@router.post("/auth", response_model=AuthResponse)
async def auth(
    request: AuthRequest,
    auth_service: AuthServiceDep
) -> AuthResponse:
    """Verify token and either login or signup"""
    # Use auth_service to handle the entire authentication flow
    result: ServiceResult = await auth_service.authenticate_with_token(request.token)
    
    return AuthResponse(
        success=result.success,
        message=result.message,
        data={
            "access_token": result.data["access_token"] if "access_token" in result.data else None,
            "refresh_token": result.data["refresh_token"] if "refresh_token" in result.data else None,
        }
    )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthServiceDep
) -> RefreshTokenResponse:
    """Refresh access token using refresh token."""
    result: ServiceResult = await auth_service.refresh_token(request.refresh_token)

    return RefreshTokenResponse(
        success=result.success,
        message=result.message,
        data={"access_token": result.data["access_token"]}
    )