from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator

class SkillLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"

class SkillCategory(str, Enum):
    TECHNICAL = "Technical"
    LANGUAGE = "Programming Language"
    FRAMEWORK = "Framework & Library"
    DATABASE = "Database"
    CLOUD = "Cloud & DevOps"
    TOOLS = "Tools & Platforms"
    CS_FUNDAMENTALS = "CS Fundamentals"
    SOFT_SKILLS = "Soft Skills"
    OTHER = "Other"

class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the skill")
    category: Optional[str] = Field("Technical", max_length=100, description="Skill category")

class SkillCreate(SkillBase):
    pass

class SkillResponse(SkillBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserSkillCreate(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100, description="Name of the skill")
    category: Optional[str] = Field("Technical", max_length=100, description="Skill category")
    self_assessed_level: SkillLevel = Field(SkillLevel.BEGINNER, description="Proficiency level")
    experience_months: int = Field(0, ge=0, description="Months of experience with this skill")

    @field_validator("skill_name")
    @classmethod
    def clean_skill_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Skill name cannot be empty")
        return cleaned

class UserSkillUpdate(BaseModel):
    category: Optional[str] = Field(None, max_length=100)
    self_assessed_level: Optional[SkillLevel] = None
    experience_months: Optional[int] = Field(None, ge=0)

class UserSkillResponse(BaseModel):
    id: int
    user_id: int
    skill_id: int
    skill_name: str
    category: Optional[str] = "Technical"
    self_assessed_level: str
    experience_months: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
