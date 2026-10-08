"""
Phase 10: Career Readiness Service.

Calculates a deterministic, transparent 4-pillar Career Readiness Score (0-100):
1. Skill Readiness (35%)
2. Roadmap Progress (25%)
3. Interview Readiness (25%)
4. Portfolio Readiness (15%)

Fully grounded in the user's active database state and selected JobAnalysis.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from app.models.user import User
from app.models.job_analysis import JobAnalysis, SkillGapReport
from app.models.roadmap import Roadmap, RoadmapItem
from app.models.interview import InterviewSession
from app.models.project import ProjectRecommendation
from app.services.skill_gap_service import calculate_skill_gap
from app.schemas.career_readiness import (
    CareerReadinessResponse,
    CareerReadinessPillars,
    CareerReadinessPillar,
    NextBestAction,
    TargetRoleResponse,
)


def get_user_target_roles_service(user: User, db: Session) -> List[TargetRoleResponse]:
    """Retrieves all analyzed jobs for the authenticated user ordered newest first."""
    analyses = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.user_id == user.id)
        .order_by(JobAnalysis.created_at.desc())
        .all()
    )
    return [
        TargetRoleResponse(
            id=ja.id,
            job_title=ja.job_title,
            target_role=ja.role_category or ja.job_title,
            company_name=ja.company_name,
            created_at=ja.created_at
        )
        for ja in analyses
    ]


def _get_tier_info(overall_score: float) -> tuple[str, str, Optional[float]]:
    """Calculates tier, tier description, and distance to next tier."""
    if overall_score >= 85.0:
        return (
            "JOB READY / STRONG CANDIDATE",
            "You possess the required technical competencies, verified roadmap progress, interview practice, and portfolio evidence to excel in this role.",
            None
        )
    elif overall_score >= 65.0:
        return (
            "COMPETITIVE / MINOR GAPS",
            "You are a competitive candidate with minor technical or interview areas to refine before application.",
            round(85.0 - overall_score, 1)
        )
    elif overall_score >= 40.0:
        return (
            "IN TRAINING / MODERATE GAPS",
            "You are making steady progress. Focus on prioritized learning modules and hands-on project implementations.",
            round(65.0 - overall_score, 1)
        )
    else:
        return (
            "GETTING STARTED / HIGH GAPS",
            "Foundational gaps identified across key job requirements. Follow your customized roadmap to systematically close them.",
            round(40.0 - overall_score, 1)
        )


def _determine_next_best_action(
    target_role: str,
    job_analysis_id: int,
    skill_score: float,
    high_missing: List[str],
    has_roadmap: bool,
    roadmap_comp_pct: float,
    current_incomplete_week: Optional[int],
    completed_interviews: int,
    interview_avg: float,
    has_projects: bool,
    project_comp_pct: float
) -> NextBestAction:
    """Calculates deterministic next best action based on lowest/highest-impact pillar."""
    if high_missing:
        top_skill = high_missing[0]
        return NextBestAction(
            action_text=f"Focus on your highest-priority missing skill: {top_skill}. Complete related curriculum modules to boost technical alignment.",
            action_type="SKILL",
            destination="/job-analyzer"
        )
    
    if not has_roadmap:
        return NextBestAction(
            action_text=f"Generate your personalized learning roadmap for {target_role} to begin structured preparation.",
            action_type="ROADMAP",
            destination="/roadmaps"
        )

    if roadmap_comp_pct < 100.0:
        wk_str = f"Week {current_incomplete_week}" if current_incomplete_week else "upcoming modules"
        return NextBestAction(
            action_text=f"Complete {wk_str} of your learning roadmap to increase curriculum completion.",
            action_type="ROADMAP",
            destination="/roadmaps"
        )

    if completed_interviews == 0:
        return NextBestAction(
            action_text=f"Complete an AI technical interview simulation grounded in {target_role} requirements.",
            action_type="INTERVIEW",
            destination="/interviews"
        )

    if interview_avg < 75.0:
        return NextBestAction(
            action_text=f"Practice another AI interview session to raise your technical score above 75%.",
            action_type="INTERVIEW",
            destination="/interviews"
        )

    if not has_projects:
        return NextBestAction(
            action_text=f"Generate recommended portfolio capstone projects to establish verified proof-of-work.",
            action_type="PROJECT",
            destination=f"/project-recommendations/{job_analysis_id}"
        )

    if project_comp_pct < 100.0:
        return NextBestAction(
            action_text="Complete your recommended portfolio projects to achieve 100% portfolio readiness.",
            action_type="PROJECT",
            destination=f"/project-recommendations/{job_analysis_id}"
        )

    return NextBestAction(
        action_text="Excellent work! You have maximized all readiness pillars for this target position.",
        action_type="GENERAL",
        destination=None
    )


def calculate_career_readiness(
    user: User,
    db: Session,
    job_analysis_id: Optional[int] = None
) -> CareerReadinessResponse:
    """
    Computes a transparent, deterministic 4-pillar Career Readiness Score for a candidate.
    """
    # 1. Resolve Target JobAnalysis
    job_analysis: Optional[JobAnalysis] = None
    if job_analysis_id is not None:
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
    else:
        # Default to user's most recent JobAnalysis
        job_analysis = (
            db.query(JobAnalysis)
            .filter(JobAnalysis.user_id == user.id)
            .order_by(JobAnalysis.created_at.desc())
            .first()
        )

    # If user has no JobAnalyses at all, return empty state
    if not job_analysis:
        tier, tier_desc, next_pts = _get_tier_info(0.0)
        return CareerReadinessResponse(
            has_target_job=False,
            job_analysis_id=None,
            job_title=None,
            target_role=None,
            overall_score=0.0,
            tier=tier,
            tier_description=tier_desc,
            points_to_next_tier=next_pts,
            pillars=CareerReadinessPillars(
                skill_readiness=CareerReadinessPillar(
                    name="Skill Readiness",
                    score=0.0,
                    weight=0.35,
                    weighted_points=0.0,
                    status="NOT_STARTED",
                    action_cta="Analyze a target job posting to compute skill match.",
                    details={}
                ),
                roadmap_progress=CareerReadinessPillar(
                    name="Roadmap Progress",
                    score=0.0,
                    weight=0.25,
                    weighted_points=0.0,
                    status="NOT_STARTED",
                    action_cta="Generate a learning roadmap.",
                    details={}
                ),
                interview_readiness=CareerReadinessPillar(
                    name="Interview Readiness",
                    score=0.0,
                    weight=0.25,
                    weighted_points=0.0,
                    status="NOT_STARTED",
                    action_cta="Complete your first AI interview simulation.",
                    details={}
                ),
                portfolio_readiness=CareerReadinessPillar(
                    name="Portfolio Readiness",
                    score=0.0,
                    weight=0.15,
                    weighted_points=0.0,
                    status="NOT_STARTED",
                    action_cta="Generate recommended portfolio projects.",
                    details={}
                )
            ),
            formula_breakdown={
                "formula": "Overall = (Skill * 0.35) + (Roadmap * 0.25) + (Interview * 0.25) + (Portfolio * 0.15)",
                "skill_weight": 0.35,
                "roadmap_weight": 0.25,
                "interview_weight": 0.25,
                "portfolio_weight": 0.15,
            },
            next_best_action=NextBestAction(
                action_text="Analyze a target job description to compute your personalized career readiness score.",
                action_type="JOB_ANALYSIS",
                destination="/job-analyzer"
            ),
            summary="No target job analysis selected yet. Submit a job description to get started.",
            skill_summary={},
            roadmap_summary={},
            interview_summary={},
            project_summary={}
        )

    target_role_label = job_analysis.role_category or job_analysis.job_title

    # -------------------------------------------------------------------------
    # Pillar 1: Skill Readiness (35%)
    # -------------------------------------------------------------------------
    skill_gap = (
        db.query(SkillGapReport)
        .filter(SkillGapReport.job_analysis_id == job_analysis.id, SkillGapReport.user_id == user.id)
        .first()
    )
    if not skill_gap:
        skill_gap = calculate_skill_gap(job_analysis.id, user.id, db)

    skill_score = round(max(0.0, min(100.0, float(skill_gap.overall_match_percentage or 0.0))), 1)
    matching_skills = skill_gap.matching_skills or []
    weak_skills = skill_gap.weak_skills or []
    missing_skills = skill_gap.missing_skills or []

    high_missing_names = [
        s.get("skill_name", "") for s in missing_skills
        if isinstance(s, dict) and s.get("priority") == "HIGH" and s.get("skill_name")
    ]

    skill_status = "COMPLETED" if skill_score >= 85.0 else ("IN_PROGRESS" if skill_score > 0.0 else "NOT_STARTED")
    skill_weighted = round(skill_score * 0.35, 1)

    # -------------------------------------------------------------------------
    # Pillar 2: Roadmap Progress (25%)
    # -------------------------------------------------------------------------
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.job_analysis_id == job_analysis.id, Roadmap.user_id == user.id)
        .first()
    )
    has_roadmap = roadmap is not None
    total_roadmap_items = 0
    completed_roadmap_items = 0
    current_incomplete_week: Optional[int] = None

    if has_roadmap and roadmap.items:
        total_roadmap_items = len(roadmap.items)
        completed_roadmap_items = sum(1 for it in roadmap.items if it.is_completed)
        for it in sorted(roadmap.items, key=lambda x: x.week_number):
            if not it.is_completed:
                current_incomplete_week = it.week_number
                break

    roadmap_score = (
        round((completed_roadmap_items / total_roadmap_items * 100.0), 1)
        if total_roadmap_items > 0 else 0.0
    )
    roadmap_status = (
        "COMPLETED" if (total_roadmap_items > 0 and completed_roadmap_items == total_roadmap_items)
        else ("IN_PROGRESS" if completed_roadmap_items > 0 else "NOT_STARTED")
    )
    roadmap_weighted = round(roadmap_score * 0.25, 1)

    # -------------------------------------------------------------------------
    # Pillar 3: Interview Readiness (25%)
    # -------------------------------------------------------------------------
    completed_interviews_list = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.job_analysis_id == job_analysis.id,
            InterviewSession.user_id == user.id,
            InterviewSession.status == "COMPLETED",
            InterviewSession.overall_score.isnot(None)
        )
        .all()
    )
    completed_interviews_count = len(completed_interviews_list)
    interview_avg_score = 0.0
    latest_interview_score: Optional[float] = None

    if completed_interviews_count > 0:
        scores = [float(s.overall_score) for s in completed_interviews_list if s.overall_score is not None]
        if scores:
            interview_avg_score = round(sum(scores) / len(scores), 1)
            latest_interview_score = scores[-1]

    interview_score = max(0.0, min(100.0, interview_avg_score))
    interview_status = (
        "COMPLETED" if (interview_score >= 85.0 and completed_interviews_count > 0)
        else ("IN_PROGRESS" if completed_interviews_count > 0 else "NOT_STARTED")
    )
    interview_weighted = round(interview_score * 0.25, 1)

    # -------------------------------------------------------------------------
    # Pillar 4: Portfolio Readiness (15%)
    # -------------------------------------------------------------------------
    projects = (
        db.query(ProjectRecommendation)
        .filter(
            ProjectRecommendation.job_analysis_id == job_analysis.id,
            ProjectRecommendation.user_id == user.id
        )
        .all()
    )
    has_projects = len(projects) > 0
    total_projects = len(projects)
    completed_projects = sum(1 for p in projects if p.is_completed)

    project_score = (
        round((completed_projects / total_projects * 100.0), 1)
        if total_projects > 0 else 0.0
    )
    project_status = (
        "COMPLETED" if (total_projects > 0 and completed_projects == total_projects)
        else ("IN_PROGRESS" if completed_projects > 0 else "NOT_STARTED")
    )
    project_weighted = round(project_score * 0.15, 1)

    # -------------------------------------------------------------------------
    # Composite Score & Tiers
    # -------------------------------------------------------------------------
    overall_score = round(
        skill_weighted + roadmap_weighted + interview_weighted + project_weighted,
        1
    )
    overall_score = max(0.0, min(100.0, overall_score))
    tier, tier_desc, pts_to_next = _get_tier_info(overall_score)

    next_action = _determine_next_best_action(
        target_role=target_role_label,
        job_analysis_id=job_analysis.id,
        skill_score=skill_score,
        high_missing=high_missing_names,
        has_roadmap=has_roadmap,
        roadmap_comp_pct=roadmap_score,
        current_incomplete_week=current_incomplete_week,
        completed_interviews=completed_interviews_count,
        interview_avg=interview_score,
        has_projects=has_projects,
        project_comp_pct=project_score
    )

    return CareerReadinessResponse(
        has_target_job=True,
        job_analysis_id=job_analysis.id,
        job_title=job_analysis.job_title,
        target_role=target_role_label,
        overall_score=overall_score,
        tier=tier,
        tier_description=tier_desc,
        points_to_next_tier=pts_to_next,
        pillars=CareerReadinessPillars(
            skill_readiness=CareerReadinessPillar(
                name="Skill Readiness",
                score=skill_score,
                weight=0.35,
                weighted_points=skill_weighted,
                status=skill_status,
                action_cta=f"{len(missing_skills)} missing / {len(weak_skills)} partial skills identified.",
                details={
                    "matching_skills_count": len(matching_skills),
                    "weak_skills_count": len(weak_skills),
                    "missing_skills_count": len(missing_skills),
                    "high_priority_missing": high_missing_names[:3]
                }
            ),
            roadmap_progress=CareerReadinessPillar(
                name="Roadmap Progress",
                score=roadmap_score,
                weight=0.25,
                weighted_points=roadmap_weighted,
                status=roadmap_status,
                action_cta=f"{completed_roadmap_items} of {total_roadmap_items} roadmap modules completed." if total_roadmap_items > 0 else "Generate learning roadmap.",
                details={
                    "total_items": total_roadmap_items,
                    "completed_items": completed_roadmap_items,
                    "current_incomplete_week": current_incomplete_week
                }
            ),
            interview_readiness=CareerReadinessPillar(
                name="Interview Readiness",
                score=interview_score,
                weight=0.25,
                weighted_points=interview_weighted,
                status=interview_status,
                action_cta=f"{completed_interviews_count} completed sessions (Avg {interview_avg_score}/100)" if completed_interviews_count > 0 else "Start AI technical interview simulation.",
                details={
                    "completed_sessions": completed_interviews_count,
                    "average_score": interview_avg_score,
                    "latest_score": latest_interview_score
                }
            ),
            portfolio_readiness=CareerReadinessPillar(
                name="Portfolio Readiness",
                score=project_score,
                weight=0.15,
                weighted_points=project_weighted,
                status=project_status,
                action_cta=f"{completed_projects} of {total_projects} portfolio projects completed." if total_projects > 0 else "Generate recommended projects.",
                details={
                    "total_projects": total_projects,
                    "completed_projects": completed_projects
                }
            )
        ),
        formula_breakdown={
            "formula": "(Skill * 0.35) + (Roadmap * 0.25) + (Interview * 0.25) + (Portfolio * 0.15)",
            "skill_points": skill_weighted,
            "roadmap_points": roadmap_weighted,
            "interview_points": interview_weighted,
            "portfolio_points": project_weighted,
            "sum_points": overall_score
        },
        next_best_action=next_action,
        summary=f"You are currently at {overall_score}/100 readiness ({tier}) for {target_role_label}.",
        skill_summary={
            "match_percentage": skill_score,
            "matching_count": len(matching_skills),
            "weak_count": len(weak_skills),
            "missing_count": len(missing_skills)
        },
        roadmap_summary={
            "total_items": total_roadmap_items,
            "completed_items": completed_roadmap_items,
            "completion_percentage": roadmap_score
        },
        interview_summary={
            "completed_sessions": completed_interviews_count,
            "average_score": interview_avg_score
        },
        project_summary={
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "completion_percentage": project_score
        }
    )
