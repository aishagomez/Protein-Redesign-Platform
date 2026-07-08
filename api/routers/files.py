from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db
from models import User
from services.file_storage import (
    get_project_outputs,
    get_stage_artifacts,
    list_project_files,
    resolve_project_file,
    resolve_stage_artifact,
    save_project_upload,
)

router = APIRouter(tags=["Files"])


@router.get("/projects/{project_id}/files", summary="Listar archivos subidos del proyecto")
def project_files(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_project_files(db, project_id, current_user.id)


@router.post("/projects/{project_id}/files/upload", summary="Subir archivo a un proyecto")
def upload_project_file(
    project_id: int,
    target_subdir: str | None = Query(default=None),
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return save_project_upload(db, project_id, current_user.id, upload, target_subdir)


@router.get("/projects/{project_id}/outputs", summary="Listar salidas descargables del proyecto")
def project_outputs(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_project_outputs(db, project_id, current_user.id)


@router.get("/projects/{project_id}/files/download", summary="Descargar archivo subido al proyecto")
def download_project_file(
    project_id: int,
    path: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path = resolve_project_file(db, project_id, current_user.id, path)
    return FileResponse(file_path, filename=file_path.name)


@router.get("/executions/stages/{stage_execution_id}/artifacts", summary="Listar artefactos de salida de una etapa")
def stage_artifacts(
    stage_execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_stage_artifacts(db, stage_execution_id, current_user.id)


@router.get("/executions/stages/{stage_execution_id}/artifacts/download", summary="Descargar artefacto de una etapa")
def download_stage_artifact(
    stage_execution_id: int,
    path: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path = resolve_stage_artifact(db, stage_execution_id, current_user.id, path)
    return FileResponse(file_path, filename=file_path.name)
