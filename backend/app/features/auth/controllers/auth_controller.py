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
    AuthResponse
)
from app.features.common.schemas import ServiceResult
from app.config.dependencies import AuthServiceDep, OTPServiceDep
from app.utils.cache_utils import manual_cache
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
    body: AuthRequest,
    auth_service: AuthServiceDep,
    request: Request,
) -> AuthResponse:
    """Verify token and either login or signup"""
    # Use auth_service to handle the entire authentication flow
    result: ServiceResult = await auth_service.authenticate_with_token(body.token)
    
    return AuthResponse(
        success=result.success,
        message=result.message,
        data={
            "access_token": result.data["access_token"] if "access_token" in result.data else None,
            "refresh_token": result.data["refresh_token"] if "refresh_token" in result.data else None,
        }
    )