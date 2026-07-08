from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base, SessionLocal
from models import User, WorkGroup, GroupMembership, Project, Pipeline, ServiceType, Tool, ToolParameter, ExecutionLog, Notification, StageExecution
from routers import (
    auth_router, projects_router, pipelines_router,
    service_types_router, tools_router, tool_params_router,
    executions_router, orchestration_router, monitoring_router, files_router, manual_router, documentation_router, reports_router, profile_router, groups_router,
)
from import_tool_from_xml import import_tools_from_directory
from services.auth import ensure_bootstrap_admin
from services.orchestration import get_watchdog


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Reiniciar completamente la base al arrancar
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin_user = ensure_bootstrap_admin(db)
        print(f"[Startup] Bootstrap admin ready: id={admin_user.id}, email={admin_user.email}, role={admin_user.role}")
    finally:
        db.close()

    # Importar herramientas declaradas en XML
    definitions_dir = Path(__file__).resolve().parent / "examples"
    imported_tools = import_tools_from_directory(str(definitions_dir))
    print(f"[Startup] XML definitions dir: {definitions_dir}")
    print(f"[Startup] Imported tools from XML: {len(imported_tools)}")
    for tool in imported_tools:
        print(f"[Startup] Tool synced: id={tool.id}, name={tool.name}, version={tool.version}")

    # Arrancar watchdog en thread daemon
    watchdog = get_watchdog(db_factory=SessionLocal)
    watchdog.start()

    yield

    # Al apagar, detener watchdog
    watchdog.stop()


app = FastAPI(
    title="Pipeline Bioinformático API",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(pipelines_router)
app.include_router(service_types_router)
app.include_router(tools_router)
app.include_router(tool_params_router)
app.include_router(executions_router)
app.include_router(orchestration_router)
app.include_router(monitoring_router)
app.include_router(files_router)
app.include_router(manual_router)
app.include_router(documentation_router)
app.include_router(reports_router)
app.include_router(profile_router)
app.include_router(groups_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "version": "0.3.0"}
