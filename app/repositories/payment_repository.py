from uuid import UUID
from typing import Optional, List, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_payment(
        self,
        user_id: UUID,
        wallet_id: UUID,
        amount: float,
        credits: float,
        provider: str = "razorpay",
        currency: str = "INR",
        payment_method: Optional[str] = None,
        provider_order_id: Optional[str] = None,
        status: PaymentStatus = PaymentStatus.PENDING
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=amount,
            credits=credits,
            provider=provider,
            currency=currency,
            payment_method=payment_method,
            provider_order_id=provider_order_id,
            status=status
        )
        self.db.add(payment)
        try:
            self.db.commit()
            self.db.refresh(payment)
            return payment
        except Exception:
            self.db.rollback()
            raise

    def get_payment_by_id(self, payment_id: UUID) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_payment_by_order_id(self, provider_order_id: str) -> Optional[Payment]:
        return self.db.query(Payment).filter(
            Payment.provider_order_id == provider_order_id
        ).first()

    def get_payment_by_provider_payment_id(self, provider_payment_id: str) -> Optional[Payment]:
        return self.db.query(Payment).filter(
            Payment.provider_payment_id == provider_payment_id
        ).first()

    def get_payments_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_payments_by_wallet(
        self,
        wallet_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.wallet_id == wallet_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_pending_payments(self) -> List[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.status == PaymentStatus.PENDING)
            .order_by(Payment.created_at.asc())
            .all()
        )

    def get_successful_payments_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        return (
            self.db.query(Payment)
            .filter(
                and_(
                    Payment.user_id == user_id,
                    Payment.status == PaymentStatus.SUCCESS
                )
            )
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_payment_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        provider_payment_id: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> Optional[Payment]:
        payment = self.get_payment_by_id(payment_id)
        if payment:
            payment.status = status
            if provider_payment_id:
                payment.provider_payment_id = provider_payment_id
            if failure_reason:
                payment.failure_reason = failure_reason
            try:
                self.db.commit()
                self.db.refresh(payment)
            except Exception:
                self.db.rollback()
                raise
        return payment

    def update_payment(self, payment_id: UUID, **kwargs: Any) -> Optional[Payment]:
        payment = self.get_payment_by_id(payment_id)
        if payment:
            for key, value in kwargs.items():
                if hasattr(payment, key) and value is not None:
                    setattr(payment, key, value)
            try:
                self.db.commit()
                self.db.refresh(payment)
            except Exception:
                self.db.rollback()
                raise
        return payment

    def delete_payment(self, payment_id: UUID) -> bool:
        payment = self.get_payment_by_id(payment_id)
        if payment:
            self.db.delete(payment)
            try:
                self.db.commit()
                return True
            except Exception:
                self.db.rollback()
                raise
        return False

    def get_payments_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        return (
            self.db.query(Payment)
            .filter(
                and_(
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date
                )
            )
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_total_successful_amount_by_user(self, user_id: UUID) -> float:
        result = (
            self.db.query(Payment)
            .filter(
                and_(
                    Payment.user_id == user_id,
                    Payment.status == PaymentStatus.SUCCESS
                )
            )
            .with_entities(Payment.amount)
            .all()
        )
        return sum(amount for amount, in result) if result else 0.0