from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class WorkGroup(Base):
    __tablename__ = "work_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())

    creator = relationship("User", back_populates="created_groups")
    memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="group")


class GroupMembership(Base):
    __tablename__ = "group_memberships"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_member"),)

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("work_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False, default="member")
    created_at = Column(DateTime(timezone=False), server_default=func.now())

    group = relationship("WorkGroup", back_populates="memberships")
    user = relationship("User", back_populates="group_memberships")
