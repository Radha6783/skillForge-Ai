"""
Phase 10: Pydantic schemas for Career Readiness Score and Advanced Dashboard.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CareerReadinessPillar(BaseModel):
    name: str
    score: float = Field(..., ge=0.0, le=100.0, description="Pillar score from 0.0 to 100.0")
    weight: float = Field(..., ge=0.0, le=1.0, description="Pillar weight in composite score")
    weighted_points: float = Field(..., ge=0.0, le=100.0, description="Score multiplied by weight")
    status: str = Field("NOT_STARTED", description="COMPLETED, IN_PROGRESS, or NOT_STARTED")
    action_cta: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class CareerReadinessPillars(BaseModel):
    skill_readiness: CareerReadinessPillar
    roadmap_progress: CareerReadinessPillar
    interview_readiness: CareerReadinessPillar
    portfolio_readiness: CareerReadinessPillar


class NextBestAction(BaseModel):
    action_text: str
    action_type: Optional[str] = "GENERAL"
    destination: Optional[str] = None


class TargetRoleResponse(BaseModel):
    id: int
    job_title: str
    target_role: Optional[str] = None
    company_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CareerReadinessResponse(BaseModel):
    has_target_job: bool = True
    job_analysis_id: Optional[int] = None
    job_title: Optional[str] = None
    target_role: Optional[str] = None
    overall_score: float = Field(..., ge=0.0, le=100.0)
    tier: str
    tier_description: str
    points_to_next_tier: Optional[float] = None
    pillars: CareerReadinessPillars
    formula_breakdown: Dict[str, Any]
    next_best_action: Optional[NextBestAction] = None
    summary: str
    skill_summary: Dict[str, Any] = Field(default_factory=dict)
    roadmap_summary: Dict[str, Any] = Field(default_factory=dict)
    interview_summary: Dict[str, Any] = Field(default_factory=dict)
    project_summary: Dict[str, Any] = Field(default_factory=dict)
