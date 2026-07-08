import os
import time
import threading
from datetime import datetime, timezone

import requests
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, create_engine, func
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@db:5432/pipeline_db")
RABBITMQ_API_URL = os.environ.get("RABBITMQ_API_URL", "http://broker:15672/api")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "password")
PIPELINE_FAILURE_WINDOW = int(os.environ.get("PIPELINE_FAILURE_WINDOW", "10"))
CACHE_TTL = int(os.environ.get("SUMMARY_TTL", "10"))

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

class Pipeline(Base):
    __tablename__ = "pipelines"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    version = Column(String(50))
    status = Column(String(50))
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))
    project = relationship("Project")

class StageExecution(Base):
    __tablename__ = "stage_executions"
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"))
    stage_name = Column(String(100))
    tool = Column(String(100))
    status = Column(String(50))
    output_files = Column(JSON)
    output_metadata = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    id = Column(Integer, primary_key=True)
    stage_execution_id = Column(Integer, ForeignKey("stage_executions.id"), nullable=True)
    log_level = Column(String(20))
    message = Column(Text)
    event_type = Column(String(50))
    created_at = Column(DateTime(timezone=True))

class UserFile(Base):
    __tablename__ = "user_files"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_filename = Column(String(255))
    size_bytes = Column(Integer)
    created_at = Column(DateTime(timezone=True))

PIPELINE_STATUS_GAUGE = Gauge("pipeline_total_by_status", "Pipelines grouped by status", ["status"])
STAGE_STATUS_GAUGE = Gauge("stage_total_by_status", "Stage executions grouped by status", ["status"])
EXECUTION_LOG_GAUGE = Gauge("execution_logs_total_by_level", "Execution logs grouped by level", ["level"])
RABBIT_READY_GAUGE = Gauge("rabbitmq_queue_messages_ready", "RabbitMQ ready messages by queue", ["queue"])
RABBIT_CONSUMERS_GAUGE = Gauge("rabbitmq_queue_consumers", "RabbitMQ consumers by queue", ["queue"])
USER_FILE_GAUGE = Gauge("user_files_total", "Total uploaded user files")
OUTPUT_FILE_GAUGE = Gauge("output_files_total", "Total published output files")

app = FastAPI(title="Observability Service", version="0.1.0")

_summary_cache = None
_last_update = 0
_lock = threading.Lock()

def _serialize_dt(value):
    return value.isoformat() if value else None

def _fetch_rabbitmq_queues():
    try:
        r = requests.get(
            f"{RABBITMQ_API_URL}/queues",
            auth=(RABBITMQ_USER, RABBITMQ_PASSWORD),
            timeout=5,
        )
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return [], str(e)

def _build_summary():
    db = SessionLocal()
    try:
        queue_payload, queue_error = _fetch_rabbitmq_queues()

        pipeline_counts = dict(
            db.query(Pipeline.status, func.count())
            .group_by(Pipeline.status)
            .all()
        )

        stage_counts = dict(
            db.query(StageExecution.status, func.count())
            .group_by(StageExecution.status)
            .all()
        )

        logs_by_level = dict(
            db.query(ExecutionLog.log_level, func.count())
            .group_by(ExecutionLog.log_level)
            .all()
        )

        logs = (
            db.query(ExecutionLog)
            .order_by(ExecutionLog.created_at.desc(), ExecutionLog.id.desc())
            .limit(20)
            .all()
        )

        failed_stages = (
            db.query(StageExecution)
            .filter(StageExecution.status == "failed")
            .order_by(StageExecution.updated_at.desc(), StageExecution.id.desc())
            .limit(PIPELINE_FAILURE_WINDOW)
            .all()
        )

        total_outputs = sum(len(s.output_files or []) for s in db.query(StageExecution.output_files).all())

        projects_total = db.query(func.count(Project.id)).scalar()
        pipelines_total = sum(pipeline_counts.values())
        user_files_total = db.query(func.count(UserFile.id)).scalar()

        for k, v in pipeline_counts.items():
            PIPELINE_STATUS_GAUGE.labels(status=k or "unknown").set(v)

        for k, v in stage_counts.items():
            STAGE_STATUS_GAUGE.labels(status=k or "unknown").set(v)

        for k, v in logs_by_level.items():
            EXECUTION_LOG_GAUGE.labels(level=k or "INFO").set(v)

        USER_FILE_GAUGE.set(user_files_total)
        OUTPUT_FILE_GAUGE.set(total_outputs)

        for q in queue_payload:
            name = q.get("name", "unknown")
            RABBIT_READY_GAUGE.labels(queue=name).set(q.get("messages_ready", 0))
            RABBIT_CONSUMERS_GAUGE.labels(queue=name).set(q.get("consumers", 0))

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "kpis": {
                "projects_total": projects_total,
                "pipelines_total": pipelines_total,
                "pipelines_running": pipeline_counts.get("running", 0),
                "pipelines_failed": pipeline_counts.get("failed", 0),
                "stages_running": stage_counts.get("running", 0),
                "stages_failed": stage_counts.get("failed", 0),
                "logs_total": sum(logs_by_level.values()),
                "user_files_total": user_files_total,
                "output_files_total": total_outputs,
            },
            "queues": queue_payload,
            "recent_logs": [
                {
                    "id": l.id,
                    "level": l.log_level,
                    "message": l.message,
                    "created_at": _serialize_dt(l.created_at),
                }
                for l in logs
            ],
            "recent_failures": [
                {
                    "stage_execution_id": s.id,
                    "error_message": s.error_message,
                    "updated_at": _serialize_dt(s.updated_at),
                }
                for s in failed_stages
            ],
            "queue_error": queue_error,
        }

    except (ProgrammingError, OperationalError):
        return {}
    finally:
        db.close()

def _background_updater():
    global _summary_cache, _last_update
    while True:
        try:
            data = _build_summary()
            with _lock:
                _summary_cache = data
                _last_update = time.time()
        except Exception as e:
            print("update error:", e)
        time.sleep(CACHE_TTL)

@app.on_event("startup")
def startup():
    t = threading.Thread(target=_background_updater, daemon=True)
    t.start()

def get_summary():
    with _lock:
        return _summary_cache or {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/summary")
def summary():
    return get_summary()

@app.get("/metrics")
def metrics():
    get_summary()
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)