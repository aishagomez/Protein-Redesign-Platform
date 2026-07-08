from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from dependencies import get_db, get_current_user
from models import User
from schemas.execution import (
    ServiceExecutionCreate, ServiceExecutionUpdate,
    ServiceExecutionResponse, ExecutionLogResponse,
)
import services.executions as svc

router = APIRouter(
    prefix="/projects/{project_id}/pipelines/{pipeline_id}/executions",
    tags=["Service Executions"],
)


@router.get("/", response_model=List[ServiceExecutionResponse], summary="Listar ejecuciones del pipeline")
def list_executions(
    project_id: int,
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.get_service_executions(db, project_id, pipeline_id, current_user.id)


@router.post("/", response_model=ServiceExecutionResponse, status_code=status.HTTP_201_CREATED, summary="Crear ejecución")
def create_execution(
    project_id: int,
    pipeline_id: int,
    data: ServiceExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.create_service_execution(db, project_id, pipeline_id, data, current_user.id)


@router.get("/{execution_id}", response_model=ServiceExecutionResponse, summary="Obtener ejecución")
def get_execution(
    project_id: int,
    pipeline_id: int,
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.get_service_execution(db, project_id, pipeline_id, execution_id, current_user.id)


@router.patch("/{execution_id}", response_model=ServiceExecutionResponse, summary="Actualizar ejecución")
def update_execution(
    project_id: int,
    pipeline_id: int,
    execution_id: int,
    data: ServiceExecutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.update_service_execution(db, project_id, pipeline_id, execution_id, data, current_user.id)


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar ejecución")
def delete_execution(
    project_id: int,
    pipeline_id: int,
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc.delete_service_execution(db, project_id, pipeline_id, execution_id, current_user.id)


@router.get("/{execution_id}/logs", response_model=List[ExecutionLogResponse], summary="Ver logs de ejecución")
def get_logs(
    project_id: int,
    pipeline_id: int,
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.get_execution_logs(db, project_id, pipeline_id, execution_id, current_user.id)
