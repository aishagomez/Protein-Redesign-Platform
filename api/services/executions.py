from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models import ServiceExecution, ExecutionLog, Pipeline, Project
from schemas.execution import ServiceExecutionCreate, ServiceExecutionUpdate
from services.access import get_pipeline_for_user


def _assert_pipeline_ownership(db: Session, project_id: int, pipeline_id: int, user_id: int) -> None:
    get_pipeline_for_user(db, project_id, pipeline_id, user_id)


# ── ServiceExecution ───────────────────────────────────────────────────────────
def get_service_executions(
    db: Session, project_id: int, pipeline_id: int, user_id: int
) -> List[ServiceExecution]:
    _assert_pipeline_ownership(db, project_id, pipeline_id, user_id)
    return db.query(ServiceExecution).filter(ServiceExecution.pipeline_id == pipeline_id).all()


def get_service_execution(
    db: Session, project_id: int, pipeline_id: int, execution_id: int, user_id: int
) -> ServiceExecution:
    _assert_pipeline_ownership(db, project_id, pipeline_id, user_id)
    execution = db.query(ServiceExecution).filter(
        ServiceExecution.id == execution_id,
        ServiceExecution.pipeline_id == pipeline_id,
    ).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejecución no encontrada")
    return execution


def create_service_execution(
    db: Session, project_id: int, pipeline_id: int, data: ServiceExecutionCreate, user_id: int
) -> ServiceExecution:
    _assert_pipeline_ownership(db, project_id, pipeline_id, user_id)
    execution = ServiceExecution(
        pipeline_id=pipeline_id,
        service_name=data.service_name,
        tool_id=data.tool_id,
        status="queued",
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def update_service_execution(
    db: Session, project_id: int, pipeline_id: int, execution_id: int,
    data: ServiceExecutionUpdate, user_id: int,
) -> ServiceExecution:
    execution = get_service_execution(db, project_id, pipeline_id, execution_id, user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(execution, field, value)
    db.commit()
    db.refresh(execution)
    return execution


def delete_service_execution(
    db: Session, project_id: int, pipeline_id: int, execution_id: int, user_id: int
) -> None:
    execution = get_service_execution(db, project_id, pipeline_id, execution_id, user_id)
    db.delete(execution)
    db.commit()


# ── ExecutionLog ───────────────────────────────────────────────────────────────
def get_execution_logs(
    db: Session, project_id: int, pipeline_id: int, execution_id: int, user_id: int
) -> List[ExecutionLog]:
    get_service_execution(db, project_id, pipeline_id, execution_id, user_id)
    return (
        db.query(ExecutionLog)
        .filter(ExecutionLog.service_execution_id == execution_id)
        .order_by(ExecutionLog.created_at)
        .all()
    )
