"""
Phase 9: AI Project Recommendation Service.

Handles business logic for:
- JobAnalysis ownership verification
- SkillGapReport extraction
- AI-driven & fallback recommendation generation
- Database persistence and safe regeneration
- Completion tracking and deletion
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.job_analysis import JobAnalysis, SkillGapReport
from app.models.project import ProjectRecommendation
from app.services.skill_gap_service import calculate_skill_gap
from app.services.ai_service import generate_project_recommendations_ai
from app.schemas.project import (
    ProjectRecommendationResponse,
    ProjectRecommendationListResponse,
)


def _format_list_response(
    job_analysis: Optional[JobAnalysis],
    projects: List[ProjectRecommendation]
) -> ProjectRecommendationListResponse:
    """Formats a list of ProjectRecommendation DB models into a response schema."""
    total = len(projects)
    completed = sum(1 for p in projects if p.is_completed)
    
    project_responses = [
        ProjectRecommendationResponse.model_validate(p)
        for p in projects
    ]

    return ProjectRecommendationListResponse(
        job_analysis_id=job_analysis.id if job_analysis else None,
        job_title=job_analysis.job_title if job_analysis else None,
        target_role=job_analysis.role_category or job_analysis.job_title if job_analysis else None,
        total_projects=total,
        completed_projects=completed,
        projects=project_responses
    )


def generate_project_recommendations_service(
    user: User,
    job_analysis_id: int,
    db: Session
) -> ProjectRecommendationListResponse:
    """
    Generates personalized project recommendations for a specific JobAnalysis grounded in skill gaps.
    Replaces existing recommendations for this specific JobAnalysis.
    """
    # 1. Verify JobAnalysis ownership
    job_analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.id == job_analysis_id, JobAnalysis.user_id == user.id)
        .first()
    )
    if not job_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found or access denied"
        )

    # 2. Get or calculate SkillGapReport
    skill_gap_report = (
        db.query(SkillGapReport)
        .filter(SkillGapReport.job_analysis_id == job_analysis_id, SkillGapReport.user_id == user.id)
        .first()
    )
    if not skill_gap_report:
        skill_gap_report = calculate_skill_gap(job_analysis_id, user.id, db)

    missing_skills = skill_gap_report.missing_skills or []
    weak_skills = skill_gap_report.weak_skills or []

    # 3. Call AI / Fallback generator
    experience_level = "MID"
    if user.profile and user.profile.experience_level:
        experience_level = user.profile.experience_level

    raw_projects = generate_project_recommendations_ai(
        target_role=job_analysis.role_category or job_analysis.job_title,
        experience_level=experience_level,
        job_title=job_analysis.job_title,
        job_requirements=[r.skill_name for r in job_analysis.requirements],
        missing_skills=missing_skills,
        weak_skills=weak_skills,
    )

    # 4. Safely replace previous generated recommendations for THIS specific job_analysis_id only
    db.query(ProjectRecommendation).filter(
        ProjectRecommendation.user_id == user.id,
        ProjectRecommendation.job_analysis_id == job_analysis_id
    ).delete(synchronize_session=False)

    # 5. Persist new ProjectRecommendation records
    new_records: List[ProjectRecommendation] = []
    for proj in raw_projects:
        rec = ProjectRecommendation(
            user_id=user.id,
            job_analysis_id=job_analysis_id,
            title=proj.get("title", "Portfolio Project"),
            difficulty=proj.get("difficulty", "INTERMEDIATE"),
            skills_practiced=proj.get("skills_practiced", []),
            description=proj.get("description", ""),
            why_recommended=proj.get("why_recommended", ""),
            estimated_hours=proj.get("estimated_hours", 10),
            expected_outcome=proj.get("expected_outcome", ""),
            resume_bullet=proj.get("resume_bullet", ""),
            is_completed=False,
        )
        db.add(rec)
        new_records.append(rec)

    db.commit()
    for rec in new_records:
        db.refresh(rec)

    return _format_list_response(job_analysis, new_records)


def get_project_recommendations_service(
    user: User,
    job_analysis_id: int,
    db: Session
) -> ProjectRecommendationListResponse:
    """
    Retrieves existing recommendations for a JobAnalysis, or generates them if none exist.
    """
    # 1. Verify JobAnalysis ownership
    job_analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.id == job_analysis_id, JobAnalysis.user_id == user.id)
        .first()
    )
    if not job_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found or access denied"
        )

    # 2. Query existing project recommendations
    existing = (
        db.query(ProjectRecommendation)
        .filter(
            ProjectRecommendation.user_id == user.id,
            ProjectRecommendation.job_analysis_id == job_analysis_id
        )
        .order_by(ProjectRecommendation.id.asc())
        .all()
    )

    if existing:
        return _format_list_response(job_analysis, existing)

    # 3. If none exist, generate them automatically
    return generate_project_recommendations_service(user, job_analysis_id, db)


def toggle_project_recommendation_complete_service(
    user: User,
    recommendation_id: int,
    is_completed: bool,
    db: Session
) -> ProjectRecommendationResponse:
    """Toggles completion status for a recommendation owned by the current user."""
    rec = (
        db.query(ProjectRecommendation)
        .filter(ProjectRecommendation.id == recommendation_id, ProjectRecommendation.user_id == user.id)
        .first()
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project recommendation not found or access denied"
        )

    rec.is_completed = is_completed
    db.commit()
    db.refresh(rec)
    return ProjectRecommendationResponse.model_validate(rec)


def delete_project_recommendations_service(
    user: User,
    job_analysis_id: int,
    db: Session
) -> bool:
    """Deletes project recommendations for a specific JobAnalysis."""
    job_analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.id == job_analysis_id, JobAnalysis.user_id == user.id)
        .first()
    )
    if not job_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found or access denied"
        )

    db.query(ProjectRecommendation).filter(
        ProjectRecommendation.user_id == user.id,
        ProjectRecommendation.job_analysis_id == job_analysis_id
    ).delete(synchronize_session=False)

    db.commit()
    return True


def get_user_recent_projects_service(
    user: User,
    db: Session,
    limit: int = 5
) -> List[ProjectRecommendationResponse]:
    """Retrieves recent project recommendations for dashboard display across all user job analyses."""
    records = (
        db.query(ProjectRecommendation)
        .filter(ProjectRecommendation.user_id == user.id)
        .order_by(ProjectRecommendation.created_at.desc())
        .limit(limit)
        .all()
    )
    return [ProjectRecommendationResponse.model_validate(r) for r in records]
