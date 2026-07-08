import os
import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import GroupMembership, Project, User, WorkGroup
from schemas.group import GroupCreate, MembershipCreate, MembershipUpdate
from schemas.user import UserProfileUpdate
from services.access import can_manage_group, can_own_group, group_role

PERSISTENT_STORAGE_ROOT = Path(os.environ.get("PERSISTENT_STORAGE_ROOT", "/persistent_storage")).resolve()
AVATAR_ROOT = (PERSISTENT_STORAGE_ROOT / "avatars").resolve()
ALLOWED_AVATAR_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024
GROUP_ROLES = {"owner", "admin", "member"}


def serialize_profile(db: Session, user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "display_name": user.display_name,
        "avatar_url": avatar_url(user),
        "is_active": user.is_active,
        "created_at": user.created_at,
        "groups": list_groups(db, user),
        "project_count": db.query(func.count(Project.id)).filter(Project.user_id == user.id).scalar() or 0,
    }


def update_profile(db: Session, user: User, data: UserProfileUpdate) -> dict:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return serialize_profile(db, user)


def save_avatar(db: Session, user: User, upload: UploadFile) -> dict:
    filename = Path(upload.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_AVATAR_SUFFIXES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de imagen no permitido")

    user_dir = AVATAR_ROOT / f"user_{user.id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    destination = user_dir / f"avatar{suffix}"

    bytes_written = 0
    with destination.open("wb") as buffer:
        while chunk := upload.file.read(1024 * 1024):
            bytes_written += len(chunk)
            if bytes_written > MAX_AVATAR_BYTES:
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="La imagen supera 2 MB")
            buffer.write(chunk)

    for stale in user_dir.glob("avatar.*"):
        if stale != destination:
            stale.unlink(missing_ok=True)

    user.avatar_path = str(destination)
    db.commit()
    db.refresh(user)
    return serialize_profile(db, user)


def avatar_file(user: User) -> Path:
    if not user.avatar_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar no encontrado")
    path = Path(user.avatar_path).resolve()
    if AVATAR_ROOT != path and AVATAR_ROOT not in path.parents:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Avatar fuera del almacenamiento permitido")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar no encontrado")
    return path


def deactivate_account(db: Session, user: User) -> None:
    user.is_active = False
    db.commit()


def create_group(db: Session, user: User, data: GroupCreate) -> dict:
    group = WorkGroup(name=data.name, description=data.description, created_by_user_id=user.id)
    db.add(group)
    db.flush()
    db.add(GroupMembership(group_id=group.id, user_id=user.id, role="owner"))
    db.commit()
    db.refresh(group)
    return serialize_group(db, group, user.id)


def list_groups(db: Session, user: User) -> list[dict]:
    query = db.query(WorkGroup).join(GroupMembership).filter(GroupMembership.user_id == user.id)
    if user.role == "admin":
        query = db.query(WorkGroup)
    return [serialize_group(db, group, user.id) for group in query.order_by(WorkGroup.created_at.desc()).all()]


def get_group(db: Session, group_id: int, user: User) -> dict:
    group = _group_visible(db, group_id, user)
    return serialize_group(db, group, user.id)


def add_member(db: Session, group_id: int, current_user: User, data: MembershipCreate) -> dict:
    if data.role not in GROUP_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol de grupo invalido")
    if not can_manage_group(db, group_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes administrar este grupo")

    user = _find_active_user(db, data.identifier)
    membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id, GroupMembership.user_id == user.id)
        .first()
    )
    if membership:
        membership.role = data.role
    else:
        db.add(GroupMembership(group_id=group_id, user_id=user.id, role=data.role))
    db.commit()
    return get_group(db, group_id, current_user)


def update_member(db: Session, group_id: int, member_user_id: int, current_user: User, data: MembershipUpdate) -> dict:
    if data.role not in GROUP_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol de grupo invalido")
    if not can_manage_group(db, group_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes administrar este grupo")

    membership = _membership(db, group_id, member_user_id)
    if membership.role == "owner" and data.role != "owner" and _owner_count(db, group_id) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El grupo debe conservar al menos un owner")
    if membership.role == "owner" and not can_own_group(db, group_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo un owner puede cambiar a otro owner")

    membership.role = data.role
    db.commit()
    return get_group(db, group_id, current_user)


def remove_member(db: Session, group_id: int, member_user_id: int, current_user: User) -> dict:
    if member_user_id != current_user.id and not can_manage_group(db, group_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes administrar este grupo")
    membership = _membership(db, group_id, member_user_id)
    if membership.role == "owner" and _owner_count(db, group_id) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El grupo debe conservar al menos un owner")
    db.delete(membership)
    db.commit()
    return get_group(db, group_id, current_user)


def serialize_group(db: Session, group: WorkGroup, current_user_id: int) -> dict:
    current_role = group_role(db, group.id, current_user_id) or "admin"
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "created_by_user_id": group.created_by_user_id,
        "current_user_role": current_role,
        "created_at": group.created_at,
        "members": [
            {
                "user_id": membership.user.id,
                "username": membership.user.username,
                "email": membership.user.email,
                "display_name": membership.user.display_name,
                "avatar_url": avatar_url(membership.user),
                "role": membership.role,
                "created_at": membership.created_at,
            }
            for membership in sorted(group.memberships, key=lambda item: (item.role != "owner", item.user.username))
            if membership.user
        ],
    }


def avatar_url(user: User) -> str | None:
    return f"/profile/avatar/{user.id}" if user.avatar_path else None


def _group_visible(db: Session, group_id: int, user: User) -> WorkGroup:
    group = db.query(WorkGroup).filter(WorkGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado")
    if user.role != "admin" and not group_role(db, group_id, user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado")
    return group


def _membership(db: Session, group_id: int, user_id: int) -> GroupMembership:
    membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id, GroupMembership.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado")
    return membership


def _owner_count(db: Session, group_id: int) -> int:
    return (
        db.query(func.count(GroupMembership.id))
        .filter(GroupMembership.group_id == group_id, GroupMembership.role == "owner")
        .scalar()
        or 0
    )


def _find_active_user(db: Session, identifier: str) -> User:
    normalized = identifier.strip()
    user = db.query(User).filter((User.email == normalized) | (User.username == normalized)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario activo no encontrado")
    return user
