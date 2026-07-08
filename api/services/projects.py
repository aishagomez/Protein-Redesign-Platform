from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models import Project
from schemas.project import ProjectCreate, ProjectUpdate
from services.auth import is_admin_user_id
from services.access import can_manage_group, get_project_for_user, project_access_query


def get_projects(db: Session, user_id: int) -> List[Project]:
    return project_access_query(db, user_id).order_by(Project.created_at.desc()).all()


def get_project(db: Session, project_id: int, user_id: int) -> Project:
    return get_project_for_user(db, project_id, user_id)


def create_project(db: Session, data: ProjectCreate, user_id: int) -> Project:
    if data.group_id is not None and not can_manage_group(db, data.group_id, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes crear proyectos en este grupo")
    project = Project(user_id=user_id, group_id=data.group_id, name=data.name, description=data.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project_id: int, data: ProjectUpdate, user_id: int) -> Project:
    project = get_project(db, project_id, user_id)
    changes = data.model_dump(exclude_unset=True)
    if "group_id" in changes and changes["group_id"] is not None and not can_manage_group(db, changes["group_id"], user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes mover proyectos a este grupo")
    for field, value in changes.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, user_id: int) -> None:
    project = get_project(db, project_id, user_id)
    db.delete(project)
    db.commit()
