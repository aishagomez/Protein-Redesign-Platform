from pydantic import BaseModel
from typing import Optional, Any, Dict, List


class ServiceTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ServiceTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ServiceTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    model_config = {"from_attributes": True}


class ToolRuntimeCreate(BaseModel):
    mode: str
    image: Optional[str] = None
    workdir: Optional[str] = None
    command_template: List[str] = []
    mounts: List[Dict[str, Any]] = []
    env: Dict[str, Any] = {}
    resources: Dict[str, Any] = {}
    notes: Optional[str] = None


class ToolRuntimeUpdate(BaseModel):
    mode: Optional[str] = None
    image: Optional[str] = None
    workdir: Optional[str] = None
    command_template: Optional[List[str]] = None
    mounts: Optional[List[Dict[str, Any]]] = None
    env: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ToolRuntimeResponse(BaseModel):
    id: int
    tool_id: int
    mode: str
    image: Optional[str]
    workdir: Optional[str]
    command_template: List[str]
    mounts: List[Dict[str, Any]]
    env: Dict[str, Any]
    resources: Dict[str, Any]
    notes: Optional[str]

    model_config = {"from_attributes": True}


class ToolParameterCreate(BaseModel):
    name: str
    data_type: str
    flag: Optional[str] = None
    optional: bool = True
    default_value: Optional[str] = None
    format: Optional[str] = None
    position: Optional[int] = None
    is_input: bool = False
    is_output: bool = False
    ui_label: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ToolParameterUpdate(BaseModel):
    name: Optional[str] = None
    data_type: Optional[str] = None
    flag: Optional[str] = None
    optional: Optional[bool] = None
    default_value: Optional[str] = None
    format: Optional[str] = None
    position: Optional[int] = None
    is_input: Optional[bool] = None
    is_output: Optional[bool] = None
    ui_label: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ToolParameterResponse(BaseModel):
    id: int
    tool_id: int
    name: str
    data_type: str
    flag: Optional[str]
    optional: bool
    default_value: Optional[str]
    format: Optional[str]
    position: Optional[int]
    is_input: bool
    is_output: bool
    ui_label: Optional[str]
    options: Optional[Dict[str, Any]]
    description: Optional[str]

    model_config = {"from_attributes": True}


class ToolCreate(BaseModel):
    service_type_id: int
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    executable_path: Optional[str] = None
    definition_format: Optional[str] = "xml"
    definition_source: Optional[str] = None
    active: bool = True
    runtime: Optional[ToolRuntimeCreate] = None


class ToolUpdate(BaseModel):
    service_type_id: Optional[int] = None
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    executable_path: Optional[str] = None
    definition_format: Optional[str] = None
    definition_source: Optional[str] = None
    active: Optional[bool] = None
    runtime: Optional[ToolRuntimeUpdate] = None


class ToolResponse(BaseModel):
    id: int
    service_type_id: int
    name: str
    version: Optional[str]
    description: Optional[str]
    executable_path: Optional[str]
    definition_format: Optional[str]
    definition_source: Optional[str]
    active: bool
    runtime: Optional[ToolRuntimeResponse] = None
    parameters: List[ToolParameterResponse] = []

    model_config = {"from_attributes": True}
