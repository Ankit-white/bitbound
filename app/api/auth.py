from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.services.auth_service import (
    AuthService,
    AuthServiceError,
    InvalidCredentialsError,
    EmailNotVerifiedError,
    UserNotFoundError,
    InvalidOTPError,
    OTPBlockedError
)
from app.services.email_service import EmailService
from app.auth.dependencies import get_current_user, get_auth_service, get_email_service
from app.core.config import settings
from app.models.user import User
from app.models.otp import OTPType


router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class VerifyEmailRequest(BaseModel):
    user_id: Optional[UUID] = None
    email: Optional[EmailStr] = None
    otp_code: str


class ResendVerificationOTPRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    user_id: UUID
    otp_code: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class RegisterResponse(MessageResponse):
    user_id: UUID
    debug_otp: Optional[str] = None


class ResendVerificationOTPResponse(MessageResponse):
    debug_otp: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    is_active: bool
    email_verified: bool

    class Config:
        from_attributes = True


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
):
    try:
        user = auth_service.register(
            name=request.name,
            email=request.email,
            password=request.password
        )
        
        otp_code = auth_service.send_otp(user.id, OTPType.EMAIL_VERIFICATION)
        if settings.AUTH_DEBUG_OTP_IN_RESPONSE:
            return RegisterResponse(
                message="User registered in debug OTP mode. Use debug_otp to verify this local account.",
                user_id=user.id,
                debug_otp=otp_code
            )

        try:
            await email_service.send_verification_otp(request.email, otp_code)
        except Exception:
            auth_service.delete_user(user.id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "message": "Verification OTP email could not be sent. Check SMTP credentials and try registering again."
                }
            )

        return RegisterResponse(
            message="User registered successfully. Please check your email for verification OTP.",
            user_id=user.id
        )
    except AuthServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=LoginResponse
)
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None
):
    try:
        access_token, refresh_token, user = auth_service.login(
            email=request.email,
            password=request.password,
            device_info=device_info,
            ip_address=ip_address
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "email_verified": getattr(user, "email_verified", True)
            }
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except EmailNotVerifiedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except AuthServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/resend-verification-otp",
    response_model=ResendVerificationOTPResponse
)
async def resend_verification_otp(
    request: ResendVerificationOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
):
    try:
        user = auth_service.get_user_by_email(request.email)
        if not user:
            raise UserNotFoundError("User not found")

        if user.email_verified:
            return MessageResponse(message="Email is already verified.")

        otp_code = auth_service.send_otp(user.id, OTPType.EMAIL_VERIFICATION)
        if settings.AUTH_DEBUG_OTP_IN_RESPONSE:
            return ResendVerificationOTPResponse(
                message="Verification OTP generated in debug OTP mode.",
                debug_otp=otp_code
            )

        try:
            await email_service.send_verification_otp(request.email, otp_code)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Verification OTP email could not be sent. Check SMTP credentials and try again."
            )

        return ResendVerificationOTPResponse(message="Verification OTP sent successfully.")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/verify-email",
    response_model=MessageResponse
)
def verify_email(
    request: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        user_id = request.user_id
        if not user_id and request.email:
            user = auth_service.get_user_by_email(request.email)
            if not user:
                raise UserNotFoundError("User not found")
            user_id = user.id

        if not user_id:
            raise UserNotFoundError("User ID or email is required")

        auth_service.verify_email(
            user_id=user_id,
            otp_code=request.otp_code
        )
        
        return MessageResponse(message="Email verified successfully. You can now log in.")
    except (InvalidOTPError, OTPBlockedError, UserNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/forgot-password",
    response_model=MessageResponse
)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
):
    user = auth_service.get_user_by_email(request.email)
    if not user:
        return MessageResponse(message="If your email is registered, you will receive a password reset OTP.")
    
    try:
        otp_code = auth_service.send_otp(user.id, OTPType.PASSWORD_RESET)
        
        await email_service.send_password_reset_otp(request.email, otp_code)
        
        return MessageResponse(message="If your email is registered, you will receive a password reset OTP.")
    except AuthServiceError:
        return MessageResponse(message="If your email is registered, you will receive a password reset OTP.")


@router.post(
    "/reset-password",
    response_model=MessageResponse
)
def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        auth_service.reset_password(
            user_id=request.user_id,
            otp_code=request.otp_code,
            new_password=request.new_password
        )
        
        return MessageResponse(message="Password reset successfully. You can now log in with your new password.")
    except (InvalidOTPError, OTPBlockedError, UserNotFoundError, AuthServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/refresh-token",
    response_model=RefreshTokenResponse
)
def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        new_access_token = auth_service.refresh_access_token(request.refresh_token)
        
        return RefreshTokenResponse(access_token=new_access_token)
    except AuthServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(
    "/logout",
    response_model=MessageResponse
)
def logout(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        auth_service.logout(request.refresh_token)
        
        return MessageResponse(message="Logged out successfully.")
    except AuthServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        email_verified=getattr(current_user, "email_verified", True)
    )
