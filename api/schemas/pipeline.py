from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime


class PipelineCreate(BaseModel):
    version: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class PipelineUpdate(BaseModel):
    version: Optional[str] = None
    status: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class PipelineResponse(BaseModel):
    id: int
    project_id: int
    version: Optional[str]
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    parameters: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}
