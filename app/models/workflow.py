from sqlalchemy import String, Text, Boolean, ForeignKey, Index, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from typing import Optional, TYPE_CHECKING

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agents import Agent
    from app.models.workflow_execution import WorkflowExecution


class Workflow(BaseModel):
    """Workflow model for n8n workflow integration."""
    
    __tablename__ = "workflows"
    
    # Foreign key to agent
    agent_id: Mapped[UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Workflow details
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # n8n integration fields
    n8n_workflow_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True
    )
    
    webhook_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Status flag
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    
    # Monetization: Cost per execution in credits
    execution_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0
    )
    
    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="workflows"
    )
    
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_workflows_agent_id", "agent_id"),
        Index("idx_workflows_n8n_workflow_id", "n8n_workflow_id"),
        Index("idx_workflows_is_active", "is_active"),
        Index("idx_workflows_agent_active", "agent_id", "is_active"),
        Index("idx_workflows_cost", "execution_cost"),
    )
    
    def __repr__(self) -> str:
        """String representation of Workflow."""
        return f"<Workflow(id={self.id!r}, name={self.name!r}, agent_id={self.agent_id!r}, is_active={self.is_active!r})>"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"Workflow: {self.name} (Agent: {self.agent_id})"
    
    @property
    def is_ready(self) -> bool:
        """Check if workflow is ready for execution."""
        return self.is_active and self.n8n_workflow_id is not None and self.webhook_url is not None
    
    @property
    def execution_count(self) -> int:
        """Get total number of executions for this workflow."""
        return len(self.executions) if self.executions else 0