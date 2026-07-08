from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class ServiceType(Base):
    __tablename__ = "service_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    tools = relationship("Tool", back_populates="service_type")


# Modelo original: se mantiene intacto para no romper routers existentes
class ServiceExecution(Base):
    __tablename__ = "service_executions"
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"))
    service_name = Column(String, nullable=False)
    status = Column(String, default="queued")
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime)
    log_reference = Column(Text)
    message = Column(Text)
    tool_id = Column(Integer, ForeignKey("tools.id"))
    pipeline = relationship("Pipeline", back_populates="service_executions")
    tool = relationship("Tool", back_populates="service_executions")
    logs = relationship("ExecutionLog", back_populates="service_execution")


class StageExecution(Base):
    """
    Una ejecucion concreta de una etapa dentro de un pipeline.
    Puede haber multiples StageExecutions por etapa (historial de retries).
    La activa es la de mayor id con status != failed, o la ultima si todas fallaron.
    """

    __tablename__ = "stage_executions"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    stage_name = Column(String(50), nullable=False)   # refinement|docking|evolution
    stage_order_index = Column(Integer, nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id"))
    tool = Column(String(100), nullable=False)
    tool_version = Column(String(50))
    params = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    # pending|running|waiting_for_approval|completed|failed|retrying
    retry_count = Column(Integer, default=0)
    retry_type = Column(String(20))  # technical | logical | manual
    error_message = Column(Text)
    output_files = Column(JSON, default=list)
    output_metadata = Column(JSON, default=dict)
    celery_task_id = Column(String(200))

    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pipeline = relationship("Pipeline", back_populates="stage_executions")
