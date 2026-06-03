from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Agent name")
    description: str | None = Field(None, max_length=1000, description="Agent description")


class AgentResponse(BaseModel):
    id: UUID = Field(..., description="Unique agent identifier")
    user_id: UUID = Field(..., description="Owner user ID")
    name: str = Field(..., description="Agent name")
    description: str | None = Field(None, description="Agent description")
    status: str = Field(..., description="Agent status (active, paused, deleted)")
    monthly_budget: float = Field(..., description="Monthly budget limit in credits")
    credits_used: float = Field(..., description="Credits used in current month")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    agents: list[AgentResponse] = Field(..., description="List of agents")
    total: int = Field(..., description="Total number of agents", ge=0)