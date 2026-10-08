"""
Pydantic schemas for Job Analyzer endpoints.

Covers:
- JobAnalysisCreate: input for creating a new analysis
- AnalysisResultSchema: structured AI analysis output
- JobRequirementResponse: individual skill requirement
- JobAnalysisResponse: full analysis record with requirements
- JobAnalysisListItem: lightweight item for history list
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class JobAnalysisCreate(BaseModel):
    """User input for analyzing a job description."""
    job_description: str = Field(
        ...,
        min_length=50,
        max_length=15000,
        description="The full job description text to analyze"
    )
    job_title: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional job title override (AI will extract if not provided)"
    )
    company_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional company name"
    )

    @field_validator("job_description")
    @classmethod
    def validate_job_description(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 50:
            raise ValueError(
                "Job description must be at least 50 characters long. "
                "Please paste a complete job listing."
            )
        return cleaned


class AnalysisResultSchema(BaseModel):
    """Structured output from AI analysis of a job description."""
    job_title: str = ""
    summary: str = ""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud_and_devops: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    experience_requirements: List[str] = Field(default_factory=list)
    education_requirements: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class JobRequirementResponse(BaseModel):
    """Response schema for an extracted job requirement."""
    id: int
    skill_name: str
    category: Optional[str] = None
    is_required: bool = True
    importance_level: Optional[str] = "HIGH"

    class Config:
        from_attributes = True


class JobAnalysisResponse(BaseModel):
    """Full job analysis response including structured results and requirements."""
    id: int
    user_id: int
    job_title: str
    company_name: Optional[str] = None
    raw_description: str
    role_category: Optional[str] = None
    analysis_result: Optional[AnalysisResultSchema] = None
    requirements: List[JobRequirementResponse] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class JobAnalysisListItem(BaseModel):
    """Lightweight schema for history list view."""
    id: int
    job_title: str
    company_name: Optional[str] = None
    role_category: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
