"""
Phase 10: API Router for Career Readiness Score and Advanced Dashboard.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.career_readiness import (
    CareerReadinessResponse,
    TargetRoleResponse,
)
from app.services import career_readiness_service

router = APIRouter(
    prefix="/api/career-readiness",
    tags=["Career Readiness"]
)


@router.get(
    "/target-roles",
    response_model=List[TargetRoleResponse],
    summary="Get all analyzed target jobs for the authenticated user"
)
def get_target_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns a lightweight list of the user's analyzed jobs (ordered newest first)
    for the Dashboard target job selector dropdown.
    """
    return career_readiness_service.get_user_target_roles_service(
        user=current_user,
        db=db
    )


@router.get(
    "",
    response_model=CareerReadinessResponse,
    summary="Get overall career readiness for the latest analyzed job"
)
def get_latest_career_readiness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculates and returns the 4-pillar Career Readiness score for the candidate's
    most recent target job analysis.
    """
    return career_readiness_service.calculate_career_readiness(
        user=current_user,
        db=db,
        job_analysis_id=None
    )


@router.get(
    "/{job_analysis_id}",
    response_model=CareerReadinessResponse,
    summary="Get career readiness score specifically for a job analysis"
)
def get_job_specific_career_readiness(
    job_analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculates and returns the 4-pillar Career Readiness score grounded
    specifically in the provided job_analysis_id.
    """
    return career_readiness_service.calculate_career_readiness(
        user=current_user,
        db=db,
        job_analysis_id=job_analysis_id
    )
