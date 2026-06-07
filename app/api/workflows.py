from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.services.workflow_service import WorkflowService, WorkflowNotFoundError, WorkflowAlreadyExistsError, InvalidWorkflowError
from app.services.workflow_execution_service import WorkflowExecutionService, WorkflowExecutionNotFoundError, InvalidExecutionError
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.workflow_execution_repository import WorkflowExecutionRepository
from app.repositories.agent_repository import AgentRepository
from app.models.user import User
from app.models.workflow_execution import ExecutionStatus


router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"]
)


class CreateWorkflowRequest(BaseModel):
    agent_id: UUID
    name: str
    description: Optional[str] = None
    n8n_workflow_id: Optional[str] = None
    webhook_url: Optional[str] = None
    execution_cost: float = 1.0


class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    n8n_workflow_id: Optional[str] = None
    webhook_url: Optional[str] = None
    execution_cost: Optional[float] = None
    is_active: Optional[bool] = None


class WorkflowResponse(BaseModel):
    id: UUID
    agent_id: UUID
    name: str
    description: Optional[str]
    n8n_workflow_id: Optional[str]
    webhook_url: Optional[str]
    execution_cost: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExecuteWorkflowRequest(BaseModel):
    input_payload: Optional[dict] = None


class ExecuteWorkflowResponse(BaseModel):
    execution_id: UUID
    status: ExecutionStatus


class ExecutionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    agent_id: UUID
    status: ExecutionStatus
    n8n_execution_id: Optional[str]
    input_payload: Optional[dict]
    output_payload: Optional[dict]
    error_message: Optional[str]
    credits_consumed: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


def get_workflow_service(db: Session = Depends(get_db)) -> WorkflowService:
    workflow_repo = WorkflowRepository(db)
    agent_repo = AgentRepository(db)
    return WorkflowService(workflow_repo, agent_repo)


def get_workflow_execution_service(db: Session = Depends(get_db)) -> WorkflowExecutionService:
    execution_repo = WorkflowExecutionRepository(db)
    workflow_repo = WorkflowRepository(db)
    agent_repo = AgentRepository(db)
    return WorkflowExecutionService(execution_repo, workflow_repo, agent_repo)


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    request: CreateWorkflowRequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service)
):
    try:
        workflow = service.create_workflow(
            agent_id=request.agent_id,
            name=request.name,
            description=request.description,
            n8n_workflow_id=request.n8n_workflow_id,
            webhook_url=request.webhook_url,
            execution_cost=request.execution_cost,
            is_active=True
        )
        return WorkflowResponse.model_validate(workflow)
    except InvalidWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except WorkflowAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/", response_model=List[WorkflowResponse])
def get_workflows(
    agent_id: Optional[UUID] = Query(None, description="Agent ID to filter workflows"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service)
):
    if agent_id:
        try:
            workflows = service.get_agent_workflows(agent_id, skip, limit)
        except InvalidWorkflowError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    else:
        workflows = service.get_active_workflows(None, skip, limit)
    
    return [WorkflowResponse.model_validate(w) for w in workflows]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service)
):
    try:
        workflow = service.get_workflow(workflow_id)
        return WorkflowResponse.model_validate(workflow)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: UUID,
    request: UpdateWorkflowRequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service)
):
    try:
        workflow = service.update_workflow(
            workflow_id=workflow_id,
            name=request.name,
            description=request.description,
            n8n_workflow_id=request.n8n_workflow_id,
            webhook_url=request.webhook_url,
            execution_cost=request.execution_cost,
            is_active=request.is_active
        )
        return WorkflowResponse.model_validate(workflow)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except (InvalidWorkflowError, WorkflowAlreadyExistsError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service)
):
    try:
        service.delete_workflow(workflow_id)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{workflow_id}/activate", response_model=WorkflowResponse)
def activate_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service)
):
    try:
        workflow = service.activate_workflow(workflow_id)
        return WorkflowResponse.model_validate(workflow)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{workflow_id}/deactivate", response_model=WorkflowResponse)
def deactivate_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service)
):
    try:
        workflow = service.deactivate_workflow(workflow_id)
        return WorkflowResponse.model_validate(workflow)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{workflow_id}/execute", response_model=ExecuteWorkflowResponse)
def execute_workflow(
    workflow_id: UUID,
    request: ExecuteWorkflowRequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
    execution_service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    try:
        workflow = service.get_workflow(workflow_id)
        
        if not workflow.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow is inactive"
            )
        
        execution = execution_service.create_execution(
            workflow_id=workflow_id,
            agent_id=workflow.agent_id,
            input_payload=request.input_payload,
            credits_consumed=workflow.execution_cost
        )
        
        return ExecuteWorkflowResponse(
            execution_id=execution.id,
            status=execution.status
        )
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{workflow_id}/executions", response_model=List[ExecutionResponse])
def get_workflow_executions(
    workflow_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
    execution_service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    try:
        service.get_workflow(workflow_id)
        
        executions = execution_service.get_workflow_executions(workflow_id, skip, limit)
        return [ExecutionResponse.model_validate(e) for e in executions]
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )