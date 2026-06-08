from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.agent_repository import AgentRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.agent import AgentCreateRequest, AgentListResponse, AgentResponse
from app.services.agent_service import (
    AgentService,
    AgentLimitExceededError,
    AgentAlreadyExistsError
)

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    request: AgentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent_repo = AgentRepository(db)
    wallet_repo = WalletRepository(db)
    agent_service = AgentService(agent_repo, wallet_repo)

    try:
        agent = agent_service.create_agent(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
        )
        return agent
    except AgentAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except AgentLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=AgentListResponse)
def get_user_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent_repo = AgentRepository(db)
    agent_service = AgentService(agent_repo)

    agents = agent_service.get_user_agents(current_user.id)

    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent_repo = AgentRepository(db)
    agent_service = AgentService(agent_repo)

    agent = agent_service.get_agent(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this agent",
        )

    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_200_OK)
def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent_repo = AgentRepository(db)
    agent_service = AgentService(agent_repo)

    agent = agent_service.get_agent(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    if agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this agent",
        )

    agent_service.delete_agent(agent_id)

    return {"message": "Agent deleted successfully"}
