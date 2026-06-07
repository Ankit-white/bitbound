from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UsageCreateRequest(BaseModel):
    agent_id: UUID
    wallet_id: Optional[UUID] = None
    workflow_execution_id: Optional[UUID] = None
    credits_used: float = Field(..., ge=0)
    usage_type: str
    description: Optional[str] = None
    usage_metadata: Optional[dict[str, Any]] = None


class UsageResponse(BaseModel):
    id: UUID
    agent_id: UUID
    wallet_id: Optional[UUID] = None
    workflow_execution_id: Optional[UUID] = None
    credits_used: float
    usage_type: str
    description: Optional[str] = None
    usage_metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
