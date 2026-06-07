from uuid import UUID
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.wallet_repository import WalletRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.agent_repository import AgentRepository
from app.models.wallet import Wallet
from app.models.transaction import Transaction


class WalletNotFoundError(Exception):
    """Raised when wallet does not exist."""
    pass


class WalletAccessDeniedError(Exception):
    """Raised when user does not have access to the wallet."""
    pass


class WalletAlreadyExistsError(Exception):
    """Raised when wallet already exists for the agent."""
    pass


class InvalidAmountError(Exception):
    """Raised when amount is invalid (zero or negative)."""
    pass


class InsufficientBalanceError(Exception):
    """Raised when wallet balance is insufficient for debit."""
    pass


class WalletService:
    def __init__(self, db: Session):
        self.db = db
        self.wallet_repo = WalletRepository(db)
        self.transaction_repo = TransactionRepository(db)
        self.agent_repo = AgentRepository(db)

    def _verify_ownership(self, wallet_id: UUID, user_id: UUID) -> Wallet:
        """
        Verify that the user owns the wallet.
        
        Args:
            wallet_id: Wallet ID to verify
            user_id: User ID to check ownership against
        
        Returns:
            Wallet object if ownership is verified
        
        Raises:
            WalletNotFoundError: If wallet not found
            WalletAccessDeniedError: If user does not own the wallet
        """
        wallet = self.wallet_repo.get_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet {wallet_id} not found")
        
        agent = self.agent_repo.get_by_id(wallet.agent_id)
        if not agent:
            raise WalletNotFoundError(f"Agent {wallet.agent_id} not found")
        
        if agent.user_id != user_id:
            raise WalletAccessDeniedError("Access denied to this wallet")
        
        return wallet

    def create_wallet(self, agent_id: UUID) -> Wallet:
        """
        Create a new wallet for an agent.
        
        Args:
            agent_id: Agent ID to create wallet for
        
        Returns:
            Created Wallet object
        
        Raises:
            WalletAlreadyExistsError: If wallet already exists for the agent
        """
        existing_wallet = self.wallet_repo.get_by_agent(agent_id)
        if existing_wallet:
            raise WalletAlreadyExistsError(f"Wallet already exists for agent {agent_id}")
        
        wallet = self.wallet_repo.create_wallet(agent_id=agent_id)
        return wallet

    def get_wallet(self, wallet_id: UUID, user_id: UUID) -> Wallet:
        """
        Get wallet by ID with ownership verification.
        
        Args:
            wallet_id: Wallet ID to retrieve
            user_id: User ID to verify ownership
        
        Returns:
            Wallet object
        
        Raises:
            WalletNotFoundError: If wallet not found
            WalletAccessDeniedError: If user does not own the wallet
        """
        return self._verify_ownership(wallet_id, user_id)

    def get_wallet_by_agent(self, agent_id: UUID, user_id: UUID) -> Wallet:
        """
        Get wallet by agent ID with ownership verification.
        
        Args:
            agent_id: Agent ID to get wallet for
            user_id: User ID to verify ownership
        
        Returns:
            Wallet object
        
        Raises:
            WalletNotFoundError: If wallet or agent not found
            WalletAccessDeniedError: If user does not own the agent
        """
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise WalletNotFoundError(f"Agent {agent_id} not found")
        
        if agent.user_id != user_id:
            raise WalletAccessDeniedError("Access denied to this agent")
        
        wallet = self.wallet_repo.get_by_agent(agent_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet for agent {agent_id} not found")
        
        return wallet

    def credit_wallet(
        self,
        wallet_id: UUID,
        user_id: UUID,
        amount: float,
        description: str = "Credit"
    ) -> Wallet:
        """
        Credit (add) funds to a wallet.
        
        Args:
            wallet_id: Wallet ID to credit
            user_id: User ID to verify ownership
            amount: Amount to credit (must be > 0)
            description: Transaction description
        
        Returns:
            Updated Wallet object
        
        Raises:
            WalletNotFoundError: If wallet not found
            WalletAccessDeniedError: If user does not own the wallet
            InvalidAmountError: If amount is not greater than 0
        """
        if amount <= 0:
            raise InvalidAmountError(f"Amount must be greater than 0. Got: {amount}")
        
        wallet = self._verify_ownership(wallet_id, user_id)
        
        try:
            wallet.credit(amount)
            
            self.transaction_repo.create_transaction(
                wallet_id=wallet_id,
                amount=amount,
                transaction_type="credit",
                description=description
            )
            
            self.db.commit()
            self.db.refresh(wallet)
            
            return wallet
        except Exception:
            self.db.rollback()
            raise

    def debit_wallet(
        self,
        wallet_id: UUID,
        user_id: UUID,
        amount: float,
        description: str = "Debit"
    ) -> Wallet:
        """
        Debit (subtract) funds from a wallet.
        
        Args:
            wallet_id: Wallet ID to debit
            user_id: User ID to verify ownership
            amount: Amount to debit (must be > 0)
            description: Transaction description
        
        Returns:
            Updated Wallet object
        
        Raises:
            WalletNotFoundError: If wallet not found
            WalletAccessDeniedError: If user does not own the wallet
            InvalidAmountError: If amount is not greater than 0
            InsufficientBalanceError: If wallet has insufficient balance
        """
        if amount <= 0:
            raise InvalidAmountError(f"Amount must be greater than 0. Got: {amount}")
        
        wallet = self._verify_ownership(wallet_id, user_id)
        
        if not wallet.has_sufficient_balance(amount):
            raise InsufficientBalanceError(
                f"Insufficient balance. Required: {amount}, Available: {wallet.balance}"
            )
        
        try:
            wallet.debit(amount)
            
            self.transaction_repo.create_transaction(
                wallet_id=wallet_id,
                amount=amount,
                transaction_type="debit",
                description=description
            )
            
            self.db.commit()
            self.db.refresh(wallet)
            
            return wallet
        except Exception:
            self.db.rollback()
            raise

    def get_wallet_transactions(
        self,
        wallet_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """
        Get paginated transaction history for a wallet.
        
        Args:
            wallet_id: Wallet ID to get transactions for
            user_id: User ID to verify ownership
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of Transaction objects
        
        Raises:
            WalletNotFoundError: If wallet not found
            WalletAccessDeniedError: If user does not own the wallet
        """
        self._verify_ownership(wallet_id, user_id)
        
        return self.transaction_repo.get_by_wallet(
            wallet_id=wallet_id,
            skip=skip,
            limit=limit
        )

    def get_wallet_balance(self, wallet_id: UUID, user_id: UUID) -> float:
        """
        Get current wallet balance.
        
        Args:
            wallet_id: Wallet ID to get balance for
            user_id: User ID to verify ownership
        
        Returns:
            Current wallet balance
        
        Raises:
            WalletNotFoundError: If wallet not found
            WalletAccessDeniedError: If user does not own the wallet
        """
        wallet = self._verify_ownership(wallet_id, user_id)
        return wallet.balance

    def transfer_between_wallets(
        self,
        from_wallet_id: UUID,
        to_wallet_id: UUID,
        user_id: UUID,
        amount: float,
        description: str = "Transfer"
    ) -> tuple[Wallet, Wallet]:
        """
        Transfer funds between two wallets.
        
        Args:
            from_wallet_id: Source wallet ID
            to_wallet_id: Destination wallet ID
            user_id: User ID to verify ownership of source wallet
            amount: Amount to transfer
            description: Transaction description
        
        Returns:
            Tuple of (updated from_wallet, updated to_wallet)
        
        Raises:
            WalletNotFoundError: If either wallet not found
            WalletAccessDeniedError: If user does not own source wallet
            InvalidAmountError: If amount is not greater than 0
            InsufficientBalanceError: If source wallet has insufficient balance
        """
        if amount <= 0:
            raise InvalidAmountError(f"Amount must be greater than 0. Got: {amount}")
        
        from_wallet = self._verify_ownership(from_wallet_id, user_id)
        
        to_wallet = self.wallet_repo.get_by_id(to_wallet_id)
        if not to_wallet:
            raise WalletNotFoundError(f"Wallet {to_wallet_id} not found")
        
        if not from_wallet.has_sufficient_balance(amount):
            raise InsufficientBalanceError(
                f"Insufficient balance. Required: {amount}, Available: {from_wallet.balance}"
            )
        
        try:
            from_wallet.debit(amount)
            to_wallet.credit(amount)
            
            self.transaction_repo.create_transaction(
                wallet_id=from_wallet_id,
                amount=amount,
                transaction_type="debit",
                description=f"{description} to {to_wallet_id}"
            )
            
            self.transaction_repo.create_transaction(
                wallet_id=to_wallet_id,
                amount=amount,
                transaction_type="credit",
                description=f"{description} from {from_wallet_id}"
            )
            
            self.db.commit()
            self.db.refresh(from_wallet)
            self.db.refresh(to_wallet)
            
            return from_wallet, to_wallet
        except Exception:
            self.db.rollback()
            raise