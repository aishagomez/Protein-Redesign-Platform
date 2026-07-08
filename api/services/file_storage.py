import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from models import Pipeline, Project, StageExecution
from services.access import get_project_for_user, get_stage_for_user

PERSISTENT_STORAGE_ROOT = Path(os.environ.get("PERSISTENT_STORAGE_ROOT", "/persistent_storage")).resolve()
UPLOADS_ROOT = (PERSISTENT_STORAGE_ROOT / "uploads").resolve()
GENERATED_ROOT = (PERSISTENT_STORAGE_ROOT / "generated").resolve()
AVATARS_ROOT = (PERSISTENT_STORAGE_ROOT / "avatars").resolve()


def _project_owned(db: Session, project_id: int, user_id: int) -> Project:
    return get_project_for_user(db, project_id, user_id)


def _safe_child(root: Path, child: Path) -> Path:
    resolved = child.resolve()
    if root != resolved and root not in resolved.parents:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruta fuera del almacenamiento permitido")
    return resolved


def project_upload_root(project_id: int, user_id: int) -> Path:
    path = UPLOADS_ROOT / f"user_{user_id}" / f"project_{project_id}"
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def generated_pipeline_root(pipeline_id: int) -> Path:
    path = GENERATED_ROOT / f"pipeline_{pipeline_id}"
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def save_project_upload(
    db: Session,
    project_id: int,
    user_id: int,
    upload: UploadFile,
    target_subdir: str | None = None,
) -> dict:
    project = _project_owned(db, project_id, user_id)
    if not upload.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo no tiene nombre")

    project_root = project_upload_root(project_id, project.user_id)
    relative_dir = Path(target_subdir.strip("/\\")) if target_subdir else Path(".")
    destination_dir = _safe_child(project_root, project_root / relative_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination = _safe_child(destination_dir, destination_dir / Path(upload.filename).name)
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return serialize_path(destination, project_root)


def save_avatar_file(user_id: int, upload: UploadFile) -> dict:
    """Save user avatar under AVATARS_ROOT/user_{id}/filename and return serialized info."""
    if not upload.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo no tiene nombre")

    user_dir = AVATARS_ROOT / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    destination = user_dir / Path(upload.filename).name
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return serialize_path(destination, AVATARS_ROOT)


def resolve_avatar_path(user_id: int, relative_path: str) -> Path:
    candidate = (AVATARS_ROOT / f"user_{user_id}" / relative_path).resolve()
    if not str(candidate).startswith(str(AVATARS_ROOT)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruta de avatar inválida")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar no encontrado")
    return candidate


def list_project_files(db: Session, project_id: int, user_id: int) -> list[dict]:
    project = _project_owned(db, project_id, user_id)
    project_root = project_upload_root(project_id, project.user_id)
    items = []
    for path in sorted(project_root.rglob("*"), key=lambda item: str(item)):
        if not path.is_file():
            continue
        items.append(serialize_path(path, project_root))
    return items


def resolve_project_file(db: Session, project_id: int, user_id: int, relative_path: str) -> Path:
    project = _project_owned(db, project_id, user_id)
    project_root = project_upload_root(project_id, project.user_id)
    candidate = _safe_child(project_root, project_root / relative_path)
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    return candidate


def get_stage_artifacts(db: Session, stage_execution_id: int, user_id: int) -> list[dict]:
    stage = _stage_owned(db, stage_execution_id, user_id)
    artifacts = []
    for output in stage.output_files or []:
        path = Path(output)
        if not path.exists() or not path.is_file():
            continue
        artifacts.append(
            {
                "name": path.name,
                "path": str(path),
                "size": path.stat().st_size,
            }
        )
    return artifacts


def get_project_outputs(db: Session, project_id: int, user_id: int) -> list[dict]:
    _project_owned(db, project_id, user_id)
    stages = (
        db.query(StageExecution)
        .join(Pipeline, StageExecution.pipeline_id == Pipeline.id)
        .filter(Pipeline.project_id == project_id)
        .filter(StageExecution.status == "completed")
        .order_by(Pipeline.id.desc(), StageExecution.stage_order_index.asc(), StageExecution.id.desc())
        .all()
    )

    grouped = []
    for stage in stages:
        artifacts = []
        for output in stage.output_files or []:
            path = Path(output)
            if not path.exists() or not path.is_file():
                continue
            artifacts.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "size": path.stat().st_size,
                }
            )
        if not artifacts:
            continue
        grouped.append(
            {
                "pipeline_id": stage.pipeline_id,
                "stage_execution_id": stage.id,
                "stage_name": stage.stage_name,
                "stage_order_index": stage.stage_order_index,
                "status": stage.status,
                "artifacts": artifacts,
                "created_at": stage.finished_at.isoformat() if stage.finished_at else None,
            }
        )
    return grouped


def resolve_stage_artifact(db: Session, stage_execution_id: int, user_id: int, artifact_path: str) -> Path:
    stage = _stage_owned(db, stage_execution_id, user_id)
    allowed = {str(Path(path).resolve()) for path in (stage.output_files or [])}
    candidate = Path(artifact_path).resolve()
    if str(candidate) not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El artefacto no pertenece a la etapa")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artefacto no encontrado")
    return candidate


def serialize_path(path: Path, root: Path | None = None) -> dict:
    stat = path.stat()
    return {
        "name": path.name,
        "absolute_path": str(path),
        "relative_path": str(path.relative_to(root)) if root else path.name,
        "size": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def _stage_owned(db: Session, stage_execution_id: int, user_id: int) -> StageExecution:
    return get_stage_for_user(db, stage_execution_id, user_id)
