from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    role_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    analysis_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="job_analyses")
    requirements: Mapped[List["JobRequirement"]] = relationship("JobRequirement", back_populates="job_analysis", cascade="all, delete-orphan")
    skill_gap_reports: Mapped[List["SkillGapReport"]] = relationship("SkillGapReport", back_populates="job_analysis", cascade="all, delete-orphan")
    interview_sessions: Mapped[List["InterviewSession"]] = relationship("InterviewSession", back_populates="job_analysis")
    project_recommendations: Mapped[List["ProjectRecommendation"]] = relationship("ProjectRecommendation", back_populates="job_analysis")

    def __repr__(self):
        return f"<JobAnalysis(id={self.id}, job_title='{self.job_title}')>"


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_analyses.id", ondelete="CASCADE"), nullable=False)
    
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    importance_level: Mapped[Optional[str]] = mapped_column(String(50), default="HIGH", nullable=True)

    # Relationship
    job_analysis: Mapped["JobAnalysis"] = relationship("JobAnalysis", back_populates="requirements")

    def __repr__(self):
        return f"<JobRequirement(id={self.id}, skill='{self.skill_name}', is_required={self.is_required})>"


class SkillGapReport(Base):
    __tablename__ = "skill_gap_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_analyses.id", ondelete="CASCADE"), nullable=False)
    
    overall_match_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    matching_skills: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    missing_skills: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    weak_skills: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    recommended_skills: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="skill_gap_reports")
    job_analysis: Mapped["JobAnalysis"] = relationship("JobAnalysis", back_populates="skill_gap_reports")

    def __repr__(self):
        return f"<SkillGapReport(id={self.id}, match={self.overall_match_percentage}%)>"
