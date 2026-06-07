from typing import TYPE_CHECKING, Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.wallet import Wallet


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(BaseModel):
    __tablename__ = "payments"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    wallet_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR"
    )

    credits: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="razorpay"
    )

    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    provider_order_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    provider_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    status: Mapped[PaymentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PaymentStatus.PENDING
    )

    failure_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="payments"
    )

    wallet: Mapped["Wallet"] = relationship(
        "Wallet",
        back_populates="payments"
    )

    __table_args__ = (
        Index("idx_payments_user", "user_id"),
        Index("idx_payments_wallet", "wallet_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_provider_order", "provider_order_id"),
        Index("idx_payments_provider_payment", "provider_payment_id"),
        Index("idx_payments_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, wallet_id={self.wallet_id}, amount={self.amount}, currency={self.currency}, credits={self.credits}, status={self.status})>"