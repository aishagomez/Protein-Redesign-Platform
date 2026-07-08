from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models import WorkGroup, GroupMembership, User
from schemas.group import GroupCreate
from services.auth import is_admin_user_id


OWNER_ROLE = "owner"
ADMIN_ROLE = "admin"
MEMBER_ROLE = "member"


def create_group(db: Session, data: GroupCreate, creator_id: int) -> WorkGroup:
    group = WorkGroup(name=data.name, description=data.description, created_by_user_id=creator_id)
    db.add(group)
    db.commit()
    # add membership for creator as owner
    membership = GroupMembership(group_id=group.id, user_id=creator_id, role=OWNER_ROLE)
    db.add(membership)
    db.commit()
    db.refresh(group)
    return group


def get_groups_for_user(db: Session, user_id: int) -> List[WorkGroup]:
    # return groups where user is a member or admin global
    if is_admin_user_id(db, user_id):
        return db.query(WorkGroup).order_by(WorkGroup.created_at.desc()).all()
    return (
        db.query(WorkGroup)
        .join(GroupMembership, GroupMembership.group_id == WorkGroup.id)
        .filter(GroupMembership.user_id == user_id)
        .order_by(WorkGroup.created_at.desc())
        .all()
    )


def get_group(db: Session, group_id: int) -> WorkGroup:
    group = db.query(WorkGroup).filter(WorkGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado")
    return group


def add_member(db: Session, group_id: int, user: User, role: str = MEMBER_ROLE) -> GroupMembership:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Usuario inactivo")
    existing = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id, GroupMembership.user_id == user.id)
        .first()
    )
    if existing:
        existing.role = role
        db.commit()
        return existing

    membership = GroupMembership(group_id=group_id, user_id=user.id, role=role)
    db.add(membership)
    db.commit()
    return membership


def update_member_role(db: Session, group_id: int, user_id: int, new_role: str):
    membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id, GroupMembership.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membresía no encontrada")
    membership.role = new_role
    db.commit()
    return membership


def remove_member(db: Session, group_id: int, user_id: int):
    membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id, GroupMembership.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membresía no encontrada")

    # prevent removing last owner
    if membership.role == OWNER_ROLE:
        owners_count = (
            db.query(GroupMembership)
            .filter(GroupMembership.group_id == group_id, GroupMembership.role == OWNER_ROLE)
            .count()
        )
        if owners_count <= 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El grupo debe tener al menos un owner")

    db.delete(membership)
    db.commit()
    return None
