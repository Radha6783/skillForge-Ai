from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_analysis_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("job_analyses.id", ondelete="SET NULL"), nullable=True)
    
    target_role: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(50), default="MIXED", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    summary_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="IN_PROGRESS", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="interview_sessions")
    job_analysis: Mapped[Optional["JobAnalysis"]] = relationship("JobAnalysis", back_populates="interview_sessions")
    questions: Mapped[List["InterviewQuestion"]] = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InterviewSession(id={self.id}, role='{self.target_role}', topic='{self.topic}')>"


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    skill_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expected_key_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="questions")
    answer: Mapped[Optional["InterviewAnswer"]] = relationship("InterviewAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InterviewQuestion(id={self.id}, session_id={self.session_id}, order={self.question_order})>"


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview_questions.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    correctness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    technical_depth_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    clarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvement_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topics_to_revise: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationship
    question: Mapped["InterviewQuestion"] = relationship("InterviewQuestion", back_populates="answer")

    def __repr__(self):
        return f"<InterviewAnswer(id={self.id}, question_id={self.question_id}, score={self.score})>"
