from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CapabilityCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    credit_cost: float = Field(default=0.0, ge=0)
    is_active: bool = True


class CapabilityResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    credit_cost: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
