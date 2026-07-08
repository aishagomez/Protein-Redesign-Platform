from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String, nullable=False, default="user")
    display_name = Column(String, nullable=True)
    avatar_path = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    projects = relationship("Project", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    group_memberships = relationship("GroupMembership", back_populates="user", cascade="all, delete-orphan")
    created_groups = relationship("WorkGroup", back_populates="creator")
