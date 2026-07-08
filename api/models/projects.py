from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("work_groups.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    user = relationship("User", back_populates="projects")
    group = relationship("WorkGroup", back_populates="projects")
    pipelines = relationship("Pipeline", back_populates="project")
