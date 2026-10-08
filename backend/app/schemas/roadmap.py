"""
Pydantic schemas for Phase 7: Personalized Learning Roadmap.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class RoadmapItemResponse(BaseModel):
    """Schema for an individual roadmap weekly item."""
    id: int
    week_number: int
    skill_name: Optional[str] = None
    topic: str
    priority: Optional[str] = "MEDIUM"
    estimated_hours: Optional[int] = 10
    learning_objectives: Optional[str] = None
    practice_task: Optional[str] = None
    suggested_project: Optional[str] = None
    is_completed: bool = False
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoadmapItemUpdate(BaseModel):
    """Schema for updating roadmap item completion status."""
    is_completed: bool


class RoadmapResponse(BaseModel):
    """Full roadmap response schema including progress metrics."""
    id: int
    title: str
    description: Optional[str] = None
    target_role: str
    job_analysis_id: Optional[int] = None
    total_weeks: int
    created_at: datetime
    updated_at: datetime
    items: List[RoadmapItemResponse] = Field(default_factory=list)
    total_items: int = 0
    completed_items: int = 0
    completion_percentage: float = 0.0

    class Config:
        from_attributes = True


class RoadmapListItem(BaseModel):
    """Lightweight roadmap schema for history/listing views."""
    id: int
    title: str
    description: Optional[str] = None
    target_role: str
    job_analysis_id: Optional[int] = None
    total_weeks: int
    created_at: datetime
    total_items: int = 0
    completed_items: int = 0
    completion_percentage: float = 0.0

    class Config:
        from_attributes = True


class RoadmapProgressSummary(BaseModel):
    """Aggregated roadmap progress metrics for user dashboard."""
    active_roadmap: Optional[RoadmapListItem] = None
    total_roadmaps: int = 0
    total_items: int = 0
    completed_items: int = 0
    completion_percentage: float = 0.0
