from typing import TYPE_CHECKING, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.agents import Agent


class APIKey(BaseModel):
    __tablename__ = "api_keys"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    agent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys"
    )

    agent: Mapped[Optional["Agent"]] = relationship(
        "Agent",
        back_populates="api_keys"
    )

    __table_args__ = (
        Index("idx_api_keys_user", "user_id"),
        Index("idx_api_keys_agent", "agent_id"),
        Index("idx_api_keys_hash", "key_hash"),
        Index("idx_api_keys_active", "is_active"),
        Index("idx_api_keys_expires", "expires_at"),
        Index("idx_api_keys_user_active", "user_id", "is_active"),
        Index("idx_api_keys_agent_active", "agent_id", "is_active"),
    )

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired

    def deactivate(self) -> None:
        self.is_active = False

    def mark_used(self) -> None:
        self.last_used_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, prefix={self.prefix}, user_id={self.user_id}, is_active={self.is_active})>"