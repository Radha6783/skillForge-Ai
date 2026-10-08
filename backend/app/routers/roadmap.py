"""
API Router for Phase 7: Personalized Learning Roadmap endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.roadmap import (
    RoadmapResponse,
    RoadmapListItem,
    RoadmapItemResponse,
    RoadmapItemUpdate,
    RoadmapProgressSummary,
)
from app.services.roadmap_service import (
    generate_personalized_roadmap,
    get_user_roadmaps,
    get_roadmap_by_id,
    update_roadmap_item_status,
    delete_roadmap,
    get_roadmap_progress_summary,
    format_roadmap_response,
)

router = APIRouter(prefix="/api/roadmaps", tags=["roadmaps"])


@router.post("/generate/{job_analysis_id}", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
def generate_roadmap_endpoint(
    job_analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a personalized week-by-week learning roadmap based on the user's
    skill gaps for a specific JobAnalysis.
    """
    roadmap = generate_personalized_roadmap(
        job_analysis_id=job_analysis_id,
        user_id=current_user.id,
        db=db
    )

    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found or does not belong to you."
        )

    return format_roadmap_response(roadmap)


@router.get("", response_model=List[RoadmapListItem])
def list_roadmaps_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all learning roadmaps created by the current user.
    """
    return get_user_roadmaps(user_id=current_user.id, db=db)


@router.get("/summary/progress", response_model=RoadmapProgressSummary)
def get_roadmap_progress_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated roadmap progress metrics for the authenticated user.
    """
    return get_roadmap_progress_summary(user_id=current_user.id, db=db)


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
def get_roadmap_endpoint(
    roadmap_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full details and weekly curriculum for a specific roadmap. Enforces ownership.
    """
    roadmap = get_roadmap_by_id(roadmap_id=roadmap_id, user_id=current_user.id, db=db)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found or does not belong to you."
        )
    return format_roadmap_response(roadmap)


@router.patch("/{roadmap_id}/items/{item_id}", response_model=RoadmapItemResponse)
def update_item_status_endpoint(
    roadmap_id: int,
    item_id: int,
    item_update: RoadmapItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the completion status of an individual roadmap weekly item.
    Enforces user ownership on both the roadmap and the item.
    """
    item = update_roadmap_item_status(
        roadmap_id=roadmap_id,
        item_id=item_id,
        is_completed=item_update.is_completed,
        user_id=current_user.id,
        db=db
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap item not found or does not belong to you."
        )

    return RoadmapItemResponse(
        id=item.id,
        week_number=item.week_number,
        skill_name=item.skill_name,
        topic=item.topic,
        priority=item.priority,
        estimated_hours=item.estimated_hours,
        learning_objectives=item.learning_objectives,
        practice_task=item.practice_task,
        suggested_project=item.suggested_project,
        is_completed=item.is_completed,
        completed_at=item.completed_at
    )


@router.delete("/{roadmap_id}", status_code=status.HTTP_200_OK)
def delete_roadmap_endpoint(
    roadmap_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a roadmap and all of its items. Enforces user ownership.
    """
    success = delete_roadmap(roadmap_id=roadmap_id, user_id=current_user.id, db=db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found or does not belong to you."
        )

    return {"message": "Roadmap deleted successfully", "id": roadmap_id}
