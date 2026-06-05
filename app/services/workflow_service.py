from uuid import UUID
from typing import Optional

from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.agent_repository import AgentRepository
from app.models.workflow import Workflow


class WorkflowNotFoundError(Exception):
    """Raised when workflow does not exist."""
    pass


class WorkflowAlreadyExistsError(Exception):
    """Raised when workflow with same name already exists for the agent."""
    pass


class InvalidWorkflowError(Exception):
    """Raised when workflow data is invalid."""
    pass


class WorkflowService:
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        agent_repository: AgentRepository
    ):
        self.workflow_repository = workflow_repository
        self.agent_repository = agent_repository

    def create_workflow(
        self,
        agent_id: UUID,
        name: str,
        description: Optional[str] = None,
        n8n_workflow_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        execution_cost: float = 1.0,
        is_active: bool = True
    ) -> Workflow:
        if not name or not name.strip():
            raise InvalidWorkflowError("Workflow name cannot be empty")
        
        if execution_cost <= 0:
            raise InvalidWorkflowError("Execution cost must be greater than 0")
        
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise InvalidWorkflowError(f"Agent with id {agent_id} does not exist")
        
        existing_workflows = self.workflow_repository.get_by_agent(agent_id, limit=1000)
        for workflow in existing_workflows:
            if workflow.name.lower() == name.strip().lower():
                raise WorkflowAlreadyExistsError(
                    f"Workflow with name '{name}' already exists for this agent"
                )
        
        return self.workflow_repository.create_workflow(
            agent_id=agent_id,
            name=name.strip(),
            description=description,
            n8n_workflow_id=n8n_workflow_id,
            webhook_url=webhook_url,
            execution_cost=execution_cost,
            is_active=is_active
        )

    def get_workflow(self, workflow_id: UUID) -> Workflow:
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow with id {workflow_id} not found")
        return workflow

    def get_agent_workflows(
        self,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Workflow]:
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise InvalidWorkflowError(f"Agent with id {agent_id} does not exist")
        
        return self.workflow_repository.get_by_agent(agent_id, skip, limit)

    def get_active_workflows(
        self,
        agent_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Workflow]:
        if agent_id:
            agent = self.agent_repository.get_by_id(agent_id)
            if not agent:
                raise InvalidWorkflowError(f"Agent with id {agent_id} does not exist")
        
        return self.workflow_repository.get_active_workflows(agent_id, skip, limit)

    def get_ready_workflows(self, agent_id: Optional[UUID] = None) -> list[Workflow]:
        if agent_id:
            agent = self.agent_repository.get_by_id(agent_id)
            if not agent:
                raise InvalidWorkflowError(f"Agent with id {agent_id} does not exist")
        
        return self.workflow_repository.get_ready_workflows(agent_id)

    def activate_workflow(self, workflow_id: UUID) -> Workflow:
        workflow = self.get_workflow(workflow_id)
        
        if workflow.is_active:
            return workflow
        
        activated_workflow = self.workflow_repository.activate_workflow(workflow_id)
        if not activated_workflow:
            raise WorkflowNotFoundError(f"Workflow with id {workflow_id} not found")
        
        return activated_workflow

    def deactivate_workflow(self, workflow_id: UUID) -> Workflow:
        workflow = self.get_workflow(workflow_id)
        
        if not workflow.is_active:
            return workflow
        
        deactivated_workflow = self.workflow_repository.deactivate_workflow(workflow_id)
        if not deactivated_workflow:
            raise WorkflowNotFoundError(f"Workflow with id {workflow_id} not found")
        
        return deactivated_workflow

    def update_workflow(
        self,
        workflow_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        n8n_workflow_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        execution_cost: Optional[float] = None,
        is_active: Optional[bool] = None
    ) -> Workflow:
        workflow = self.get_workflow(workflow_id)
        
        if name is not None:
            if not name or not name.strip():
                raise InvalidWorkflowError("Workflow name cannot be empty")
            
            if name.strip().lower() != workflow.name.lower():
                existing_workflows = self.workflow_repository.get_by_agent(
                    workflow.agent_id, limit=1000
                )
                for existing in existing_workflows:
                    if existing.name.lower() == name.strip().lower():
                        raise WorkflowAlreadyExistsError(
                            f"Workflow with name '{name}' already exists for this agent"
                        )
        
        if execution_cost is not None and execution_cost <= 0:
            raise InvalidWorkflowError("Execution cost must be greater than 0")
        
        updated_workflow = self.workflow_repository.update_workflow(
            workflow_id=workflow_id,
            name=name.strip() if name else None,
            description=description,
            n8n_workflow_id=n8n_workflow_id,
            webhook_url=webhook_url,
            execution_cost=execution_cost,
            is_active=is_active
        )
        
        if not updated_workflow:
            raise WorkflowNotFoundError(f"Workflow with id {workflow_id} not found")
        
        return updated_workflow

    def delete_workflow(self, workflow_id: UUID) -> bool:
        workflow = self.get_workflow(workflow_id)
        
        deleted = self.workflow_repository.delete_workflow(workflow_id)
        if not deleted:
            raise WorkflowNotFoundError(f"Workflow with id {workflow_id} not found")
        
        return True

    def get_workflow_by_n8n_id(self, n8n_workflow_id: str) -> Optional[Workflow]:
        return self.workflow_repository.get_by_n8n_id(n8n_workflow_id)

    def get_by_agent_and_status(self, agent_id: UUID, is_active: bool) -> list[Workflow]:
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise InvalidWorkflowError(f"Agent with id {agent_id} does not exist")
        
        return self.workflow_repository.get_by_agent_and_status(agent_id, is_active)