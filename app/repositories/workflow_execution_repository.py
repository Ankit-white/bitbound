from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta

from app.models.workflow_execution import WorkflowExecution, ExecutionStatus


class WorkflowExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_execution(
        self,
        workflow_id: UUID,
        agent_id: UUID,
        input_payload: Optional[dict] = None,
        credits_consumed: float = 0.0
    ) -> WorkflowExecution:
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            agent_id=agent_id,
            input_payload=input_payload,
            credits_consumed=credits_consumed,
            status=ExecutionStatus.PENDING
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def get_by_id(self, execution_id: UUID) -> Optional[WorkflowExecution]:
        return self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()

    def get_by_workflow(self, workflow_id: UUID, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.workflow_id == workflow_id)
            .order_by(WorkflowExecution.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_agent(self, agent_id: UUID, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.agent_id == agent_id)
            .order_by(WorkflowExecution.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_n8n_execution_id(self, n8n_execution_id: str) -> Optional[WorkflowExecution]:
        return self.db.query(WorkflowExecution).filter(
            WorkflowExecution.n8n_execution_id == n8n_execution_id
        ).first()

    def get_pending_executions(self, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.status == ExecutionStatus.PENDING)
            .order_by(WorkflowExecution.created_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_running_executions(self, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.status == ExecutionStatus.RUNNING)
            .order_by(WorkflowExecution.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_completed_executions(self, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.status == ExecutionStatus.COMPLETED)
            .order_by(WorkflowExecution.completed_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_failed_executions(self, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.status == ExecutionStatus.FAILED)
            .order_by(WorkflowExecution.completed_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(
        self,
        execution_id: UUID,
        status: ExecutionStatus,
        n8n_execution_id: Optional[str] = None
    ) -> Optional[WorkflowExecution]:
        execution = self.get_by_id(execution_id)
        if execution:
            if status == ExecutionStatus.RUNNING:
                execution.mark_started()
                if n8n_execution_id:
                    execution.n8n_execution_id = n8n_execution_id
            elif status == ExecutionStatus.COMPLETED:
                execution.mark_completed()
                if n8n_execution_id:
                    execution.n8n_execution_id = n8n_execution_id
            elif status == ExecutionStatus.FAILED:
                execution.mark_failed(execution.error_message or "Execution failed")
                if n8n_execution_id:
                    execution.n8n_execution_id = n8n_execution_id
            else:
                execution.status = status
            self.db.commit()
            self.db.refresh(execution)
        return execution

    def update_output(
        self,
        execution_id: UUID,
        output_payload: dict,
        webhook_response_status: Optional[int] = None,
        webhook_response_body: Optional[str] = None
    ) -> Optional[WorkflowExecution]:
        execution = self.get_by_id(execution_id)
        if execution:
            execution.output_payload = output_payload
            if webhook_response_status is not None:
                execution.webhook_response_status = webhook_response_status
            if webhook_response_body is not None:
                execution.webhook_response_body = webhook_response_body
            self.db.commit()
            self.db.refresh(execution)
        return execution

    def update_error(
        self,
        execution_id: UUID,
        error_message: str
    ) -> Optional[WorkflowExecution]:
        execution = self.get_by_id(execution_id)
        if execution:
            execution.error_message = error_message
            execution.mark_failed(error_message)
            self.db.commit()
            self.db.refresh(execution)
        return execution

    def delete_execution(self, execution_id: UUID) -> bool:
        execution = self.get_by_id(execution_id)
        if execution:
            self.db.delete(execution)
            self.db.commit()
            return True
        return False

    def get_by_agent_and_status(
        self,
        agent_id: UUID,
        status: ExecutionStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[WorkflowExecution]:
        return (
            self.db.query(WorkflowExecution)
            .filter(
                and_(
                    WorkflowExecution.agent_id == agent_id,
                    WorkflowExecution.status == status
                )
            )
            .order_by(WorkflowExecution.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_stuck_executions(self, minutes: int = 30) -> list[WorkflowExecution]:
        threshold = datetime.utcnow() - timedelta(minutes=minutes)
        return (
            self.db.query(WorkflowExecution)
            .filter(
                WorkflowExecution.status == ExecutionStatus.RUNNING,
                WorkflowExecution.started_at < threshold
            )
            .order_by(WorkflowExecution.started_at.asc())
            .all()
        )

    def get_recent_executions(self, limit: int = 20) -> list[WorkflowExecution]:
        return (
            self.db.query(WorkflowExecution)
            .order_by(WorkflowExecution.created_at.desc())
            .limit(limit)
            .all()
        )