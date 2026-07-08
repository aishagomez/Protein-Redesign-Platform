from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── ExecutionLog ───────────────────────────────────────────────────────────────
class ExecutionLogResponse(BaseModel):
    id: int
    service_execution_id: int
    log_level: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── ServiceExecution ───────────────────────────────────────────────────────────
class ServiceExecutionCreate(BaseModel):
    service_name: str
    tool_id: Optional[int] = None


class ServiceExecutionUpdate(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    log_reference: Optional[str] = None
    finished_at: Optional[datetime] = None


class ServiceExecutionResponse(BaseModel):
    id: int
    pipeline_id: int
    service_name: str
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    log_reference: Optional[str]
    message: Optional[str]
    tool_id: Optional[int]

    model_config = {"from_attributes": True}
