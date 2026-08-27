from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
from dependencies import get_admin_user, get_db
from models import Pipeline, Project, StageExecution, User
from services.orchestration import WORKER_TIMEOUT_SECONDS, get_watchdog

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


def _serialize_dt(value):
    return value.isoformat() if value else None


@router.get("/summary", summary="Resumen operativo para dashboard")
def monitoring_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    projects = db.query(Project).all()
    project_ids = [project.id for project in projects]

    if project_ids:
        pipelines = db.query(Pipeline).filter(Pipeline.project_id.in_(project_ids)).all()
    else:
        pipelines = []

    pipeline_ids = [pipeline.id for pipeline in pipelines]
    if pipeline_ids:
        stages = (
            db.query(StageExecution)
            .filter(StageExecution.pipeline_id.in_(pipeline_ids))
            .order_by(StageExecution.pipeline_id, StageExecution.stage_order_index, StageExecution.id.desc())
            .all()
        )
    else:
        stages = []

    latest_stage_by_pipeline_and_index = {}
    for stage in stages:
        key = (stage.pipeline_id, stage.stage_order_index)
        if key not in latest_stage_by_pipeline_and_index:
            latest_stage_by_pipeline_and_index[key] = stage

    active_stage_lists = {}
    for stage in latest_stage_by_pipeline_and_index.values():
        active_stage_lists.setdefault(stage.pipeline_id, []).append(stage)

    pipeline_cards = []
    for pipeline in sorted(pipelines, key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True):
        active_stages = sorted(active_stage_lists.get(pipeline.id, []), key=lambda item: item.stage_order_index)
        current_stage = next((stage for stage in active_stages if stage.status in {"running", "pending", "waiting_for_approval", "retrying"}), None)
        failed_stage = next((stage for stage in active_stages if stage.status == "failed"), None)

        pipeline_cards.append(
            {
                "pipeline_id": pipeline.id,
                "project_id": pipeline.project_id,
                "project_name": next((project.name for project in projects if project.id == pipeline.project_id), f"Project {pipeline.project_id}"),
                "version": pipeline.version,
                "status": pipeline.status,
                "current_stage": current_stage.stage_name if current_stage else (failed_stage.stage_name if failed_stage else None),
                "progress": {
                    "total": len(active_stages),
                    "completed": len([stage for stage in active_stages if stage.status == "completed"]),
                    "running": len([stage for stage in active_stages if stage.status == "running"]),
                    "failed": len([stage for stage in active_stages if stage.status == "failed"]),
                },
                "started_at": _serialize_dt(pipeline.started_at),
                "finished_at": _serialize_dt(pipeline.finished_at),
            }
        )

    failed_stages = [
        {
            "pipeline_id": stage.pipeline_id,
            "stage_execution_id": stage.id,
            "stage_name": stage.stage_name,
            "tool": stage.tool,
            "error_message": stage.error_message,
            "updated_at": _serialize_dt(stage.updated_at),
        }
        for stage in sorted(
            [stage for stage in latest_stage_by_pipeline_and_index.values() if stage.status == "failed"],
            key=lambda item: item.updated_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )[:5]
    ]

    now = datetime.now(timezone.utc)
    timeout = timedelta(seconds=WORKER_TIMEOUT_SECONDS)
    watchdog = get_watchdog(SessionLocal)
    raw_worker_last_seen = getattr(watchdog, "worker_last_seen", {})
    expected_workers = ["refinement", "docking", "interaction_optimization"]
    worker_status = []

    for worker_name in expected_workers:
        matching = [
            (hostname, last_seen)
            for hostname, last_seen in raw_worker_last_seen.items()
            if hostname.startswith(f"{worker_name}@") or worker_name in hostname
        ]
        if matching:
            hostname, last_seen = sorted(matching, key=lambda item: item[1], reverse=True)[0]
            online = now - last_seen <= timeout
            worker_status.append(
                {
                    "name": worker_name,
                    "hostname": hostname,
                    "status": "online" if online else "offline",
                    "last_seen": _serialize_dt(last_seen),
                }
            )
        else:
            worker_status.append(
                {
                    "name": worker_name,
                    "hostname": None,
                    "status": "unknown",
                    "last_seen": None,
                }
            )

    return {
        "kpis": {
            "projects": len(projects),
            "pipelines_active": len([pipeline for pipeline in pipelines if pipeline.status in {"running", "waiting_for_approval"}]),
            "executions_in_progress": len([stage for stage in latest_stage_by_pipeline_and_index.values() if stage.status == "running"]),
            "recent_failures": len(failed_stages),
            "workers_active": len([worker for worker in worker_status if worker["status"] == "online"]),
        },
        "pipelines": pipeline_cards[:12],
        "recent_failures": failed_stages,
        "worker_status": worker_status,
        "system_status": {
            "api": "online",
            "db": "online",
            "broker": "unknown",
        },
    }
