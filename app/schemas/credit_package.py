from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreditPackageCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Package name")
    description: str | None = Field(None, max_length=1000, description="Package description")
    price: float = Field(..., gt=0, description="Package price in real money")
    credits: float = Field(..., gt=0, description="Number of credits to purchase")

    model_config = ConfigDict(from_attributes=True)


class CreditPackageResponse(BaseModel):
    id: UUID = Field(..., description="Package unique identifier")
    name: str = Field(..., description="Package name")
    description: str | None = Field(None, description="Package description")
    price: float = Field(..., description="Package price in real money")
    credits: float = Field(..., description="Number of credits to purchase")
    is_active: bool = Field(..., description="Whether package is available for purchase")
    created_at: datetime = Field(..., description="Package creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class CreditPackageListResponse(BaseModel):
    packages: list[CreditPackageResponse] = Field(..., description="List of credit packages")
    total: int = Field(..., description="Total number of packages", ge=0)

    model_config = ConfigDict(from_attributes=True)