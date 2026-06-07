from typing import TYPE_CHECKING, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    token: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    device_info: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="refresh_tokens"
    )

    __table_args__ = (
        Index("idx_refresh_tokens_user", "user_id"),
        Index("idx_refresh_tokens_token", "token"),
        Index("idx_refresh_tokens_expires", "expires_at"),
        Index("idx_refresh_tokens_revoked", "is_revoked"),
        Index("idx_refresh_tokens_user_revoked", "user_id", "is_revoked"),
        Index("idx_refresh_tokens_active", "is_revoked", "expires_at"),
    )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_expired and not self.is_revoked

    def revoke(self) -> None:
        self.is_revoked = True

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, is_revoked={self.is_revoked})>"