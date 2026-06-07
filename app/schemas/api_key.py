from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., description="API key display name")
    agent_id: Optional[UUID] = Field(None, description="Optional agent scope")
    expires_at: Optional[datetime] = Field(None, description="Optional expiry timestamp")


class APIKeyResponse(BaseModel):
    id: UUID
    user_id: UUID
    agent_id: Optional[UUID] = None
    name: str
    prefix: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class APIKeyCreateResponse(APIKeyResponse):
    api_key: str = Field(..., description="Plain API key, returned only once")
