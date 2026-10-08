from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Integer, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.STUDENT, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    profile: Mapped[Optional["Profile"]] = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    user_skills: Mapped[List["UserSkill"]] = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    job_analyses: Mapped[List["JobAnalysis"]] = relationship("JobAnalysis", back_populates="user", cascade="all, delete-orphan")
    skill_gap_reports: Mapped[List["SkillGapReport"]] = relationship("SkillGapReport", back_populates="user", cascade="all, delete-orphan")
    roadmaps: Mapped[List["Roadmap"]] = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    project_recommendations: Mapped[List["ProjectRecommendation"]] = relationship("ProjectRecommendation", back_populates="user", cascade="all, delete-orphan")
    interview_sessions: Mapped[List["InterviewSession"]] = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
