from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.workflow import Workflow


class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db

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
        workflow = Workflow(
            agent_id=agent_id,
            name=name,
            description=description,
            n8n_workflow_id=n8n_workflow_id,
            webhook_url=webhook_url,
            execution_cost=execution_cost,
            is_active=is_active
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_by_id(self, workflow_id: UUID) -> Optional[Workflow]:
        return self.db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()

    def get_by_agent(self, agent_id: UUID, skip: int = 0, limit: int = 100) -> list[Workflow]:
        return (
            self.db.query(Workflow)
            .filter(Workflow.agent_id == agent_id)
            .order_by(Workflow.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_n8n_id(self, n8n_workflow_id: str) -> Optional[Workflow]:
        return self.db.query(Workflow).filter(
            Workflow.n8n_workflow_id == n8n_workflow_id
        ).first()

    def get_active_workflows(self, agent_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> list[Workflow]:
        query = self.db.query(Workflow).filter(Workflow.is_active.is_(True))
        if agent_id:
            query = query.filter(Workflow.agent_id == agent_id)
        return (
            query
            .order_by(Workflow.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_ready_workflows(self, agent_id: Optional[UUID] = None) -> list[Workflow]:
        query = self.db.query(Workflow).filter(
            Workflow.is_active.is_(True),
            Workflow.n8n_workflow_id.isnot(None),
            Workflow.webhook_url.isnot(None),
        )
        if agent_id:
            query = query.filter(Workflow.agent_id == agent_id)
        return query.order_by(Workflow.created_at.desc()).all()

    def activate_workflow(self, workflow_id: UUID) -> Optional[Workflow]:
        workflow = self.get_by_id(workflow_id)
        if workflow:
            workflow.is_active = True
            self.db.commit()
            self.db.refresh(workflow)
        return workflow

    def deactivate_workflow(self, workflow_id: UUID) -> Optional[Workflow]:
        workflow = self.get_by_id(workflow_id)
        if workflow:
            workflow.is_active = False
            self.db.commit()
            self.db.refresh(workflow)
        return workflow

    def update_workflow(
        self,
        workflow_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        n8n_workflow_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        execution_cost: Optional[float] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Workflow]:
        workflow = self.get_by_id(workflow_id)
        if workflow:
            if name is not None:
                workflow.name = name
            if description is not None:
                workflow.description = description
            if n8n_workflow_id is not None:
                workflow.n8n_workflow_id = n8n_workflow_id
            if webhook_url is not None:
                workflow.webhook_url = webhook_url
            if execution_cost is not None:
                workflow.execution_cost = execution_cost
            if is_active is not None:
                workflow.is_active = is_active
            self.db.commit()
            self.db.refresh(workflow)
        return workflow

    def delete_workflow(self, workflow_id: UUID) -> bool:
        workflow = self.get_by_id(workflow_id)
        if workflow:
            self.db.delete(workflow)
            self.db.commit()
            return True
        return False

    def get_by_agent_and_status(self, agent_id: UUID, is_active: bool) -> list[Workflow]:
        return (
            self.db.query(Workflow)
            .filter(
                and_(
                    Workflow.agent_id == agent_id,
                    Workflow.is_active.is_(is_active)
                )
            )
            .order_by(Workflow.created_at.desc())
            .all()
        )