from pydantic import BaseModel
from datetime import datetime


class GroupCreate(BaseModel):
    name: str
    description: str | None = None


class MembershipCreate(BaseModel):
    identifier: str
    role: str = "member"


class MembershipUpdate(BaseModel):
    role: str


class GroupMemberResponse(BaseModel):
    user_id: int
    username: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    role: str
    created_at: datetime


class GroupResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_by_user_id: int
    current_user_role: str
    created_at: datetime
    members: list[GroupMemberResponse] = []


class ProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    display_name: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
    groups: list[GroupResponse] = []
    project_count: int = 0
