from uuid import UUID
from typing import Optional, Dict, Any

from app.repositories.workflow_execution_repository import WorkflowExecutionRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.agent_repository import AgentRepository
from app.models.workflow_execution import WorkflowExecution, ExecutionStatus


class WorkflowExecutionNotFoundError(Exception):
    """Raised when workflow execution does not exist."""
    pass


class InvalidExecutionError(Exception):
    """Raised when execution data is invalid."""
    pass


class WorkflowExecutionService:
    def __init__(
        self,
        execution_repository: WorkflowExecutionRepository,
        workflow_repository: WorkflowRepository,
        agent_repository: AgentRepository
    ):
        self.execution_repository = execution_repository
        self.workflow_repository = workflow_repository
        self.agent_repository = agent_repository

    def create_execution(
        self,
        workflow_id: UUID,
        agent_id: UUID,
        input_payload: Optional[Dict[str, Any]] = None,
        credits_consumed: float = 0.0
    ) -> WorkflowExecution:
        if credits_consumed < 0:
            raise InvalidExecutionError("Credits consumed cannot be negative")
        
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if not workflow:
            raise InvalidExecutionError(f"Workflow with id {workflow_id} does not exist")
        
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise InvalidExecutionError(f"Agent with id {agent_id} does not exist")
        
        return self.execution_repository.create_execution(
            workflow_id=workflow_id,
            agent_id=agent_id,
            input_payload=input_payload,
            credits_consumed=credits_consumed
        )

    def get_execution(self, execution_id: UUID) -> WorkflowExecution:
        execution = self.execution_repository.get_by_id(execution_id)
        if not execution:
            raise WorkflowExecutionNotFoundError(f"Execution with id {execution_id} not found")
        return execution

    def get_workflow_executions(
        self,
        workflow_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[WorkflowExecution]:
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if not workflow:
            raise InvalidExecutionError(f"Workflow with id {workflow_id} does not exist")
        
        return self.execution_repository.get_by_workflow(workflow_id, skip, limit)

    def get_agent_executions(
        self,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[WorkflowExecution]:
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise InvalidExecutionError(f"Agent with id {agent_id} does not exist")
        
        return self.execution_repository.get_by_agent(agent_id, skip, limit)

    def mark_running(
        self,
        execution_id: UUID,
        n8n_execution_id: Optional[str] = None
    ) -> WorkflowExecution:
        execution = self.get_execution(execution_id)
        
        if execution.status != ExecutionStatus.PENDING:
            raise InvalidExecutionError(
                f"Cannot mark execution {execution_id} as running. "
                f"Current status: {execution.status}"
            )
        
        updated = self.execution_repository.update_status(
            execution_id=execution_id,
            status=ExecutionStatus.RUNNING,
            n8n_execution_id=n8n_execution_id
        )
        
        if not updated:
            raise WorkflowExecutionNotFoundError(f"Execution with id {execution_id} not found")
        
        return updated

    def mark_completed(
        self,
        execution_id: UUID,
        output_payload: Optional[Dict[str, Any]] = None,
        webhook_response_status: Optional[int] = None,
        webhook_response_body: Optional[str] = None
    ) -> WorkflowExecution:
        execution = self.get_execution(execution_id)
        
        if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
            raise InvalidExecutionError(
                f"Cannot mark execution {execution_id} as completed. "
                f"Current status: {execution.status}"
            )
        
        updated = self.execution_repository.update_status(
            execution_id=execution_id,
            status=ExecutionStatus.COMPLETED
        )
        
        if not updated:
            raise WorkflowExecutionNotFoundError(f"Execution with id {execution_id} not found")
        
        if output_payload:
            self.execution_repository.update_output(
                execution_id=execution_id,
                output_payload=output_payload,
                webhook_response_status=webhook_response_status,
                webhook_response_body=webhook_response_body
            )
        
        return self.get_execution(execution_id)

    def mark_failed(
        self,
        execution_id: UUID,
        error_message: str
    ) -> WorkflowExecution:
        execution = self.get_execution(execution_id)
        
        if execution.status in [ExecutionStatus.COMPLETED]:
            raise InvalidExecutionError(
                f"Cannot mark execution {execution_id} as failed. "
                f"Current status: {execution.status}"
            )
        
        updated = self.execution_repository.update_error(
            execution_id=execution_id,
            error_message=error_message
        )
        
        if not updated:
            raise WorkflowExecutionNotFoundError(f"Execution with id {execution_id} not found")
        
        return updated

    def delete_execution(self, execution_id: UUID) -> bool:
        execution = self.get_execution(execution_id)
        
        deleted = self.execution_repository.delete_execution(execution_id)
        if not deleted:
            raise WorkflowExecutionNotFoundError(f"Execution with id {execution_id} not found")
        
        return True

    def get_pending_executions(self, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return self.execution_repository.get_pending_executions(skip, limit)

    def get_running_executions(self, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return self.execution_repository.get_running_executions(skip, limit)

    def get_completed_executions(self, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return self.execution_repository.get_completed_executions(skip, limit)

    def get_failed_executions(self, skip: int = 0, limit: int = 100) -> list[WorkflowExecution]:
        return self.execution_repository.get_failed_executions(skip, limit)

    def get_stuck_executions(self, minutes: int = 30) -> list[WorkflowExecution]:
        return self.execution_repository.get_stuck_executions(minutes)

    def get_execution_by_n8n_id(self, n8n_execution_id: str) -> Optional[WorkflowExecution]:
        return self.execution_repository.get_by_n8n_execution_id(n8n_execution_id)

    def get_recent_executions(self, limit: int = 20) -> list[WorkflowExecution]:
        return self.execution_repository.get_recent_executions(limit)

    def get_agent_executions_by_status(
        self,
        agent_id: UUID,
        status: ExecutionStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[WorkflowExecution]:
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise InvalidExecutionError(f"Agent with id {agent_id} does not exist")
        
        return self.execution_repository.get_by_agent_and_status(agent_id, status, skip, limit)