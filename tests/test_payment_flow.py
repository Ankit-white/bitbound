from uuid import uuid4

from app.database import SessionLocal
from app.models.payment import PaymentStatus
from app.repositories.agent_repository import AgentRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.agent_service import AgentService
from app.services.payment_service import PaymentService
from app.services.wallet_service import WalletService


def test_payment_listing_and_completion_credits_wallet():
    db_session = SessionLocal()
    user_repo = UserRepository(db_session)
    user = user_repo.create_user(
        name="Payment Test",
        email=f"payment.{uuid4()}@example.com",
        password_hash="hash",
        email_verified=True,
    )

    agent_repo = AgentRepository(db_session)
    wallet_repo = WalletRepository(db_session)
    agent_service = AgentService(agent_repo, wallet_repo)
    payment_service = PaymentService(
        payment_repository=PaymentRepository(db_session),
        wallet_repository=wallet_repo,
        wallet_service=WalletService(db_session),
    )

    try:
        agent = agent_service.create_agent(
            user_id=user.id,
            name="Payment Agent",
            description="Payment smoke test agent",
        )
        wallet = wallet_repo.get_by_agent(agent.id)

        payment = payment_service.create_payment(
            user_id=user.id,
            wallet_id=wallet.id,
            amount=99.0,
            credits=100.0,
            provider="razorpay",
            currency="INR",
        )

        wallet_payments = payment_service.get_wallet_payments(wallet.id)
        assert [p.id for p in wallet_payments] == [payment.id]
        assert payment.status == PaymentStatus.PENDING

        completed_payment = payment_service.complete_payment(
            payment_id=payment.id,
            provider_payment_id="pay_test_123",
        )
        db_session.refresh(wallet)

        assert completed_payment.status == PaymentStatus.SUCCESS
        assert completed_payment.provider_payment_id == "pay_test_123"
        assert wallet.balance == 100.0
    finally:
        user_repo.delete_user(user.id)
        db_session.close()
