from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models import Pipeline, Project
from schemas.pipeline import PipelineCreate, PipelineUpdate
from services.access import get_pipeline_for_user, get_project_for_user


def _assert_project_ownership(db: Session, project_id: int, user_id: int) -> None:
    get_project_for_user(db, project_id, user_id)


def get_pipelines(db: Session, project_id: int, user_id: int) -> List[Pipeline]:
    _assert_project_ownership(db, project_id, user_id)
    return db.query(Pipeline).filter(Pipeline.project_id == project_id).all()


def get_pipeline(db: Session, project_id: int, pipeline_id: int, user_id: int) -> Pipeline:
    return get_pipeline_for_user(db, project_id, pipeline_id, user_id)


def create_pipeline(db: Session, project_id: int, data: PipelineCreate, user_id: int) -> Pipeline:
    _assert_project_ownership(db, project_id, user_id)
    pipeline = Pipeline(
        project_id=project_id,
        version=data.version,
        parameters=data.parameters,
        status="pending",
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline


def update_pipeline(
    db: Session, project_id: int, pipeline_id: int, data: PipelineUpdate, user_id: int
) -> Pipeline:
    pipeline = get_pipeline(db, project_id, pipeline_id, user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pipeline, field, value)
    db.commit()
    db.refresh(pipeline)
    return pipeline


def delete_pipeline(db: Session, project_id: int, pipeline_id: int, user_id: int) -> None:
    pipeline = get_pipeline(db, project_id, pipeline_id, user_id)
    db.delete(pipeline)
    db.commit()
