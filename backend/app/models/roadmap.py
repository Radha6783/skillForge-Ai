from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_analysis_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("job_analyses.id", ondelete="SET NULL"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_role: Mapped[str] = mapped_column(String(100), nullable=False)
    total_weeks: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="roadmaps")
    job_analysis: Mapped[Optional["JobAnalysis"]] = relationship("JobAnalysis")
    items: Mapped[List["RoadmapItem"]] = relationship("RoadmapItem", back_populates="roadmap", cascade="all, delete-orphan", order_by="RoadmapItem.week_number")

    def __repr__(self):
        return f"<Roadmap(id={self.id}, title='{self.title}', target_role='{self.target_role}')>"


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    roadmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False)
    
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[Optional[str]] = mapped_column(String(50), default="MEDIUM", nullable=True)
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, default=10, nullable=True)
    learning_objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    practice_task: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_project: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="items")

    def __repr__(self):
        return f"<RoadmapItem(id={self.id}, week={self.week_number}, skill='{self.skill_name}', topic='{self.topic}')>"
