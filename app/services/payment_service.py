from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.models.payment import Payment, PaymentStatus
from app.repositories.credit_package_repository import CreditPackageRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.wallet_service import WalletService


class PaymentNotFoundError(Exception):
    pass


class InvalidPaymentError(Exception):
    pass


class InvalidPaymentStatusError(Exception):
    pass


class PaymentCreditingError(Exception):
    pass


class PaymentVerificationError(Exception):
    pass


class PackageNotFoundError(Exception):
    pass


class PaymentService:
    def __init__(
        self,
        payment_repository: PaymentRepository | None = None,
        wallet_repository: WalletRepository | None = None,
        wallet_service: WalletService | None = None,
        package_repo: CreditPackageRepository | None = None,
        razorpay_client=None,
        payment_repo: PaymentRepository | None = None,
    ):
        self.payment_repo = payment_repository or payment_repo
        if self.payment_repo is None:
            raise ValueError("payment_repository is required")

        self.wallet_repository = wallet_repository
        self.wallet_service = wallet_service
        self.package_repo = package_repo
        self.razorpay_client = razorpay_client

    def create_payment(
        self,
        user_id: UUID,
        wallet_id: UUID,
        amount: float | None = None,
        credits: float | None = None,
        provider: str = "razorpay",
        currency: str = "INR",
        payment_method: str | None = None,
        package_id: UUID | None = None,
    ) -> Payment:
        if package_id is not None:
            amount, credits = self._resolve_package(package_id)

        if amount is None or amount <= 0:
            raise InvalidPaymentError("Payment amount must be greater than 0")
        if credits is None or credits <= 0:
            raise InvalidPaymentError("Payment credits must be greater than 0")

        self._verify_wallet_owner(wallet_id, user_id)

        payment = self.payment_repo.create_payment(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=amount,
            credits=credits,
            provider=provider,
            currency=currency,
            payment_method=payment_method,
            status=PaymentStatus.PENDING,
        )

        provider_order_id = self._create_provider_order(payment)
        if provider_order_id:
            payment = self.payment_repo.update_payment(
                payment.id,
                provider_order_id=provider_order_id,
            )

        return payment

    def _resolve_package(self, package_id: UUID) -> tuple[float, float]:
        if not self.package_repo:
            raise PackageNotFoundError("Credit package repository is not configured")

        package = self.package_repo.get_package_by_id(package_id)
        if not package:
            raise PackageNotFoundError(f"Credit package {package_id} not found")
        if not package.is_active:
            raise PackageNotFoundError(f"Credit package {package_id} is not active")

        return package.price, package.credits

    def _verify_wallet_owner(self, wallet_id: UUID, user_id: UUID) -> None:
        if self.wallet_service:
            self.wallet_service.get_wallet(wallet_id, user_id)
            return

        if not self.wallet_repository:
            return

        wallet = self.wallet_repository.get_by_id(wallet_id)
        if not wallet:
            raise InvalidPaymentError(f"Wallet {wallet_id} not found")
        if wallet.agent and wallet.agent.user_id != user_id:
            raise InvalidPaymentError("Access denied to this wallet")

    def _create_provider_order(self, payment: Payment) -> str | None:
        if not self.razorpay_client:
            return None

        try:
            order = self.razorpay_client.order.create(
                data={
                    "amount": int(round(payment.amount * 100)),
                    "currency": payment.currency,
                    "receipt": str(payment.id),
                    "payment_capture": 1,
                }
            )
            return order.get("id")
        except Exception as exc:
            raise InvalidPaymentError(f"Failed to create Razorpay order: {exc}") from exc

    def get_payment(self, payment_id: UUID) -> Payment:
        payment = self.payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")
        return payment

    def get_payment_by_order_id(self, provider_order_id: str) -> Payment | None:
        return self.payment_repo.get_payment_by_order_id(provider_order_id)

    def get_payment_by_provider_payment_id(self, provider_payment_id: str) -> Payment | None:
        return self.payment_repo.get_payment_by_provider_payment_id(provider_payment_id)

    def get_user_payments(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        return self.payment_repo.get_payments_by_user(user_id, skip, limit)

    def get_wallet_payments(
        self,
        wallet_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        return self.payment_repo.get_payments_by_wallet(wallet_id, skip, limit)

    def get_pending_payments(self) -> list[Payment]:
        return self.payment_repo.get_pending_payments()

    def complete_payment(
        self,
        payment_id: UUID,
        provider_payment_id: str,
        razorpay_order_id: str | None = None,
        razorpay_signature: str | None = None,
    ) -> Payment:
        payment = self.get_payment(payment_id)

        if payment.status != PaymentStatus.PENDING:
            raise InvalidPaymentStatusError(
                f"Cannot complete payment with status {payment.status}. Expected: pending"
            )

        if razorpay_order_id and razorpay_signature:
            self._verify_provider_signature(
                razorpay_order_id=razorpay_order_id,
                provider_payment_id=provider_payment_id,
                razorpay_signature=razorpay_signature,
            )

        db = self.payment_repo.db
        try:
            if self.wallet_service:
                self.wallet_service.credit_wallet(
                    wallet_id=payment.wallet_id,
                    user_id=payment.user_id,
                    amount=payment.credits,
                    description=f"Payment {payment_id} completed",
                )

            updated_payment = self.payment_repo.update_payment_status(
                payment_id=payment_id,
                status=PaymentStatus.SUCCESS,
                provider_payment_id=provider_payment_id,
            )
            if not updated_payment:
                raise PaymentNotFoundError(f"Payment {payment_id} not found")
            return updated_payment
        except SQLAlchemyError as exc:
            db.rollback()
            raise PaymentCreditingError(f"Failed to complete payment {payment_id}: {exc}") from exc

    def _verify_provider_signature(
        self,
        razorpay_order_id: str,
        provider_payment_id: str,
        razorpay_signature: str,
    ) -> None:
        if not self.razorpay_client:
            raise PaymentVerificationError("Razorpay client is not configured")

        try:
            self.razorpay_client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": provider_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )
        except Exception as exc:
            raise PaymentVerificationError(f"Payment signature verification failed: {exc}") from exc

    def fail_payment(self, payment_id: UUID, reason: str | None = None) -> Payment:
        payment = self.get_payment(payment_id)
        if payment.status != PaymentStatus.PENDING:
            raise InvalidPaymentStatusError(
                f"Cannot fail payment with status {payment.status}. Expected: pending"
            )

        updated_payment = self.payment_repo.update_payment_status(
            payment_id=payment_id,
            status=PaymentStatus.FAILED,
            failure_reason=reason,
        )
        if not updated_payment:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")
        return updated_payment

    def refund_payment(self, payment_id: UUID, reason: str | None = None) -> Payment:
        payment = self.get_payment(payment_id)
        if payment.status not in (PaymentStatus.SUCCESS, PaymentStatus.FAILED):
            raise InvalidPaymentStatusError(
                f"Cannot refund payment with status {payment.status}"
            )

        updated_payment = self.payment_repo.update_payment_status(
            payment_id=payment_id,
            status=PaymentStatus.REFUNDED,
            failure_reason=reason,
        )
        if not updated_payment:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")
        return updated_payment
