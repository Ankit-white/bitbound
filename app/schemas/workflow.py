from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowCreateRequest(BaseModel):
    agent_id: UUID
    name: str
    description: Optional[str] = None
    n8n_workflow_id: Optional[str] = None
    webhook_url: Optional[str] = None
    execution_cost: float = Field(default=1.0, ge=0)


class WorkflowResponse(BaseModel):
    id: UUID
    agent_id: UUID
    name: str
    description: Optional[str] = None
    n8n_workflow_id: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: bool
    execution_cost: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
