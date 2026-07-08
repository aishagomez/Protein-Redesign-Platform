from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

from dependencies import get_db, get_current_user
from models import User
from schemas.tool import (
    ServiceTypeCreate, ServiceTypeUpdate, ServiceTypeResponse,
    ToolCreate, ToolUpdate, ToolResponse,
    ToolParameterCreate, ToolParameterUpdate, ToolParameterResponse,
)
import services.tools as svc

# ── ServiceTypes ───────────────────────────────────────────────────────────────
service_types_router = APIRouter(prefix="/service-types", tags=["Service Types"])


@service_types_router.get("/", response_model=List[ServiceTypeResponse])
def list_service_types(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_service_types(db)


@service_types_router.post("/", response_model=ServiceTypeResponse, status_code=status.HTTP_201_CREATED)
def create_service_type(data: ServiceTypeCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.create_service_type(db, data)


@service_types_router.get("/{service_type_id}", response_model=ServiceTypeResponse)
def get_service_type(service_type_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_service_type(db, service_type_id)


@service_types_router.patch("/{service_type_id}", response_model=ServiceTypeResponse)
def update_service_type(service_type_id: int, data: ServiceTypeUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.update_service_type(db, service_type_id, data)


@service_types_router.delete("/{service_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_type(service_type_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    svc.delete_service_type(db, service_type_id)


# ── Tools ──────────────────────────────────────────────────────────────────────
tools_router = APIRouter(prefix="/tools", tags=["Tools"])


@tools_router.get("/", response_model=List[ToolResponse])
def list_tools(
    service_type_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return svc.get_tools(db, service_type_id)


@tools_router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
def create_tool(data: ToolCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.create_tool(db, data)


@tools_router.get("/{tool_id}", response_model=ToolResponse)
def get_tool(tool_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_tool(db, tool_id)


@tools_router.patch("/{tool_id}", response_model=ToolResponse)
def update_tool(tool_id: int, data: ToolUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.update_tool(db, tool_id, data)


@tools_router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tool(tool_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    svc.delete_tool(db, tool_id)


# ── ToolParameters ─────────────────────────────────────────────────────────────
tool_params_router = APIRouter(prefix="/tools/{tool_id}/parameters", tags=["Tool Parameters"])


@tool_params_router.get("/", response_model=List[ToolParameterResponse])
def list_parameters(tool_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_tool_parameters(db, tool_id)


@tool_params_router.post("/", response_model=ToolParameterResponse, status_code=status.HTTP_201_CREATED)
def create_parameter(tool_id: int, data: ToolParameterCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.create_tool_parameter(db, tool_id, data)


@tool_params_router.get("/{param_id}", response_model=ToolParameterResponse)
def get_parameter(tool_id: int, param_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_tool_parameter(db, tool_id, param_id)


@tool_params_router.patch("/{param_id}", response_model=ToolParameterResponse)
def update_parameter(tool_id: int, param_id: int, data: ToolParameterUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.update_tool_parameter(db, tool_id, param_id, data)


@tool_params_router.delete("/{param_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parameter(tool_id: int, param_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    svc.delete_tool_parameter(db, tool_id, param_id)
