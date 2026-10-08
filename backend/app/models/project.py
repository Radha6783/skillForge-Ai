from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class ProjectRecommendation(Base):
    __tablename__ = "project_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_analysis_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("job_analyses.id", ondelete="SET NULL"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    skills_practiced: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    why_recommended: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, default=10, nullable=True)
    expected_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resume_bullet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="project_recommendations")
    job_analysis: Mapped[Optional["JobAnalysis"]] = relationship("JobAnalysis", back_populates="project_recommendations")

    def __repr__(self):
        return f"<ProjectRecommendation(id={self.id}, title='{self.title}', difficulty='{self.difficulty}')>"

