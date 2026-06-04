from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.models.payment import Payment
from app.models.transaction import Transaction
from app.repositories.credit_package_repository import CreditPackageRepository
from app.repositories.payment_repository import PaymentRepository
from app.services.wallet_service import WalletService


class PaymentNotFoundError(Exception):
    pass


class InvalidPaymentStatusError(Exception):
    pass


class PaymentCreditingError(Exception):
    pass


class PackageNotFoundError(Exception):
    pass


class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        wallet_service: WalletService,
        package_repo: CreditPackageRepository
    ):
        self.payment_repo = payment_repo
        self.wallet_service = wallet_service
        self.package_repo = package_repo

    def create_payment(
        self,
        user_id: UUID,
        wallet_id: UUID,
        package_id: UUID
    ) -> Payment:
        package = self.package_repo.get_package_by_id(package_id)
        if not package:
            raise PackageNotFoundError(f"Credit package {package_id} not found")
        
        if not package.is_active:
            raise PackageNotFoundError(f"Credit package {package_id} is not active")
        
        payment = self.payment_repo.create_payment(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=package.price,
            credits=package.credits,
            provider="razorpay",
            status="pending"
        )
        
        return payment

    def get_payment(self, payment_id: UUID) -> Payment:
        payment = self.payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")
        return payment

    def get_user_payments(self, user_id: UUID) -> list[Payment]:
        return self.payment_repo.get_payments_by_user(user_id)

    def get_wallet_payments(self, wallet_id: UUID) -> list[Payment]:
        return self.payment_repo.get_payments_by_wallet(wallet_id)

    def complete_payment(self, payment_id: UUID, provider_payment_id: str) -> Payment:
        payment = self.get_payment(payment_id)
        
        if payment.status != "pending":
            raise InvalidPaymentStatusError(
                f"Cannot complete payment with status {payment.status}. Expected: pending"
            )
        
        db = self.payment_repo.db
        
        try:
            wallet = self.wallet_service.get_wallet(payment.wallet_id)
            new_balance = wallet.balance + payment.credits
            wallet.balance = new_balance
            
            transaction = Transaction(
                wallet_id=payment.wallet_id,
                amount=payment.credits,
                transaction_type="credit",
                description=f"Payment {payment_id} completed. Real amount paid: {payment.amount}",
                status="completed"
            )
            
            payment.status = "completed"
            payment.provider_payment_id = provider_payment_id
            
            db.add(transaction)
            db.commit()
            db.refresh(payment)
            
            return payment
            
        except SQLAlchemyError as e:
            db.rollback()
            raise PaymentCreditingError(f"Failed to complete payment {payment_id}: {str(e)}")

    def fail_payment(self, payment_id: UUID) -> Payment:
        payment = self.get_payment(payment_id)
        
        if payment.status != "pending":
            raise InvalidPaymentStatusError(
                f"Cannot fail payment with status {payment.status}. Expected: pending"
            )
        
        return self.payment_repo.update_payment_status(
            payment_id=payment_id,
            status="failed"
        )