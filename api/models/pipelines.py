from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Pipeline(Base):
    __tablename__ = "pipelines"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    version = Column(String)
    status = Column(String, default="pending")  # pending|running|waiting_for_approval|completed|failed
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    parameters = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    pause_between_stages = Column(Boolean, default=False)
    stage_order = Column(JSON, default=list)

    project = relationship("Project", back_populates="pipelines")
    stage_executions = relationship(
        "StageExecution",
        back_populates="pipeline",
        order_by="StageExecution.stage_order_index",
    )
    service_executions = relationship("ServiceExecution", back_populates="pipeline")