from sqlalchemy import String, Text, ForeignKey, Index, JSON, Float, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.workflow import Workflow
    from app.models.agents import Agent
    from app.models.usage import Usage


class ExecutionStatus(str, Enum):
    """Execution status enum for workflow runs."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowExecution(BaseModel):
    """Workflow execution model to track each workflow run."""
    
    __tablename__ = "workflow_executions"
    
    # Foreign keys
    workflow_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False
    )
    
    agent_id: Mapped[UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Execution details
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ExecutionStatus.PENDING
    )
    
    # n8n execution tracking
    n8n_execution_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True
    )
    
    # Input/Output payloads
    input_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    output_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Credits tracking
    credits_consumed: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Webhook response tracking
    webhook_response_status: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    webhook_response_body: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Relationships
    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        back_populates="executions"
    )
    
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="workflow_executions"
    )
    
    usage: Mapped[Optional["Usage"]] = relationship(
        "Usage",
        back_populates="workflow_execution",
        uselist=False
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_workflow_executions_workflow_id", "workflow_id"),
        Index("idx_workflow_executions_agent_id", "agent_id"),
        Index("idx_workflow_executions_status", "status"),
        Index("idx_workflow_executions_n8n_execution_id", "n8n_execution_id"),
        Index("idx_workflow_executions_created_at", "created_at"),
        Index("idx_workflow_executions_workflow_status", "workflow_id", "status"),
        Index("idx_workflow_executions_agent_status", "agent_id", "status"),
        Index("idx_workflow_executions_status_created", "status", "created_at"),
        Index("idx_workflow_executions_credits", "credits_consumed"),
    )
    
    def __repr__(self) -> str:
        """String representation of WorkflowExecution."""
        return f"<WorkflowExecution(id={self.id!r}, workflow_id={self.workflow_id!r}, agent_id={self.agent_id!r}, status={self.status!r})>"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"Execution {self.id} for Workflow {self.workflow_id}: {self.status}"
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == ExecutionStatus.COMPLETED
    
    @property
    def is_finished(self) -> bool:
        """Check if execution has finished (completed or failed)."""
        return self.status in [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED
        ]
    
    def mark_started(self) -> None:
        """Mark execution as started."""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def mark_completed(self, output_payload: Optional[Dict[str, Any]] = None) -> None:
        """Mark execution as completed."""
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if output_payload:
            self.output_payload = output_payload
    
    def mark_failed(self, error_message: str) -> None:
        """Mark execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message