from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkflowExecutionCreateRequest(BaseModel):
    workflow_id: UUID
    agent_id: UUID
    input_payload: Optional[dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    agent_id: UUID
    status: str
    n8n_execution_id: Optional[str] = None
    input_payload: Optional[dict[str, Any]] = None
    output_payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    credits_consumed: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
