from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user
from schemas.group import GroupCreate, GroupResponse, MembershipCreate, MembershipUpdate
from services.profile import (
    list_groups as profile_list_groups,
    create_group as profile_create_group,
    get_group as profile_get_group,
    add_member as profile_add_member,
    update_member as profile_update_member,
    remove_member as profile_remove_member,
)
from models import User

router = APIRouter(prefix="/groups", tags=["Grupos"])


@router.get("", response_model=list[GroupResponse])
def list_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return profile_list_groups(db, current_user)


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_new_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return profile_create_group(db, current_user, data)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group_detail(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return profile_get_group(db, group_id, current_user)


@router.post("/{group_id}/members", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def add_group_member(
    group_id: int,
    data: MembershipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return profile_add_member(db, group_id, current_user, data)


@router.patch("/{group_id}/members/{user_id}", response_model=GroupResponse)
def change_member_role(
    group_id: int,
    user_id: int,
    data: MembershipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return profile_update_member(db, group_id, user_id, current_user, data)


@router.delete("/{group_id}/members/{user_id}", response_model=GroupResponse)
def delete_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return profile_remove_member(db, group_id, user_id, current_user)
