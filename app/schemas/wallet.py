from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WalletCreateRequest(BaseModel):
    agent_id: UUID = Field(..., description="ID of the agent to create wallet for")

    model_config = ConfigDict(from_attributes=True)


class WalletResponse(BaseModel):
    id: UUID = Field(..., description="Wallet unique identifier")
    agent_id: UUID = Field(..., description="Associated agent ID")
    balance: float = Field(..., description="Current wallet balance in CREDITS")
    currency: str = Field(..., description="Currency type (CREDITS)")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class WalletBalanceUpdateRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to credit or debit (must be positive)")

    model_config = ConfigDict(from_attributes=True)