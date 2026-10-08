"""
Phase 9: API Router for AI Project Recommendations.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.project import (
    ProjectRecommendationResponse,
    ProjectRecommendationListResponse,
    ProjectRecommendationCompleteRequest,
)
from app.services import project_service

router = APIRouter(
    prefix="/api/project-recommendations",
    tags=["Project Recommendations"]
)


@router.post(
    "/generate/{job_analysis_id}",
    response_model=ProjectRecommendationListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI project recommendations grounded in job skill gaps"
)
def generate_project_recommendations(
    job_analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates 2-3 personalized project recommendations for a specific Job Analysis.
    Replaces previously generated recommendations for that job analysis.
    """
    return project_service.generate_project_recommendations_service(
        user=current_user,
        job_analysis_id=job_analysis_id,
        db=db
    )


@router.get(
    "/recent",
    response_model=List[ProjectRecommendationResponse],
    summary="Get recent project recommendations across all user jobs"
)
def get_recent_project_recommendations(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves recent project recommendations for the authenticated user (for Dashboard display).
    """
    return project_service.get_user_recent_projects_service(
        user=current_user,
        db=db,
        limit=limit
    )


@router.get(
    "/{job_analysis_id}",
    response_model=ProjectRecommendationListResponse,
    summary="Get project recommendations for a job analysis"
)
def get_project_recommendations(
    job_analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves project recommendations for a specific Job Analysis.
    Generates them if none exist yet.
    """
    return project_service.get_project_recommendations_service(
        user=current_user,
        job_analysis_id=job_analysis_id,
        db=db
    )


@router.patch(
    "/{recommendation_id}/complete",
    response_model=ProjectRecommendationResponse,
    summary="Toggle completion status of a project recommendation"
)
def toggle_project_recommendation_complete(
    recommendation_id: int,
    body: ProjectRecommendationCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates the completion status (is_completed) of a specific project recommendation.
    """
    return project_service.toggle_project_recommendation_complete_service(
        user=current_user,
        recommendation_id=recommendation_id,
        is_completed=body.is_completed,
        db=db
    )


@router.delete(
    "/{job_analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project recommendations for a job analysis"
)
def delete_project_recommendations(
    job_analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes all project recommendations associated with a specific Job Analysis.
    """
    project_service.delete_project_recommendations_service(
        user=current_user,
        job_analysis_id=job_analysis_id,
        db=db
    )
    return None
