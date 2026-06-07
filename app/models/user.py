from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.api_key import APIKey
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agents import Agent
    from app.models.payment import Payment
    from app.models.otp import OTP
    from app.models.refresh_token import RefreshToken


class User(BaseModel):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="developer"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    otps: Mapped[list["OTP"]] = relationship(
        "OTP",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
    "APIKey",
    back_populates="user",
    cascade="all, delete-orphan",
    lazy="selectin"
    )

    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
        Index("idx_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
