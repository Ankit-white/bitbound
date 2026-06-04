from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreateRequest(BaseModel):
    wallet_id: UUID = Field(..., description="ID of the wallet to transact with")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    transaction_type: Literal["credit", "debit"] = Field(..., description="Type of transaction")
    description: str | None = Field(None, max_length=500, description="Transaction description")

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    id: UUID = Field(..., description="Transaction unique identifier")
    wallet_id: UUID = Field(..., description="Associated wallet ID")
    amount: float = Field(..., description="Transaction amount")
    transaction_type: str = Field(..., description="Type of transaction (credit/debit)")
    status: str = Field(..., description="Transaction status (completed/failed/pending)")
    description: str | None = Field(None, description="Transaction description")
    created_at: datetime = Field(..., description="Transaction timestamp")

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse] = Field(..., description="List of transactions")
    total: int = Field(..., description="Total number of transactions", ge=0)

    model_config = ConfigDict(from_attributes=True)