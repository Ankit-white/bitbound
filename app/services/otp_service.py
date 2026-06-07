from datetime import datetime, timedelta, timezone
import secrets
import string
from uuid import UUID

from app.models.otp import OTPType
from app.repositories.otp_repository import OTPRepository
from app.repositories.user_repository import UserRepository


class UserNotFoundError(Exception):
    pass


class InvalidOTPError(Exception):
    pass


class OTPBlockedError(Exception):
    pass


class OTPService:
    def __init__(
        self,
        user_repository: UserRepository,
        otp_repository: OTPRepository
    ):
        self.user_repository = user_repository
        self.otp_repository = otp_repository

    def _generate_otp_code(self, length: int = 8) -> str:
        if length < 4:
            raise ValueError("OTP length must be at least 4 characters")

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        required_chars = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        remaining_chars = [
            secrets.choice(alphabet)
            for _ in range(length - len(required_chars))
        ]
        chars = required_chars + remaining_chars
        secrets.SystemRandom().shuffle(chars)

        return "".join(chars)

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

        self.otp_repository.create_otp(
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
