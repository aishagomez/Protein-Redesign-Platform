from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models import Tool, ToolRuntime, ToolParameter, ServiceType
from schemas.tool import (
    ServiceTypeCreate,
    ServiceTypeUpdate,
    ToolCreate,
    ToolUpdate,
    ToolParameterCreate,
    ToolParameterUpdate,
)


def get_service_types(db: Session) -> List[ServiceType]:
    return db.query(ServiceType).all()


def get_service_type(db: Session, service_type_id: int) -> ServiceType:
    service_type = db.query(ServiceType).filter(ServiceType.id == service_type_id).first()
    if not service_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de servicio no encontrado")
    return service_type


def create_service_type(db: Session, data: ServiceTypeCreate) -> ServiceType:
    existing = db.query(ServiceType).filter(ServiceType.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un tipo de servicio con ese nombre",
        )
    service_type = ServiceType(name=data.name, description=data.description)
    db.add(service_type)
    db.commit()
    db.refresh(service_type)
    return service_type


def update_service_type(db: Session, service_type_id: int, data: ServiceTypeUpdate) -> ServiceType:
    service_type = get_service_type(db, service_type_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(service_type, field, value)
    db.commit()
    db.refresh(service_type)
    return service_type


def delete_service_type(db: Session, service_type_id: int) -> None:
    service_type = get_service_type(db, service_type_id)
    db.delete(service_type)
    db.commit()


def get_tools(db: Session, service_type_id: int | None = None) -> List[Tool]:
    query = db.query(Tool)
    if service_type_id:
        query = query.filter(Tool.service_type_id == service_type_id)
    return query.all()


def get_tool(db: Session, tool_id: int) -> Tool:
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Herramienta no encontrada")
    return tool


def create_tool(db: Session, data: ToolCreate) -> Tool:
    get_service_type(db, data.service_type_id)
    payload = data.model_dump(exclude={"runtime"})
    tool = Tool(**payload)
    db.add(tool)
    db.flush()

    if data.runtime:
        runtime = ToolRuntime(tool_id=tool.id, **data.runtime.model_dump())
        db.add(runtime)

    db.commit()
    db.refresh(tool)
    return tool


def update_tool(db: Session, tool_id: int, data: ToolUpdate) -> Tool:
    tool = get_tool(db, tool_id)

    payload = data.model_dump(exclude_unset=True, exclude={"runtime"})
    if "service_type_id" in payload:
        get_service_type(db, payload["service_type_id"])

    for field, value in payload.items():
        setattr(tool, field, value)

    if data.runtime is not None:
        runtime_payload = data.runtime.model_dump(exclude_unset=True)
        if tool.runtime is None:
            tool.runtime = ToolRuntime(tool_id=tool.id, **runtime_payload)
        else:
            for field, value in runtime_payload.items():
                setattr(tool.runtime, field, value)

    db.commit()
    db.refresh(tool)
    return tool


def delete_tool(db: Session, tool_id: int) -> None:
    tool = get_tool(db, tool_id)
    db.delete(tool)
    db.commit()


def get_tool_parameters(db: Session, tool_id: int) -> List[ToolParameter]:
    get_tool(db, tool_id)
    return (
        db.query(ToolParameter)
        .filter(ToolParameter.tool_id == tool_id)
        .order_by(ToolParameter.position.asc().nulls_last(), ToolParameter.id.asc())
        .all()
    )


def get_tool_parameter(db: Session, tool_id: int, param_id: int) -> ToolParameter:
    param = db.query(ToolParameter).filter(
        ToolParameter.id == param_id,
        ToolParameter.tool_id == tool_id,
    ).first()
    if not param:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parametro no encontrado")
    return param


def create_tool_parameter(db: Session, tool_id: int, data: ToolParameterCreate) -> ToolParameter:
    get_tool(db, tool_id)
    param = ToolParameter(tool_id=tool_id, **data.model_dump())
    db.add(param)
    db.commit()
    db.refresh(param)
    return param


def update_tool_parameter(
    db: Session,
    tool_id: int,
    param_id: int,
    data: ToolParameterUpdate,
) -> ToolParameter:
    param = get_tool_parameter(db, tool_id, param_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(param, field, value)
    db.commit()
    db.refresh(param)
    return param


def delete_tool_parameter(db: Session, tool_id: int, param_id: int) -> None:
    param = get_tool_parameter(db, tool_id, param_id)
    db.delete(param)
    db.commit()
