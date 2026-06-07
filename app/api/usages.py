from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.services.usage_service import (
    UsageService,
    UsageNotFoundError,
    InvalidUsageError,
    AgentNotFoundError,
    WalletNotFoundError
)
from app.repositories.usage_repository import UsageRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.wallet_repository import WalletRepository
from app.models.user import User


router = APIRouter(
    prefix="/usage",
    tags=["Usage"]
)


class CreateUsageRequest(BaseModel):
    agent_id: UUID
    credits_used: float
    usage_type: str
    wallet_id: Optional[UUID] = None
    workflow_execution_id: Optional[UUID] = None
    description: Optional[str] = None
    usage_metadata: Optional[dict] = None


class UsageResponse(BaseModel):
    id: UUID
    agent_id: UUID
    wallet_id: Optional[UUID]
    workflow_execution_id: Optional[UUID]
    credits_used: float
    usage_type: str
    description: Optional[str]
    usage_metadata: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class TotalCreditsResponse(BaseModel):
    total_credits: float


class UsageSummaryResponse(BaseModel):
    usage_type: str
    total_credits: float
    usage_count: int


class DailyUsageResponse(BaseModel):
    date: str
    total_credits: float


def get_usage_service(db: Session = Depends(get_db)) -> UsageService:
    usage_repo = UsageRepository(db)
    agent_repo = AgentRepository(db)
    wallet_repo = WalletRepository(db)
    return UsageService(usage_repo, agent_repo, wallet_repo)


@router.get("/agent/{agent_id}", response_model=List[UsageResponse])
def get_agent_usage(
    agent_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    service: UsageService = Depends(get_usage_service)
):
    try:
        usage_records = service.get_agent_usage(
            agent_id=agent_id,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        return [UsageResponse.model_validate(u) for u in usage_records]
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/wallet/{wallet_id}", response_model=List[UsageResponse])
def get_wallet_usage(
    wallet_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: UsageService = Depends(get_usage_service)
):
    try:
        usage_records = service.get_wallet_usage(
            wallet_id=wallet_id,
            skip=skip,
            limit=limit
        )
        return [UsageResponse.model_validate(u) for u in usage_records]
    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/workflow-execution/{execution_id}", response_model=UsageResponse)
def get_workflow_execution_usage(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UsageService = Depends(get_usage_service)
):
    try:
        usage = service.get_workflow_execution_usage(execution_id)
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usage for workflow execution {execution_id} not found"
            )
        return UsageResponse.model_validate(usage)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/agent/{agent_id}/total-credits", response_model=TotalCreditsResponse)
def get_total_credits_used(
    agent_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    service: UsageService = Depends(get_usage_service)
):
    try:
        total = service.get_total_credits_used(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date
        )
        return TotalCreditsResponse(total_credits=total)
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/agent/{agent_id}/summary", response_model=List[UsageSummaryResponse])
def get_usage_summary(
    agent_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    service: UsageService = Depends(get_usage_service)
):
    try:
        summary = service.get_usage_summary_by_type(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date
        )
        return [UsageSummaryResponse(**s) for s in summary]
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/agent/{agent_id}/daily", response_model=List[DailyUsageResponse])
def get_daily_usage(
    agent_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: UsageService = Depends(get_usage_service)
):
    try:
        daily_usage = service.get_daily_usage(
            agent_id=agent_id,
            days=days
        )
        return [DailyUsageResponse(**d) for d in daily_usage]
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/", response_model=UsageResponse, status_code=status.HTTP_201_CREATED)
def create_usage(
    request: CreateUsageRequest,
    current_user: User = Depends(get_current_user),
    service: UsageService = Depends(get_usage_service)
):
    try:
        usage = service.create_usage(
            agent_id=request.agent_id,
            credits_used=request.credits_used,
            usage_type=request.usage_type,
            wallet_id=request.wallet_id,
            workflow_execution_id=request.workflow_execution_id,
            description=request.description,
            usage_metadata=request.usage_metadata
        )
        return UsageResponse.model_validate(usage)
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidUsageError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{usage_id}", response_model=UsageResponse)
def get_usage(
    usage_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UsageService = Depends(get_usage_service)
):
    try:
        usage = service.get_usage(usage_id)
        return UsageResponse.model_validate(usage)
    except UsageNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{usage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usage(
    usage_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UsageService = Depends(get_usage_service)
):
    try:
        service.delete_usage(usage_id)
    except UsageNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )