from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.repositories.wallet_repository import WalletRepository


class WalletAlreadyExistsError(Exception):
    pass


class WalletNotFoundError(Exception):
    pass


class InsufficientBalanceError(Exception):
    pass


class InvalidAmountError(Exception):
    pass


class TransactionCreationError(Exception):
    pass


class WalletService:
    def __init__(self, wallet_repo: WalletRepository):
        self.wallet_repo = wallet_repo

    def create_wallet(self, agent_id: UUID) -> Wallet:
        if self.wallet_repo.wallet_exists(agent_id):
            raise WalletAlreadyExistsError(f"Wallet already exists for agent {agent_id}")
        
        return self.wallet_repo.create_wallet(agent_id, "CREDITS")

    def get_wallet(self, wallet_id: UUID) -> Wallet:
        wallet = self.wallet_repo.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet {wallet_id} not found")
        return wallet

    def get_wallet_by_agent(self, agent_id: UUID) -> Wallet:
        wallet = self.wallet_repo.get_wallet_by_agent(agent_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet not found for agent {agent_id}")
        return wallet

    def credit_wallet(self, wallet_id: UUID, amount: float, description: str = "Wallet credit") -> Wallet:
        if amount <= 0:
            raise InvalidAmountError(f"Credit amount must be positive. Got: {amount}")
        
        try:
            wallet = self.get_wallet(wallet_id)
            new_balance = wallet.balance + amount
            
            wallet.balance = new_balance
            
            transaction = Transaction(
                wallet_id=wallet_id,
                amount=amount,
                transaction_type="credit",
                description=description,
                status="completed"
            )
            
            self.wallet_repo.db.add(transaction)
            self.wallet_repo.db.commit()
            self.wallet_repo.db.refresh(wallet)
            
            return wallet
            
        except SQLAlchemyError as e:
            self.wallet_repo.db.rollback()
            raise TransactionCreationError(f"Failed to process credit: {str(e)}")

    def debit_wallet(self, wallet_id: UUID, amount: float, description: str = "Wallet debit") -> Wallet:
        if amount <= 0:
            raise InvalidAmountError(f"Debit amount must be positive. Got: {amount}")
        
        try:
            wallet = self.get_wallet(wallet_id)
            
            if wallet.balance < amount:
                raise InsufficientBalanceError(
                    f"Insufficient balance. Available: {wallet.balance}, Required: {amount}"
                )
            
            new_balance = wallet.balance - amount
            wallet.balance = new_balance
            
            transaction = Transaction(
                wallet_id=wallet_id,
                amount=amount,
                transaction_type="debit",
                description=description,
                status="completed"
            )
            
            self.wallet_repo.db.add(transaction)
            self.wallet_repo.db.commit()
            self.wallet_repo.db.refresh(wallet)
            
            return wallet
            
        except SQLAlchemyError as e:
            self.wallet_repo.db.rollback()
            raise TransactionCreationError(f"Failed to process debit: {str(e)}")