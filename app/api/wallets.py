from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.agent_repository import AgentRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.wallet import (
    WalletBalanceUpdateRequest,
    WalletCreateRequest,
    WalletResponse,
)
from app.services.wallet_service import (
    WalletAlreadyExistsError,
    WalletNotFoundError,
    InsufficientBalanceError,
    InvalidAmountError,
    WalletService,
)

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.get("/agent/{agent_id}", response_model=WalletResponse)
def get_wallet_by_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    wallet_repo = WalletRepository(db)
    wallet_service = WalletService(wallet_repo)
    
    try:
        wallet = wallet_service.get_wallet_by_agent(agent_id)
        return wallet
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=list[WalletResponse])
def get_all_user_wallets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent_repo = AgentRepository(db)
    agents = agent_repo.get_by_user(current_user.id)
    
    wallet_repo = WalletRepository(db)
    wallets = []
    
    for agent in agents:
        wallet = wallet_repo.get_wallet_by_agent(agent.id)
        if wallet:
            wallets.append(wallet)
    
    return wallets


@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet_by_id(
    wallet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet_repo = WalletRepository(db)
    wallet_service = WalletService(wallet_repo)
    
    try:
        wallet = wallet_service.get_wallet(wallet_id)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(wallet.agent_id)
    
    if not agent or agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return wallet


@router.post("/", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def create_wallet(
    request: WalletCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(request.agent_id)
    
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    wallet_repo = WalletRepository(db)
    wallet_service = WalletService(wallet_repo)
    
    try:
        wallet = wallet_service.create_wallet(request.agent_id)
        return wallet
    except WalletAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{wallet_id}/credit", response_model=WalletResponse)
def credit_wallet(
    wallet_id: UUID,
    request: WalletBalanceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet_repo = WalletRepository(db)
    wallet_service = WalletService(wallet_repo)
    
    try:
        wallet = wallet_service.get_wallet(wallet_id)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(wallet.agent_id)
    
    if not agent or agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        updated_wallet = wallet_service.credit_wallet(wallet_id, request.amount)
        return updated_wallet
    except InvalidAmountError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{wallet_id}/debit", response_model=WalletResponse)
def debit_wallet(
    wallet_id: UUID,
    request: WalletBalanceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet_repo = WalletRepository(db)
    wallet_service = WalletService(wallet_repo)
    
    try:
        wallet = wallet_service.get_wallet(wallet_id)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(wallet.agent_id)
    
    if not agent or agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        updated_wallet = wallet_service.debit_wallet(wallet_id, request.amount)
        return updated_wallet
    except (InvalidAmountError, InsufficientBalanceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))