from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db
from models import User
from services.reports import (
    generate_pipeline_report_file,
    generate_project_report_file,
    get_pipeline_report,
    get_project_reports_overview,
)

router = APIRouter(tags=["Reports"])


@router.get("/projects/{project_id}/reports/overview", summary="Resumen de reportes del proyecto")
def project_reports_overview(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_project_reports_overview(db, project_id, current_user.id)


@router.get("/projects/{project_id}/reports/download", summary="Descargar reporte del proyecto")
def download_project_report(
    project_id: int,
    format: str = Query(default="md", pattern="^(md|json)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path = generate_project_report_file(db, project_id, current_user.id, format)
    return FileResponse(file_path, filename=file_path.name)


@router.get("/projects/{project_id}/pipelines/{pipeline_id}/reports/overview", summary="Resumen del reporte de pipeline")
def pipeline_report_overview(
    project_id: int,
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_pipeline_report(db, project_id, pipeline_id, current_user.id)


@router.get("/projects/{project_id}/pipelines/{pipeline_id}/reports/download", summary="Descargar reporte del pipeline")
def download_pipeline_report(
    project_id: int,
    pipeline_id: int,
    format: str = Query(default="md", pattern="^(md|json)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path = generate_pipeline_report_file(db, project_id, pipeline_id, current_user.id, format)
    return FileResponse(file_path, filename=file_path.name)
