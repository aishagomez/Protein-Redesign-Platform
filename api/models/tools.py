from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database import Base


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    service_type_id = Column(Integer, ForeignKey("service_types.id"))
    name = Column(String(100), nullable=False)
    version = Column(String(50))
    description = Column(Text)
    executable_path = Column(Text)
    definition_format = Column(String(20), default="xml")
    definition_source = Column(Text)
    active = Column(Boolean, default=True)

    service_type = relationship("ServiceType", back_populates="tools")
    parameters = relationship("ToolParameter", back_populates="tool", cascade="all, delete")
    runtime = relationship("ToolRuntime", back_populates="tool", cascade="all, delete-orphan", uselist=False)
    service_executions = relationship("ServiceExecution", back_populates="tool")


class ToolRuntime(Base):
    __tablename__ = "tool_runtimes"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), unique=True, nullable=False)
    mode = Column(String(20), nullable=False, default="docker")
    image = Column(String(255))
    workdir = Column(String(255))
    command_template = Column(JSON, default=list)
    mounts = Column(JSON, default=list)
    env = Column(JSON, default=dict)
    resources = Column(JSON, default=dict)
    notes = Column(Text)

    tool = relationship("Tool", back_populates="runtime")


class ToolParameter(Base):
    __tablename__ = "tool_parameters"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"))
    name = Column(String(100), nullable=False)
    flag = Column(String(100))
    data_type = Column(String(50), nullable=False)
    optional = Column(Boolean, default=True)
    default_value = Column(Text)
    format = Column(String(50))
    position = Column(Integer)
    is_input = Column(Boolean, default=False)
    is_output = Column(Boolean, default=False)
    ui_label = Column(String(100))
    options = Column(JSON)
    description = Column(Text)

    tool = relationship("Tool", back_populates="parameters")
