"""
API Router for Phase 6: Skill Gap Analysis endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.job_analysis import JobAnalysis, SkillGapReport
from app.models.skill import UserSkill
from app.schemas.skill_gap import SkillGapReportResponse, SkillGapSummaryResponse
from app.dependencies.auth import get_current_user
from app.services.skill_gap_service import calculate_skill_gap, get_user_skill_gap_summary

router = APIRouter(prefix="/api/skill-gap", tags=["skill-gap"])


@router.post("/analyze/{job_analysis_id}", response_model=SkillGapReportResponse)
def analyze_skill_gap_endpoint(
    job_analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Computes or refreshes the skill gap analysis for a given JobAnalysis,
    comparing against the user's latest skill inventory.
    """
    job_analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.id == job_analysis_id, JobAnalysis.user_id == current_user.id)
        .first()
    )

    if not job_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found or does not belong to you."
        )

    # Fetch user's latest skills
    user_skills = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == current_user.id)
        .all()
    )

    report = calculate_skill_gap(job_analysis=job_analysis, user_skills=user_skills, db=db)
    return report


@router.get("/report/{job_analysis_id}", response_model=SkillGapReportResponse)
def get_skill_gap_report_endpoint(
    job_analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve existing SkillGapReport for a specific JobAnalysis.
    """
    job_analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.id == job_analysis_id, JobAnalysis.user_id == current_user.id)
        .first()
    )

    if not job_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found."
        )

    report = (
        db.query(SkillGapReport)
        .filter(
            SkillGapReport.job_analysis_id == job_analysis_id,
            SkillGapReport.user_id == current_user.id
        )
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No skill gap report exists for this job analysis yet. Run analyze endpoint first."
        )

    return report


@router.get("/summary", response_model=SkillGapSummaryResponse)
def get_skill_gap_summary_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated skill gap statistics across all job analyses for the current user.
    """
    summary = get_user_skill_gap_summary(user_id=current_user.id, db=db)
    return summary
