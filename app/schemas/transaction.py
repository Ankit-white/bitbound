from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreateRequest(BaseModel):
    wallet_id: UUID = Field(..., description="Wallet to create the transaction for")
    amount: float = Field(..., gt=0, description="Transaction amount")
    transaction_type: Literal["credit", "debit"] = Field(
        ...,
        description="Transaction type"
    )
    description: Optional[str] = Field(None, description="Optional transaction description")


class TransactionResponse(BaseModel):
    id: UUID
    wallet_id: UUID
    amount: float
    transaction_type: str
    status: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
    total: int
