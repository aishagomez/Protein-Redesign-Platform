"""
Endpoints de orquestacion:
  POST /projects/{pid}/pipelines/{plid}/run
  POST /executions/{id}/approve
  POST /executions/{id}/retry-stage
  GET  /executions/{id}
  GET  /executions/{id}/stages

Endpoints internos (llamados por workers):
  POST /internal/stages/{id}/started
  POST /internal/stages/{id}/completed
  POST /internal/stages/{id}/failed
"""

import os
from typing import Optional, List

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user
from models import User, StageExecution
from services.auth import is_admin_user
from services.access import get_pipeline_by_id_for_user
from services.orchestration import (
    launch_pipeline,
    approve_stage,
    retry_stage_manual,
    on_stage_started,
    on_stage_completed,
    on_stage_failed,
)

INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "internal-secret-change-me")

router = APIRouter(tags=["Orquestacion"])


class StageDef(BaseModel):
    stage_name: str
    tool_id: int
    tool: str
    tool_version: Optional[str] = None
    params: dict


class RunPipelineRequest(BaseModel):
    stage_order: List[StageDef]
    pause_between_stages: bool = False


class ApproveRequest(BaseModel):
    chosen_stage_execution_id: Optional[int] = None
    params: Optional[dict] = None


class RetryStageRequest(BaseModel):
    stage_order_index: Optional[int] = None
    stage_execution_id: Optional[int] = None
    new_params: dict
    new_tool_id: Optional[int] = None
    new_tool: Optional[str] = None


class StageStartedPayload(BaseModel):
    celery_task_id: str


class StageCompletedPayload(BaseModel):
    output_files: List[str]
    metadata: dict = {}


class StageFailedPayload(BaseModel):
    error: str
    traceback: Optional[str] = None
    retry_type: str = "logical"  # technical | logical


def _verify_internal(x_internal_token: str = Header(...)):
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Token interno invalido")


@router.post(
    "/projects/{project_id}/pipelines/{pipeline_id}/run",
    summary="Lanzar pipeline flexible",
)
def run_pipeline(
    project_id: int,
    pipeline_id: int,
    body: RunPipelineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return launch_pipeline(
        db=db,
        project_id=project_id,
        pipeline_id=pipeline_id,
        user_id=current_user.id,
        stage_order=[s.model_dump() for s in body.stage_order],
        pause_between_stages=body.pause_between_stages,
    )


@router.post(
    "/executions/{pipeline_id}/approve",
    summary="Aprobar siguiente etapa (cuando pause_between_stages=true)",
)
def approve(
    pipeline_id: int,
    body: ApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return approve_stage(
        db=db,
        pipeline_id=pipeline_id,
        user_id=current_user.id,
        chosen_stage_execution_id=body.chosen_stage_execution_id,
        new_params=body.params,
    )


@router.post(
    "/executions/{pipeline_id}/retry-stage",
    summary="Retry manual de una etapa con nuevos parametros",
)
def retry_stage(
    pipeline_id: int,
    body: RetryStageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return retry_stage_manual(
        db=db,
        pipeline_id=pipeline_id,
        stage_order_index=body.stage_order_index,
        stage_execution_id=body.stage_execution_id,
        new_params=body.new_params,
        new_tool_id=body.new_tool_id,
        new_tool=body.new_tool,
        user_id=current_user.id,
    )


@router.get("/executions/{pipeline_id}", summary="Estado del pipeline")
def get_execution(
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from models import Pipeline

    pipeline = get_pipeline_by_id_for_user(db, pipeline_id, current_user.id)
    return {
        "pipeline_id": pipeline_id,
        "status": pipeline.status,
        "pause_between_stages": pipeline.pause_between_stages,
        "stage_order": pipeline.stage_order,
        "started_at": pipeline.started_at,
        "finished_at": pipeline.finished_at,
    }


@router.get("/executions/{pipeline_id}/stages", summary="Todas las StageExecutions del pipeline")
def get_stages(
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from models import Pipeline

    pipeline = get_pipeline_by_id_for_user(db, pipeline_id, current_user.id)
    stages = (
        db.query(StageExecution)
        .filter(StageExecution.pipeline_id == pipeline_id)
        .order_by(StageExecution.stage_order_index, StageExecution.id)
        .all()
    )
    return [
        {
            "id": s.id,
            "stage_name": s.stage_name,
            "stage_order_index": s.stage_order_index,
            "tool_id": s.tool_id,
            "tool": s.tool,
            "params": s.params,
            "status": s.status,
            "celery_task_id": s.celery_task_id,
            "retry_count": s.retry_count,
            "retry_type": s.retry_type,
            "output_files": s.output_files,
            "output_metadata": s.output_metadata,
            "error_message": s.error_message,
            "started_at": s.started_at,
            "finished_at": s.finished_at,
            "updated_at": s.updated_at,
        }
        for s in stages
    ]


@router.post(
    "/internal/stages/{stage_execution_id}/started",
    dependencies=[Depends(_verify_internal)],
    include_in_schema=False,
)
def internal_stage_started(
    stage_execution_id: int,
    body: StageStartedPayload,
    db: Session = Depends(get_db),
):
    on_stage_started(db, stage_execution_id, body.celery_task_id)
    return {"ok": True}


@router.post(
    "/internal/stages/{stage_execution_id}/completed",
    dependencies=[Depends(_verify_internal)],
    include_in_schema=False,
)
def internal_stage_completed(
    stage_execution_id: int,
    body: StageCompletedPayload,
    db: Session = Depends(get_db),
):
    on_stage_completed(db, stage_execution_id, body.output_files, body.metadata)
    return {"ok": True}


@router.post(
    "/internal/stages/{stage_execution_id}/failed",
    dependencies=[Depends(_verify_internal)],
    include_in_schema=False,
)
def internal_stage_failed(
    stage_execution_id: int,
    body: StageFailedPayload,
    db: Session = Depends(get_db),
):
    on_stage_failed(db, stage_execution_id, body.error, body.retry_type)
    return {"ok": True}
