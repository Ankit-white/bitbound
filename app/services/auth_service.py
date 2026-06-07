from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import random
import string

from passlib.context import CryptContext

from app.repositories.user_repository import UserRepository
from app.repositories.otp_repository import OTPRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.jwt_service import JWTService, JWTServiceError
from app.models.user import User
from app.models.otp import OTP, OTPType
from app.models.refresh_token import RefreshToken


class AuthServiceError(Exception):
    """Raised when authentication operations fail."""
    pass


class InvalidCredentialsError(AuthServiceError):
    """Raised when email or password is invalid."""
    pass


class EmailNotVerifiedError(AuthServiceError):
    """Raised when email is not verified."""
    pass


class UserNotFoundError(AuthServiceError):
    """Raised when user does not exist."""
    pass


class InvalidOTPError(AuthServiceError):
    """Raised when OTP is invalid or expired."""
    pass


class OTPBlockedError(AuthServiceError):
    """Raised when OTP has exceeded maximum attempts."""
    pass


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        otp_repository: OTPRepository,
        refresh_token_repository: RefreshTokenRepository,
        jwt_service: JWTService
    ):
        self.user_repository = user_repository
        self.otp_repository = otp_repository
        self.refresh_token_repository = refresh_token_repository
        self.jwt_service = jwt_service
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _generate_otp_code(self, length: int = 6) -> str:
        return ''.join(random.choices(string.digits, k=length))

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise AuthServiceError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            raise AuthServiceError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise AuthServiceError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise AuthServiceError("Password must contain at least one digit")

    def _hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def register(
        self,
        name: str,
        email: str,
        password: str
    ) -> User:
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            raise AuthServiceError(f"User with email {email} already exists")
        
        self._validate_password(password)

        hashed_password = self._hash_password(password)

        user = self.user_repository.create_user(
            name=name,
            email=email,
            password_hash=hashed_password,
            role="developer",
            is_active=False,
            email_verified=False
        )

        return user

    def login(
        self,
        email: str,
        password: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[str, str, User]:
        user = self.user_repository.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        if not self._verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise AuthServiceError("Account is deactivated")
        
        if not user.email_verified:
            raise EmailNotVerifiedError("Email not verified. Please verify your email before logging in.")

        access_token = self.jwt_service.create_access_token(user.id)
        refresh_token = self.jwt_service.create_refresh_token(user.id)
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        self.refresh_token_repository.create_refresh_token(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address
        )

        return access_token, refresh_token, user

    def logout(self, refresh_token: str) -> None:
        try:
            payload = self.jwt_service.verify_refresh_token(refresh_token)
            user_id = UUID(payload["sub"])
            
            token_record = self.refresh_token_repository.get_by_token(refresh_token)
            if token_record and token_record.user_id == user_id:
                token_record.revoke()
                self.refresh_token_repository.update_refresh_token(token_record)
        except JWTServiceError as e:
            raise AuthServiceError(f"Invalid refresh token: {str(e)}")

    def refresh_access_token(self, refresh_token: str) -> str:
        try:
            payload = self.jwt_service.verify_refresh_token(refresh_token)
            user_id = UUID(payload["sub"])
            
            token_record = self.refresh_token_repository.get_by_token(refresh_token)
            if not token_record:
                raise AuthServiceError("Refresh token not found")
            
            if not token_record.is_valid:
                raise AuthServiceError("Refresh token is invalid or expired")
            
            user = self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("User not found")
            
            if not user.is_active:
                raise AuthServiceError("Account is deactivated")
            
            if not user.email_verified:
                raise EmailNotVerifiedError("Email not verified")
            
            new_access_token = self.jwt_service.create_access_token(user_id)
            return new_access_token
        except JWTServiceError as e:
            raise AuthServiceError(f"Invalid refresh token: {str(e)}")

    def send_otp(
        self,
        user_id: UUID,
        otp_type: OTPType
    ) -> str:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        otp_code = self._generate_otp_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        otp = self.otp_repository.create_otp(
            user_id=user_id,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at
        )

        return otp_code

    def verify_otp(
        self,
        user_id: UUID,
        otp_code: str,
        otp_type: OTPType
    ) -> bool:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        otp = self.otp_repository.get_latest_otp(user_id, otp_type)
        
        if not otp:
            raise InvalidOTPError("No OTP found. Please request a new OTP.")
        
        if otp.is_used:
            raise InvalidOTPError("OTP has already been used")
        
        if otp.is_expired:
            raise InvalidOTPError("OTP has expired. Please request a new OTP.")
        
        if otp.attempts >= 5:
            raise OTPBlockedError("OTP has been blocked due to too many failed attempts. Please request a new OTP.")
        
        if otp.otp_code != otp_code:
            otp.increment_attempts()
            self.otp_repository.update_otp(otp)
            
            remaining_attempts = 5 - otp.attempts
            raise InvalidOTPError(f"Invalid OTP code. {remaining_attempts} attempts remaining.")
        
        otp.mark_used()
        self.otp_repository.update_otp(otp)

        return True

    def verify_email(self, user_id: UUID, otp_code: str) -> bool:
        result = self.verify_otp(user_id, otp_code, OTPType.EMAIL_VERIFICATION)
        if result:
            user = self.user_repository.get_by_id(user_id)
            if user:
                user.email_verified = True
                user.is_active = True
                self.user_repository.update_user(user)
        return result

    def reset_password(
        self,
        user_id: UUID,
        otp_code: str,
        new_password: str
    ) -> bool:
        self._validate_password(new_password)
        
        result = self.verify_otp(user_id, otp_code, OTPType.PASSWORD_RESET)
        if result:
            hashed_password = self._hash_password(new_password)
            user = self.user_repository.get_by_id(user_id)
            if user:
                user.password_hash = hashed_password
                self.user_repository.update_user(user)
                
                all_tokens = self.refresh_token_repository.get_by_user(user_id)
                for token in all_tokens:
                    token.revoke()
                    self.refresh_token_repository.update_refresh_token(token)
        return result

    def get_current_user(self, access_token: str) -> User:
        try:
            payload = self.jwt_service.verify_access_token(access_token)
            user_id = UUID(payload["sub"])
            
            user = self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError("User not found")
            
            if not user.is_active:
                raise AuthServiceError("Account is deactivated")
            
            if not user.email_verified:
                raise EmailNotVerifiedError("Email not verified")
            
            return user
        except JWTServiceError as e:
            raise AuthServiceError(f"Invalid token: {str(e)}")

    def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> bool:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        if not self._verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect")
        
        self._validate_password(new_password)

        hashed_password = self._hash_password(new_password)
        user.password_hash = hashed_password
        self.user_repository.update_user(user)
        
        all_tokens = self.refresh_token_repository.get_by_user(user_id)
        for token in all_tokens:
            token.revoke()
            self.refresh_token_repository.update_refresh_token(token)
        
        return True

    def revoke_all_user_sessions(self, user_id: UUID) -> None:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        all_tokens = self.refresh_token_repository.get_by_user(user_id)
        for token in all_tokens:
            token.revoke()
            self.refresh_token_repository.update_refresh_token(token)