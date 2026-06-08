from uuid import UUID
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.services.wallet_service import (
    WalletService,
    WalletNotFoundError,
    WalletAccessDeniedError,
    InsufficientBalanceError,
    InvalidAmountError,
    WalletAlreadyExistsError
)
from app.models.user import User


router = APIRouter(
    prefix="/wallets",
    tags=["Wallets"]
)


class WalletResponse(BaseModel):
    id: UUID
    agent_id: UUID
    balance: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class CreditWalletRequest(BaseModel):
    amount: float


class DebitWalletRequest(BaseModel):
    amount: float


class TransactionResponse(BaseModel):
    id: UUID
    wallet_id: UUID
    amount: float
    transaction_type: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


def get_wallet_service(db: Session = Depends(get_db)) -> WalletService:
    return WalletService(db)


@router.get("/agent/{agent_id}", response_model=WalletResponse)
def get_wallet_by_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service)
):
    try:
        wallet = service.get_wallet_by_agent(agent_id, current_user.id)
        return WalletResponse.model_validate(wallet)
    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WalletAccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet_by_id(
    wallet_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service)
):
    try:
        wallet = service.get_wallet(wallet_id, current_user.id)
        return WalletResponse.model_validate(wallet)
    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WalletAccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/{wallet_id}/credit", response_model=WalletResponse)
def credit_wallet(
    wallet_id: UUID,
    request: CreditWalletRequest,
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service)
):
    try:
        wallet = service.credit_wallet(
            wallet_id=wallet_id,
            user_id=current_user.id,
            amount=request.amount,
            description="Manual credit"
        )
        return WalletResponse.model_validate(wallet)
    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WalletAccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except InvalidAmountError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{wallet_id}/debit", response_model=WalletResponse)
def debit_wallet(
    wallet_id: UUID,
    request: DebitWalletRequest,
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service)
):
    try:
        wallet = service.debit_wallet(
            wallet_id=wallet_id,
            user_id=current_user.id,
            amount=request.amount,
            description="Manual debit"
        )
        return WalletResponse.model_validate(wallet)
    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WalletAccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except (InvalidAmountError, InsufficientBalanceError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{wallet_id}/transactions", response_model=List[TransactionResponse])
def get_wallet_transactions(
    wallet_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service)
):
    try:
        transactions = service.get_wallet_transactions(
            wallet_id=wallet_id,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        return [TransactionResponse.model_validate(t) for t in transactions]
    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WalletAccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
