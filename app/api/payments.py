from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.agent_repository import AgentRepository
from app.repositories.credit_package_repository import CreditPackageRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.payment import (
    PaymentCompleteRequest,
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentResponse,
)
from app.services.payment_service import (
    InvalidPaymentStatusError,
    PackageNotFoundError,
    PaymentCreditingError,
    PaymentNotFoundError,
    PaymentService,
)
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    request: PaymentCreateRequest,
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
    
    payment_repo = PaymentRepository(db)
    package_repo = CreditPackageRepository(db)
    wallet_service = WalletService(wallet_repo)
    payment_service = PaymentService(payment_repo, wallet_service, package_repo)
    
    try:
        payment = payment_service.create_payment(
            user_id=current_user.id,
            wallet_id=request.wallet_id,
            package_id=request.package_id,
        )
        return payment
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=PaymentListResponse)
def get_all_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment_repo = PaymentRepository(db)
    package_repo = CreditPackageRepository(db)
    wallet_service = WalletService(WalletRepository(db))
    payment_service = PaymentService(payment_repo, wallet_service, package_repo)
    
    payments = payment_service.get_user_payments(current_user.id)
    
    return PaymentListResponse(payments=payments, total=len(payments))


@router.get("/wallet/{wallet_id}", response_model=PaymentListResponse)
def get_wallet_payments(
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
    
    payment_repo = PaymentRepository(db)
    package_repo = CreditPackageRepository(db)
    wallet_service = WalletService(wallet_repo)
    payment_service = PaymentService(payment_repo, wallet_service, package_repo)
    
    payments = payment_service.get_wallet_payments(wallet_id)
    
    return PaymentListResponse(payments=payments, total=len(payments))


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment_repo = PaymentRepository(db)
    package_repo = CreditPackageRepository(db)
    wallet_service = WalletService(WalletRepository(db))
    payment_service = PaymentService(payment_repo, wallet_service, package_repo)
    
    try:
        payment = payment_service.get_payment(payment_id)
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return payment


@router.post("/{payment_id}/complete", response_model=PaymentResponse)
def complete_payment(
    payment_id: UUID,
    request: PaymentCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment_repo = PaymentRepository(db)
    wallet_repo = WalletRepository(db)
    package_repo = CreditPackageRepository(db)
    wallet_service = WalletService(wallet_repo)
    payment_service = PaymentService(payment_repo, wallet_service, package_repo)
    
    try:
        payment = payment_service.get_payment(payment_id)
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        updated_payment = payment_service.complete_payment(payment_id, request.provider_payment_id)
        return updated_payment
    except InvalidPaymentStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PaymentCreditingError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{payment_id}/fail", response_model=PaymentResponse)
def fail_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment_repo = PaymentRepository(db)
    wallet_repo = WalletRepository(db)
    package_repo = CreditPackageRepository(db)
    wallet_service = WalletService(wallet_repo)
    payment_service = PaymentService(payment_repo, wallet_service, package_repo)
    
    try:
        payment = payment_service.get_payment(payment_id)
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        updated_payment = payment_service.fail_payment(payment_id)
        return updated_payment
    except InvalidPaymentStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))