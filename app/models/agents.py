from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.wallet import Wallet
    from app.models.usage import Usage
    from app.models.workflow import Workflow
    from app.models.workflow_execution import WorkflowExecution
    from app.models.api_key import APIKey


class Agent(BaseModel):
    __tablename__ = "agents"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active"
    )

    monthly_budget: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    credits_used: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    user: Mapped["User"] = relationship("User", back_populates="agents")
    
    wallet: Mapped["Wallet"] = relationship(
        "Wallet",
        back_populates="agent",
        uselist=False,
        cascade="all, delete-orphan"
    )

    usages: Mapped[list["Usage"]] = relationship(
        "Usage",
        back_populates="agent",
        cascade="all, delete-orphan"
    )

    workflows: Mapped[list["Workflow"]] = relationship(
        "Workflow",
        back_populates="agent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    workflow_executions: Mapped[list["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="agent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="agent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_agents_user", "user_id"),
        Index("idx_agents_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, user_id={self.user_id}, status={self.status})>"