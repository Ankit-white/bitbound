from uuid import UUID
from datetime import datetime
from typing import Optional

from app.repositories.usage_repository import UsageRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.wallet_repository import WalletRepository
from app.models.usage import Usage


class UsageNotFoundError(Exception):
    """Raised when usage record does not exist."""
    pass


class InvalidUsageError(Exception):
    """Raised when usage data is invalid."""
    pass


class AgentNotFoundError(Exception):
    """Raised when agent does not exist."""
    pass


class WalletNotFoundError(Exception):
    """Raised when wallet does not exist."""
    pass


class UsageService:
    def __init__(
        self,
        usage_repository: UsageRepository,
        agent_repository: AgentRepository,
        wallet_repository: WalletRepository
    ):
        self.usage_repository = usage_repository
        self.agent_repository = agent_repository
        self.wallet_repository = wallet_repository

    def create_usage(
        self,
        agent_id: UUID,
        credits_used: float,
        usage_type: str,
        wallet_id: Optional[UUID] = None,
        workflow_execution_id: Optional[UUID] = None,
        description: Optional[str] = None,
        usage_metadata: Optional[dict] = None
    ) -> Usage:
        if credits_used <= 0:
            raise InvalidUsageError("Credits used must be greater than 0")
        
        if not usage_type or not usage_type.strip():
            raise InvalidUsageError("Usage type cannot be empty")
        
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with id {agent_id} does not exist")
        
        if wallet_id:
            wallet = self.wallet_repository.get_wallet_by_id(wallet_id)
            if not wallet:
                raise WalletNotFoundError(f"Wallet with id {wallet_id} does not exist")
        
        return self.usage_repository.create_usage(
            agent_id=agent_id,
            credits_used=credits_used,
            usage_type=usage_type.strip(),
            wallet_id=wallet_id,
            workflow_execution_id=workflow_execution_id,
            description=description,
            usage_metadata=usage_metadata
        )

    def get_usage(self, usage_id: UUID) -> Usage:
        usage = self.usage_repository.get_by_id(usage_id)
        if not usage:
            raise UsageNotFoundError(f"Usage with id {usage_id} not found")
        return usage

    def get_agent_usage(
        self,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[Usage]:
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with id {agent_id} does not exist")
        
        return self.usage_repository.get_by_agent(
            agent_id=agent_id,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )

    def get_wallet_usage(
        self,
        wallet_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Usage]:
        wallet = self.wallet_repository.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet with id {wallet_id} does not exist")
        
        return self.usage_repository.get_by_wallet(wallet_id, skip, limit)

    def get_workflow_execution_usage(
        self,
        workflow_execution_id: UUID
    ) -> Optional[Usage]:
        return self.usage_repository.get_by_workflow_execution(workflow_execution_id)

    def get_total_credits_used(
        self,
        agent_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with id {agent_id} does not exist")
        
        return self.usage_repository.get_total_credits_used(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date
        )

    def get_usage_by_type(
        self,
        agent_id: UUID,
        usage_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        if not usage_type or not usage_type.strip():
            raise InvalidUsageError("Usage type cannot be empty")
        
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with id {agent_id} does not exist")
        
        return self.usage_repository.get_usage_by_type(
            agent_id=agent_id,
            usage_type=usage_type.strip(),
            start_date=start_date,
            end_date=end_date
        )

    def get_recent_usage(
        self,
        agent_id: Optional[UUID] = None,
        limit: int = 20
    ) -> list[Usage]:
        if agent_id:
            agent = self.agent_repository.get_by_id(agent_id)
            if not agent:
                raise AgentNotFoundError(f"Agent with id {agent_id} does not exist")
        
        return self.usage_repository.get_recent_usage(agent_id, limit)

    def get_usage_summary_by_type(
        self,
        agent_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[dict]:
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with id {agent_id} does not exist")
        
        return self.usage_repository.get_usage_summary_by_type(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date
        )

    def get_daily_usage(
        self,
        agent_id: UUID,
        days: int = 30
    ) -> list[dict]:
        if days <= 0:
            raise InvalidUsageError("Days must be greater than 0")
        
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with id {agent_id} does not exist")
        
        return self.usage_repository.get_daily_usage(agent_id, days)

    def delete_usage(self, usage_id: UUID) -> bool:
        usage = self.get_usage(usage_id)
        
        deleted = self.usage_repository.delete_usage(usage_id)
        if not deleted:
            raise UsageNotFoundError(f"Usage with id {usage_id} not found")
        
        return True