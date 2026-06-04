from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.wallet import Wallet


class Transaction(BaseModel):
    __tablename__ = "transactions"

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

    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="completed"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    wallet: Mapped["Wallet"] = relationship(
        "Wallet",
        back_populates="transactions"
    )

    __table_args__ = (
        Index("idx_transactions_wallet", "wallet_id"),
        Index("idx_transactions_type", "transaction_type"),
        Index("idx_transactions_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, wallet_id={self.wallet_id}, amount={self.amount}, type={self.transaction_type}, status={self.status})>"