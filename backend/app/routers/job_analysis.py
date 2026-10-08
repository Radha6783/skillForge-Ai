"""
Router for Job Description Analysis and Skill Extraction endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.job_analysis import JobAnalysis, JobRequirement, SkillGapReport
from app.models.skill import UserSkill, Skill
from app.schemas.job_analysis import (
    JobAnalysisCreate,
    JobAnalysisResponse,
    JobAnalysisListItem,
    AnalysisResultSchema,
    JobRequirementResponse
)
from app.dependencies.auth import get_current_user
from app.services.ai_service import analyze_job_description

router = APIRouter(prefix="/api/job-analysis", tags=["job-analysis"])


@router.post("/analyze", response_model=JobAnalysisResponse, status_code=status.HTTP_201_CREATED)
def analyze_job(
    analysis_in: JobAnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a job description text using AI skill extraction.
    Saves the job analysis, individual requirement entries, and computes initial skill match.
    """
    # 1. Run AI / Heuristic Analysis
    ai_result: AnalysisResultSchema = analyze_job_description(
        job_description=analysis_in.job_description,
        job_title_hint=analysis_in.job_title
    )

    resolved_title = analysis_in.job_title or ai_result.job_title or "Job Position"
    
    # Simple role category inference
    role_cat = "Software Engineering"
    title_lower = resolved_title.lower()
    if "data" in title_lower or "ai" in title_lower or "ml" in title_lower:
        role_cat = "Data & AI"
    elif "devops" in title_lower or "cloud" in title_lower or "sre" in title_lower:
        role_cat = "DevOps & Cloud"
    elif "frontend" in title_lower or "ui" in title_lower or "react" in title_lower:
        role_cat = "Frontend Engineering"
    elif "backend" in title_lower or "api" in title_lower:
        role_cat = "Backend Engineering"

    # 2. Create JobAnalysis Record
    job_analysis = JobAnalysis(
        user_id=current_user.id,
        job_title=resolved_title,
        company_name=analysis_in.company_name,
        raw_description=analysis_in.job_description,
        role_category=role_cat,
        analysis_result=ai_result.model_dump()
    )
    db.add(job_analysis)
    db.flush()  # populate job_analysis.id

    # 3. Create JobRequirement Records
    requirements_to_add = []
    
    # Required skills
    for skill_name in ai_result.required_skills:
        req = JobRequirement(
            job_analysis_id=job_analysis.id,
            skill_name=skill_name,
            category="Technical",
            is_required=True,
            importance_level="HIGH"
        )
        requirements_to_add.append(req)

    # Preferred / Nice to have skills
    for skill_name in ai_result.preferred_skills:
        # Avoid duplicate skill names if already added in required
        if not any(r.skill_name.lower() == skill_name.lower() for r in requirements_to_add):
            req = JobRequirement(
                job_analysis_id=job_analysis.id,
                skill_name=skill_name,
                category="Technical",
                is_required=False,
                importance_level="MEDIUM"
            )
            requirements_to_add.append(req)

    db.add_all(requirements_to_add)

    # 4. Perform Initial Skill Gap Evaluation against User's Skills Profile
    user_skills = (
        db.query(UserSkill)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == current_user.id)
        .all()
    )

    user_skill_map = {us.skill.name.lower(): us.self_assessed_level for us in user_skills if us.skill}

    matching_skills = []
    missing_skills = []
    weak_skills = []

    all_req_skills = [r.skill_name for r in requirements_to_add]
    for req_skill in all_req_skills:
        req_lower = req_skill.lower()
        if req_lower in user_skill_map:
            level = user_skill_map[req_lower]
            if level in ["BEGINNER"]:
                weak_skills.append({"skill_name": req_skill, "level": level})
            else:
                matching_skills.append({"skill_name": req_skill, "level": level})
        else:
            missing_skills.append({"skill_name": req_skill})

    total_reqs = len(all_req_skills)
    match_pct = round((len(matching_skills) / total_reqs * 100.0), 1) if total_reqs > 0 else 100.0

    gap_report = SkillGapReport(
        user_id=current_user.id,
        job_analysis_id=job_analysis.id,
        overall_match_percentage=match_pct,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        weak_skills=weak_skills,
        recommended_skills=missing_skills[:5]
    )
    db.add(gap_report)

    db.commit()
    db.refresh(job_analysis)

    return _format_job_analysis_response(job_analysis)


@router.get("/history", response_model=List[JobAnalysisListItem])
def get_analysis_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all past job analyses for the current authenticated user.
    """
    analyses = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.user_id == current_user.id)
        .order_by(desc(JobAnalysis.created_at))
        .all()
    )

    items = []
    for a in analyses:
        summary_text = None
        if a.analysis_result and isinstance(a.analysis_result, dict):
            summary_text = a.analysis_result.get("summary")

        items.append(
            JobAnalysisListItem(
                id=a.id,
                job_title=a.job_title,
                company_name=a.company_name,
                role_category=a.role_category,
                summary=summary_text,
                created_at=a.created_at
            )
        )
    return items


@router.get("/{analysis_id}", response_model=JobAnalysisResponse)
def get_analysis_by_id(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific job analysis by ID.
    Enforces user ownership.
    """
    analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.id == analysis_id, JobAnalysis.user_id == current_user.id)
        .first()
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found."
        )

    return _format_job_analysis_response(analysis)


@router.delete("/{analysis_id}", status_code=status.HTTP_200_OK)
def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a job analysis record by ID.
    """
    analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.id == analysis_id, JobAnalysis.user_id == current_user.id)
        .first()
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found."
        )

    db.delete(analysis)
    db.commit()
    return {"message": "Job analysis deleted successfully", "id": analysis_id}


def _format_job_analysis_response(analysis: JobAnalysis) -> JobAnalysisResponse:
    """Helper to convert JobAnalysis ORM model into JobAnalysisResponse Pydantic model."""
    result_schema = None
    if analysis.analysis_result and isinstance(analysis.analysis_result, dict):
        result_schema = AnalysisResultSchema(**analysis.analysis_result)

    req_responses = [
        JobRequirementResponse(
            id=req.id,
            skill_name=req.skill_name,
            category=req.category,
            is_required=req.is_required,
            importance_level=req.importance_level
        )
        for req in (analysis.requirements or [])
    ]

    return JobAnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        job_title=analysis.job_title,
        company_name=analysis.company_name,
        raw_description=analysis.raw_description,
        role_category=analysis.role_category,
        analysis_result=result_schema,
        requirements=req_responses,
        created_at=analysis.created_at
    )
