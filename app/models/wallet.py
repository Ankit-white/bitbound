from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agents import Agent
    from app.models.transaction import Transaction
    from app.models.payment import Payment
    from app.models.usage import Usage


class Wallet(BaseModel):
    __tablename__ = "wallets"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    balance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    currency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="CREDITS"
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="wallet"
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="wallet",
        cascade="all, delete-orphan"
    )

    usages: Mapped[list["Usage"]] = relationship(
        "Usage",
        back_populates="wallet",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_wallets_balance", "balance"),
        Index("idx_wallets_agent_balance", "agent_id", "balance"),
    )

    def __repr__(self) -> str:
        return f"<Wallet(id={self.id}, agent_id={self.agent_id}, balance={self.balance}, currency={self.currency})>"

    def has_sufficient_balance(self, amount: float) -> bool:
        """Check if wallet has sufficient balance."""
        return self.balance >= amount

    def debit(self, amount: float) -> bool:
        """
        Debit (subtract) from wallet balance.
        Returns True if successful, False if insufficient balance.
        """
        if not self.has_sufficient_balance(amount):
            return False
        self.balance -= amount
        return True

    def credit(self, amount: float) -> None:
        """Credit (add) to wallet balance."""
        self.balance += amount