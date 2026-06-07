from typing import TYPE_CHECKING, Optional
from uuid import UUID
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Index, Enum as SQLAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class OTPType(str, Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class OTP(BaseModel):
    __tablename__ = "otps"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    otp_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    otp_type: Mapped[OTPType] = mapped_column(
        SQLAEnum(OTPType),
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    is_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="otps"
    )

    __table_args__ = (
        Index("idx_otps_user", "user_id"),
        Index("idx_otps_code", "otp_code"),
        Index("idx_otps_type", "otp_type"),
        Index("idx_otps_expires", "expires_at"),
        Index("idx_otps_used", "is_used"),
        Index("idx_otps_user_type", "user_id", "otp_type"),
    )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_expired and not self.is_used

    def mark_used(self) -> None:
        self.is_used = True

    def increment_attempts(self) -> None:
        self.attempts += 1

    def __repr__(self) -> str:
        return f"<OTP(id={self.id}, user_id={self.user_id}, otp_type={self.otp_type}, is_used={self.is_used})>"