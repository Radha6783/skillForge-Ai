from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user_skills: Mapped[List["UserSkill"]] = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}', category='{self.category}')>"


class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    
    # BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    self_assessed_level: Mapped[str] = mapped_column(String(50), default="BEGINNER", nullable=False)
    experience_months: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="user_skills")

    def __repr__(self):
        return f"<UserSkill(user_id={self.user_id}, skill_id={self.skill_id}, level='{self.self_assessed_level}')>"
