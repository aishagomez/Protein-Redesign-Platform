from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from dependencies import get_db, get_current_user
from models import User
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
import services.projects as svc

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=List[ProjectResponse], summary="Listar mis proyectos")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.get_projects(db, current_user.id)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Crear proyecto")
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.create_project(db, data, current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse, summary="Obtener proyecto")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.get_project(db, project_id, current_user.id)


@router.patch("/{project_id}", response_model=ProjectResponse, summary="Actualizar proyecto")
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.update_project(db, project_id, data, current_user.id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar proyecto")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc.delete_project(db, project_id, current_user.id)
