from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agents import Agent
    from app.models.wallet import Wallet
    from app.models.workflow_execution import WorkflowExecution


class Usage(BaseModel):
    __tablename__ = "usages"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    wallet_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wallets.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    workflow_execution_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    credits_used: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    usage_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    usage_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="usages"
    )

    wallet: Mapped[Optional["Wallet"]] = relationship(
        "Wallet",
        back_populates="usages"
    )

    workflow_execution: Mapped[Optional["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="usage"
    )

    __table_args__ = (
        Index("idx_usages_agent", "agent_id"),
        Index("idx_usages_wallet", "wallet_id"),
        Index("idx_usages_workflow_execution", "workflow_execution_id"),
        Index("idx_usages_type", "usage_type"),
        Index("idx_usages_created_at", "created_at"),
        Index("idx_usages_agent_type", "agent_id", "usage_type"),
        Index("idx_usages_agent_created", "agent_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Usage(id={self.id}, agent_id={self.agent_id}, credits_used={self.credits_used}, usage_type={self.usage_type})>"