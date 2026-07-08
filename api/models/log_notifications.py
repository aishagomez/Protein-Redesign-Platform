from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    service_execution_id = Column(Integer, ForeignKey("service_executions.id"), nullable=True)
    stage_execution_id = Column(Integer, ForeignKey("stage_executions.id"), nullable=True)  # NUEVO
    log_level = Column(String, default="INFO")
    message = Column(Text, nullable=False)
    event_type = Column(String(50))  # NUEVO: "start"|"heartbeat"|"complete"|"fail"|"retry"|"watchdog"
    created_at = Column(DateTime, server_default=func.now())
    service_execution = relationship("ServiceExecution", back_populates="logs")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(Text)
    message = Column(Text)
    sent_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="notifications")