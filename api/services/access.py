from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import GroupMembership, Pipeline, Project, StageExecution
from services.auth import is_admin_user_id

GROUP_OWNER_ROLES = {"owner"}
GROUP_MANAGER_ROLES = {"owner", "admin"}


def user_group_ids(db: Session, user_id: int) -> list[int]:
    return [
        row.group_id
        for row in db.query(GroupMembership.group_id).filter(GroupMembership.user_id == user_id).all()
    ]


def group_role(db: Session, group_id: int, user_id: int) -> str | None:
    membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id, GroupMembership.user_id == user_id)
        .first()
    )
    return membership.role if membership else None


def can_manage_group(db: Session, group_id: int, user_id: int) -> bool:
    if is_admin_user_id(db, user_id):
        return True
    return group_role(db, group_id, user_id) in GROUP_MANAGER_ROLES


def can_own_group(db: Session, group_id: int, user_id: int) -> bool:
    if is_admin_user_id(db, user_id):
        return True
    return group_role(db, group_id, user_id) in GROUP_OWNER_ROLES


def project_access_query(db: Session, user_id: int):
    query = db.query(Project)
    if is_admin_user_id(db, user_id):
        return query
    groups = user_group_ids(db, user_id)
    criteria = [Project.user_id == user_id]
    if groups:
        criteria.append(Project.group_id.in_(groups))
    return query.filter(*criteria) if len(criteria) == 1 else query.filter(criteria[0] | criteria[1])


def get_project_for_user(db: Session, project_id: int, user_id: int) -> Project:
    project = project_access_query(db, user_id).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


def get_pipeline_for_user(db: Session, project_id: int, pipeline_id: int, user_id: int) -> Pipeline:
    get_project_for_user(db, project_id, user_id)
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id, Pipeline.project_id == project_id).first()
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline no encontrado")
    return pipeline


def get_pipeline_by_id_for_user(db: Session, pipeline_id: int, user_id: int) -> Pipeline:
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline or not pipeline.project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline no encontrado")
    get_project_for_user(db, pipeline.project_id, user_id)
    return pipeline


def get_stage_for_user(db: Session, stage_execution_id: int, user_id: int) -> StageExecution:
    stage = (
        db.query(StageExecution)
        .join(Pipeline, StageExecution.pipeline_id == Pipeline.id)
        .filter(StageExecution.id == stage_execution_id)
        .first()
    )
    if not stage or not stage.pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="StageExecution no encontrada")
    get_project_for_user(db, stage.pipeline.project_id, user_id)
    return stage
