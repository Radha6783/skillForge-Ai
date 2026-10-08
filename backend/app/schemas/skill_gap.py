"""
Pydantic schemas for Phase 6: Skill Gap Analysis endpoints and responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnalyzedSkillItem(BaseModel):
    """Detailed object representing a single skill comparison result."""
    skill_name: str
    status: str = Field(..., description="MATCHED | PARTIAL_GAP | MISSING")
    user_level: str = Field(..., description="NOT_ADDED | BEGINNER | INTERMEDIATE | ADVANCED | EXPERT")
    required_level: str = Field(..., description="BEGINNER | INTERMEDIATE | ADVANCED | EXPERT")
    gap_delta: int = Field(..., description="required_numeric_level - user_numeric_level (0 or negative if matched)")
    priority: str = Field(..., description="HIGH | MEDIUM | LOW")
    is_required: bool = True
    importance_level: str = "HIGH"
    category: Optional[str] = "Technical"

    class Config:
        from_attributes = True


class SkillGapReportResponse(BaseModel):
    """Full Skill Gap Report response schema."""
    id: int
    user_id: int
    job_analysis_id: int
    overall_match_percentage: float
    matching_skills: List[AnalyzedSkillItem] = Field(default_factory=list)
    weak_skills: List[AnalyzedSkillItem] = Field(default_factory=list)
    missing_skills: List[AnalyzedSkillItem] = Field(default_factory=list)
    recommended_skills: List[AnalyzedSkillItem] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class SkillGapSummaryResponse(BaseModel):
    """Summary statistics for the authenticated user across all analyzed jobs."""
    total_analyzed_jobs: int
    average_match_percentage: float
    highest_match_percentage: float
    lowest_match_percentage: float
    total_unique_missing_skills: int
    total_unique_weak_skills: int
    total_matched_skills: int
