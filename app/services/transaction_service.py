from uuid import UUID

from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository


class TransactionNotFoundError(Exception):
    pass


class WalletNotFoundError(Exception):
    pass


class InvalidTransactionTypeError(Exception):
    pass


class InvalidAmountError(Exception):
    pass


class TransactionService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        wallet_repo: WalletRepository
    ):
        self.transaction_repo = transaction_repo
        self.wallet_repo = wallet_repo

    def create_transaction(
        self,
        wallet_id: UUID,
        amount: float,
        transaction_type: str,
        description: str | None = None
    ) -> Transaction:
        if amount <= 0:
            raise InvalidAmountError(f"Amount must be greater than 0. Got: {amount}")
        
        if transaction_type not in ["credit", "debit"]:
            raise InvalidTransactionTypeError(
                f"Transaction type must be 'credit' or 'debit'. Got: {transaction_type}"
            )
        
        wallet = self.wallet_repo.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet {wallet_id} not found")
        
        transaction = self.transaction_repo.create_transaction(
            wallet_id=wallet_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            status="completed"
        )
        
        return transaction

    def get_transaction(self, transaction_id: UUID) -> Transaction:
        transaction = self.transaction_repo.get_transaction_by_id(transaction_id)
        if not transaction:
            raise TransactionNotFoundError(f"Transaction {transaction_id} not found")
        return transaction

    def get_wallet_transactions(self, wallet_id: UUID) -> list[Transaction]:
        return self.transaction_repo.get_transactions_by_wallet(wallet_id)

    def get_all_transactions(self) -> list[Transaction]:
        return self.transaction_repo.get_all_transactions()