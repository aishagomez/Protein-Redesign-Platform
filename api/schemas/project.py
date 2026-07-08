from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    group_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[int] = None


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    group_id: Optional[int] = None
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
