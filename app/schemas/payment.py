from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateRequest(BaseModel):
    wallet_id: UUID = Field(..., description="ID of the wallet to credit")
    package_id: UUID = Field(..., description="ID of the credit package to purchase")

    model_config = ConfigDict(from_attributes=True)


class PaymentCompleteRequest(BaseModel):
    provider_payment_id: str = Field(..., min_length=1, description="Payment provider's transaction ID")

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    id: UUID = Field(..., description="Payment unique identifier")
    user_id: UUID = Field(..., description="User who made the payment")
    wallet_id: UUID = Field(..., description="Wallet that received credits")
    amount: float = Field(..., description="Real money amount paid")
    credits: float = Field(..., description="Credits purchased")
    provider: str = Field(..., description="Payment provider (razorpay, stripe, etc.)")
    provider_order_id: str | None = Field(None, description="Provider's order ID")
    provider_payment_id: str | None = Field(None, description="Provider's payment transaction ID")
    status: str = Field(..., description="Payment status (pending, completed, failed)")
    created_at: datetime = Field(..., description="Payment creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponse(BaseModel):
    payments: list[PaymentResponse] = Field(..., description="List of payments")
    total: int = Field(..., description="Total number of payments", ge=0)

    model_config = ConfigDict(from_attributes=True)