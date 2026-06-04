from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agents import Agent
    from app.models.wallet import Wallet


class Usage(BaseModel):
    __tablename__ = "usages"

    wallet_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    service_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    credits_used: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    request_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="completed"
    )

    wallet: Mapped["Wallet"] = relationship(
        "Wallet",
        back_populates="usages"
    )

    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="usages"
    )

    __table_args__ = (
        Index("idx_usages_wallet", "wallet_id"),
        Index("idx_usages_agent", "agent_id"),
        Index("idx_usages_service", "service_name"),
        Index("idx_usages_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Usage(id={self.id}, wallet_id={self.wallet_id}, agent_id={self.agent_id}, service_name={self.service_name}, credits_used={self.credits_used}, status={self.status})>"