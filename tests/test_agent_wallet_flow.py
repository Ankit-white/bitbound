from uuid import uuid4

from app.database import SessionLocal
from app.models.wallet import Wallet
from app.repositories.agent_repository import AgentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.agent_service import AgentService


def test_create_agent_creates_wallet():
    db_session = SessionLocal()
    user_repo = UserRepository(db_session)
    user = user_repo.create_user(
        name="Agent Wallet Test",
        email=f"agent.wallet.{uuid4()}@example.com",
        password_hash="hash",
        email_verified=True,
    )
    agent_repo = AgentRepository(db_session)
    wallet_repo = WalletRepository(db_session)
    service = AgentService(agent_repo, wallet_repo)

    try:
        agent = service.create_agent(
            user_id=user.id,
            name="Research Agent",
            description="Finds information",
        )

        wallet = (
            db_session.query(Wallet)
            .filter(Wallet.agent_id == agent.id)
            .first()
        )

        assert wallet is not None
        assert wallet.balance == 0.0
        assert wallet.currency == "CREDITS"
    finally:
        user_repo.delete_user(user.id)
        db_session.close()
