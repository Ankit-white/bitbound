from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.services.workflow_execution_service import (
    WorkflowExecutionService,
    WorkflowExecutionNotFoundError,
    InvalidExecutionError
)
from app.repositories.workflow_execution_repository import WorkflowExecutionRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.agent_repository import AgentRepository
from app.models.user import User
from app.models.workflow_execution import ExecutionStatus


router = APIRouter(
    prefix="/workflow-executions",
    tags=["Workflow Executions"]
)


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
    webhook_response_status: Optional[int]
    webhook_response_body: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CompleteExecutionRequest(BaseModel):
    output_payload: Optional[dict] = None
    webhook_response_status: Optional[int] = None
    webhook_response_body: Optional[str] = None


class FailExecutionRequest(BaseModel):
    error_message: str


def get_workflow_execution_service(db: Session = Depends(get_db)) -> WorkflowExecutionService:
    execution_repo = WorkflowExecutionRepository(db)
    workflow_repo = WorkflowRepository(db)
    agent_repo = AgentRepository(db)
    return WorkflowExecutionService(execution_repo, workflow_repo, agent_repo)


@router.get("/pending", response_model=List[ExecutionResponse])
def get_pending_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    executions = service.get_pending_executions(skip, limit)
    return [ExecutionResponse.model_validate(e) for e in executions]


@router.get("/running", response_model=List[ExecutionResponse])
def get_running_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    executions = service.get_running_executions(skip, limit)
    return [ExecutionResponse.model_validate(e) for e in executions]


@router.get("/completed", response_model=List[ExecutionResponse])
def get_completed_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    executions = service.get_completed_executions(skip, limit)
    return [ExecutionResponse.model_validate(e) for e in executions]


@router.get("/failed", response_model=List[ExecutionResponse])
def get_failed_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    executions = service.get_failed_executions(skip, limit)
    return [ExecutionResponse.model_validate(e) for e in executions]


@router.get("/stuck", response_model=List[ExecutionResponse])
def get_stuck_executions(
    minutes: int = Query(30, ge=1, description="Minutes after which execution is considered stuck"),
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    executions = service.get_stuck_executions(minutes)
    return [ExecutionResponse.model_validate(e) for e in executions]


@router.get("/agent/{agent_id}", response_model=List[ExecutionResponse])
def get_agent_executions(
    agent_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    try:
        executions = service.get_agent_executions(agent_id, skip, limit)
        return [ExecutionResponse.model_validate(e) for e in executions]
    except InvalidExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/workflow/{workflow_id}", response_model=List[ExecutionResponse])
def get_workflow_executions(
    workflow_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    try:
        executions = service.get_workflow_executions(workflow_id, skip, limit)
        return [ExecutionResponse.model_validate(e) for e in executions]
    except InvalidExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    try:
        execution = service.get_execution(execution_id)
        return ExecutionResponse.model_validate(execution)
    except WorkflowExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{execution_id}/running", response_model=ExecutionResponse)
def mark_running(
    execution_id: UUID,
    n8n_execution_id: Optional[str] = Query(None, description="n8n execution ID"),
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    try:
        execution = service.mark_running(execution_id, n8n_execution_id)
        return ExecutionResponse.model_validate(execution)
    except WorkflowExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{execution_id}/complete", response_model=ExecutionResponse)
def mark_completed(
    execution_id: UUID,
    request: CompleteExecutionRequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    try:
        execution = service.mark_completed(
            execution_id=execution_id,
            output_payload=request.output_payload,
            webhook_response_status=request.webhook_response_status,
            webhook_response_body=request.webhook_response_body
        )
        return ExecutionResponse.model_validate(execution)
    except WorkflowExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{execution_id}/fail", response_model=ExecutionResponse)
def mark_failed(
    execution_id: UUID,
    request: FailExecutionRequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    try:
        execution = service.mark_failed(execution_id, request.error_message)
        return ExecutionResponse.model_validate(execution)
    except WorkflowExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_execution(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    try:
        service.delete_execution(execution_id)
    except WorkflowExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )