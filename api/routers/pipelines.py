from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from dependencies import get_db, get_current_user
from models import User
from schemas.pipeline import PipelineCreate, PipelineUpdate, PipelineResponse
import services.pipelines as svc

router = APIRouter(prefix="/projects/{project_id}/pipelines", tags=["Pipelines"])


@router.get("/", response_model=List[PipelineResponse], summary="Listar pipelines del proyecto")
def list_pipelines(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.get_pipelines(db, project_id, current_user.id)


@router.post("/", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED, summary="Crear pipeline")
def create_pipeline(
    project_id: int,
    data: PipelineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.create_pipeline(db, project_id, data, current_user.id)


@router.get("/{pipeline_id}", response_model=PipelineResponse, summary="Obtener pipeline")
def get_pipeline(
    project_id: int,
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.get_pipeline(db, project_id, pipeline_id, current_user.id)


@router.patch("/{pipeline_id}", response_model=PipelineResponse, summary="Actualizar pipeline")
def update_pipeline(
    project_id: int,
    pipeline_id: int,
    data: PipelineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.update_pipeline(db, project_id, pipeline_id, data, current_user.id)


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar pipeline")
def delete_pipeline(
    project_id: int,
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc.delete_pipeline(db, project_id, pipeline_id, current_user.id)
