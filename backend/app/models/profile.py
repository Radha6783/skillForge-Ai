from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    college: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    degree: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile(id={self.id}, user_id={self.user_id}, target_role='{self.target_role}')>"
