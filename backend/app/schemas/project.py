"""
Phase 9: Pydantic schemas for Project Recommendations.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectRecommendationBase(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the recommended project")
    difficulty: str = Field("INTERMEDIATE", description="Difficulty level (BEGINNER, INTERMEDIATE, ADVANCED)")
    skills_practiced: List[str] = Field(default_factory=list, description="List of target skills practiced")
    description: Optional[str] = Field(None, description="Detailed project description")
    why_recommended: Optional[str] = Field(None, description="Explanation of why project was recommended")
    estimated_hours: Optional[int] = Field(10, ge=1, description="Estimated completion time in hours")
    expected_outcome: Optional[str] = Field(None, description="Expected learning outcomes/deliverables")
    resume_bullet: Optional[str] = Field(None, description="Suggested resume accomplishment bullet point")

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        valid_levels = {"BEGINNER", "INTERMEDIATE", "ADVANCED"}
        cleaned = (v or "INTERMEDIATE").strip().upper()
        if cleaned not in valid_levels:
            return "INTERMEDIATE"
        return cleaned

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        cleaned = (v or "").strip()
        if not cleaned:
            raise ValueError("Title cannot be empty")
        return cleaned


class ProjectRecommendationResponse(ProjectRecommendationBase):
    id: int
    user_id: int
    job_analysis_id: Optional[int] = None
    is_completed: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectRecommendationListResponse(BaseModel):
    job_analysis_id: Optional[int] = None
    job_title: Optional[str] = None
    target_role: Optional[str] = None
    total_projects: int = 0
    completed_projects: int = 0
    projects: List[ProjectRecommendationResponse] = Field(default_factory=list)


class ProjectRecommendationCompleteRequest(BaseModel):
    is_completed: bool = True
