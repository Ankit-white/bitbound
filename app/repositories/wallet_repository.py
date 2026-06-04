from uuid import UUID

from sqlalchemy.orm import Session

from app.models.wallet import Wallet


class WalletRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_wallet(self, agent_id: UUID, currency: str = "CREDITS") -> Wallet:
        wallet = Wallet(
            agent_id=agent_id,
            balance=0.0,
            currency=currency
        )
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return wallet

    def get_wallet_by_id(self, wallet_id: UUID) -> Wallet | None:
        return self.db.query(Wallet).filter(Wallet.id == wallet_id).first()

    def get_wallet_by_agent(self, agent_id: UUID) -> Wallet | None:
        return self.db.query(Wallet).filter(Wallet.agent_id == agent_id).first()

    def wallet_exists(self, agent_id: UUID) -> bool:
        return self.get_wallet_by_agent(agent_id) is not None

    def update_balance(self, wallet_id: UUID, balance: float) -> Wallet | None:
        wallet = self.get_wallet_by_id(wallet_id)
        if not wallet:
            return None
        wallet.balance = balance
        return wallet

    def delete_wallet(self, wallet_id: UUID) -> bool:
        wallet = self.get_wallet_by_id(wallet_id)
        if not wallet:
            return False
        self.db.delete(wallet)
        self.db.commit()
        return True