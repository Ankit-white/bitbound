from uuid import UUID

from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(
        self,
        wallet_id: UUID,
        amount: float,
        transaction_type: str,
        description: str | None = None,
        status: str = "completed"
    ) -> Transaction:
        transaction = Transaction(
            wallet_id=wallet_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            status=status
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_transaction_by_id(self, transaction_id: UUID) -> Transaction | None:
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()

    def get_transactions_by_wallet(self, wallet_id: UUID) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
            .all()
        )

    def get_all_transactions(self) -> list[Transaction]:
        return self.db.query(Transaction).order_by(Transaction.created_at.desc()).all()

    def delete_transaction(self, transaction_id: UUID) -> bool:
        transaction = self.get_transaction_by_id(transaction_id)
        if not transaction:
            return False
        self.db.delete(transaction)
        self.db.commit()
        return True