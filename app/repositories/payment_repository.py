from uuid import UUID

from sqlalchemy.orm import Session

from app.models.payment import Payment


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
        provider_order_id: str | None = None,
        status: str = "pending"
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=amount,
            credits=credits,
            provider=provider,
            provider_order_id=provider_order_id,
            status=status
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_payment_by_id(self, payment_id: UUID) -> Payment | None:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_payment_by_order_id(self, provider_order_id: str) -> Payment | None:
        return self.db.query(Payment).filter(Payment.provider_order_id == provider_order_id).first()

    def get_payments_by_user(self, user_id: UUID) -> list[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .all()
        )

    def get_payments_by_wallet(self, wallet_id: UUID) -> list[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.wallet_id == wallet_id)
            .order_by(Payment.created_at.desc())
            .all()
        )

    def update_payment_status(
        self,
        payment_id: UUID,
        status: str,
        provider_payment_id: str | None = None
    ) -> Payment | None:
        payment = self.get_payment_by_id(payment_id)
        if not payment:
            return None
        
        payment.status = status
        if provider_payment_id:
            payment.provider_payment_id = provider_payment_id
        
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def delete_payment(self, payment_id: UUID) -> bool:
        payment = self.get_payment_by_id(payment_id)
        if not payment:
            return False
        self.db.delete(payment)
        self.db.commit()
        return True