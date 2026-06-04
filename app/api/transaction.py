from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.agent_repository import AgentRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
)
from app.services.transaction_service import (
    InvalidAmountError,
    InvalidTransactionTypeError,
    TransactionNotFoundError,
    TransactionService,
    WalletNotFoundError,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    request: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_wallet_by_id(request.wallet_id)
    
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(wallet.agent_id)
    
    if not agent or agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    transaction_repo = TransactionRepository(db)
    transaction_service = TransactionService(transaction_repo, wallet_repo)
    
    try:
        transaction = transaction_service.create_transaction(
            wallet_id=request.wallet_id,
            amount=request.amount,
            transaction_type=request.transaction_type,
            description=request.description,
        )
        return transaction
    except (InvalidAmountError, InvalidTransactionTypeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=TransactionListResponse)
def get_all_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent_repo = AgentRepository(db)
    agents = agent_repo.get_by_user(current_user.id)
    
    if not agents:
        return TransactionListResponse(transactions=[], total=0)
    
    wallet_repo = WalletRepository(db)
    wallet_ids = []
    
    for agent in agents:
        wallet = wallet_repo.get_wallet_by_agent(agent.id)
        if wallet:
            wallet_ids.append(wallet.id)
    
    transaction_repo = TransactionRepository(db)
    all_transactions = transaction_repo.get_all_transactions()
    
    filtered_transactions = [
        t for t in all_transactions if t.wallet_id in wallet_ids
    ]
    
    return TransactionListResponse(
        transactions=filtered_transactions,
        total=len(filtered_transactions)
    )


@router.get("/wallet/{wallet_id}", response_model=TransactionListResponse)
def get_wallet_transactions(
    wallet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_wallet_by_id(wallet_id)
    
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(wallet.agent_id)
    
    if not agent or agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    transaction_repo = TransactionRepository(db)
    transaction_service = TransactionService(transaction_repo, wallet_repo)
    
    transactions = transaction_service.get_wallet_transactions(wallet_id)
    
    return TransactionListResponse(
        transactions=transactions,
        total=len(transactions)
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction_repo = TransactionRepository(db)
    transaction_service = TransactionService(transaction_repo, WalletRepository(db))
    
    try:
        transaction = transaction_service.get_transaction(transaction_id)
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_wallet_by_id(transaction.wallet_id)
    
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_by_id(wallet.agent_id)
    
    if not agent or agent.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return transaction