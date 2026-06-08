from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.services.payment_service import (
    PaymentService,
    PaymentNotFoundError,
    InvalidPaymentError,
    PaymentVerificationError
)
from app.services.wallet_service import WalletService
from app.repositories.payment_repository import PaymentRepository
from app.repositories.wallet_repository import WalletRepository
from app.models.user import User
from app.models.payment import PaymentStatus


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


class CreatePaymentRequest(BaseModel):
    wallet_id: UUID
    amount: float
    credits: float
    provider: str = "razorpay"
    currency: str = "INR"
    payment_method: Optional[str] = None


class PaymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    wallet_id: UUID
    amount: float
    currency: str
    credits: float
    provider: str
    payment_method: Optional[str]
    provider_order_id: Optional[str]
    provider_payment_id: Optional[str]
    status: PaymentStatus
    failure_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CreatePaymentResponse(BaseModel):
    payment_id: UUID
    razorpay_order_id: Optional[str]
    amount: float
    currency: str


class RazorpayWebhookRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    payment_repo = PaymentRepository(db)
    wallet_repo = WalletRepository(db)
    wallet_service = WalletService(db)
    
    razorpay_client = None
    try:
        import razorpay
        from app.core.config import settings
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            razorpay_client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
    except (ImportError, AttributeError):
        pass
    
    return PaymentService(
        payment_repository=payment_repo,
        wallet_repository=wallet_repo,
        wallet_service=wallet_service,
        razorpay_client=razorpay_client
    )


@router.post("/", response_model=CreatePaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    request: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    try:
        payment = service.create_payment(
            user_id=current_user.id,
            wallet_id=request.wallet_id,
            amount=request.amount,
            credits=request.credits,
            provider=request.provider,
            currency=request.currency,
            payment_method=request.payment_method
        )
        
        return CreatePaymentResponse(
            payment_id=payment.id,
            razorpay_order_id=payment.provider_order_id,
            amount=payment.amount,
            currency=payment.currency
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[PaymentResponse])
def get_user_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    payments = service.get_user_payments(current_user.id, skip, limit)
    return [PaymentResponse.model_validate(p) for p in payments]


@router.get("/wallet/{wallet_id}", response_model=List[PaymentResponse])
def get_wallet_payments(
    wallet_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    payments = service.get_wallet_payments(wallet_id, skip, limit)
    
    for payment in payments:
        if payment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to one or more payments"
            )
    
    return [PaymentResponse.model_validate(p) for p in payments]


@router.get("/pending", response_model=List[PaymentResponse])
def get_pending_payments(
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    payments = service.get_pending_payments()
    
    user_payments = [p for p in payments if p.user_id == current_user.id]
    
    return [PaymentResponse.model_validate(p) for p in user_payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    try:
        payment = service.get_payment(payment_id)
        
        if payment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return PaymentResponse.model_validate(payment)
    except PaymentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/webhook/razorpay", status_code=status.HTTP_200_OK)
async def razorpay_webhook(
    request: RazorpayWebhookRequest,
    service: PaymentService = Depends(get_payment_service)
):
    try:
        payment = service.get_payment_by_order_id(request.razorpay_order_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment with order {request.razorpay_order_id} not found"
            )
        
        completed_payment = service.complete_payment(
            payment_id=payment.id,
            provider_payment_id=request.razorpay_payment_id,
            razorpay_order_id=request.razorpay_order_id,
            razorpay_signature=request.razorpay_signature
        )
        
        return {"status": "success", "payment_id": str(completed_payment.id)}
    except PaymentVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (PaymentNotFoundError, InvalidPaymentError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


