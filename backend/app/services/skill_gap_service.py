"""
Phase 6: Skill Gap Analysis Service.

Responsibilities:
- Compare user's actual database skills against job description requirements
- Case-insensitive skill matching
- Weighted match score calculation
- Priority ranking for skill gap resolution
- Persistent SkillGapReport creation/update
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.job_analysis import JobAnalysis, JobRequirement, SkillGapReport
from app.models.skill import UserSkill, Skill
from app.schemas.skill_gap import AnalyzedSkillItem, SkillGapReportResponse, SkillGapSummaryResponse

# Proficiency Level Numeric Mapping
LEVEL_NUMERIC: Dict[str, int] = {
    "NOT_ADDED": 0,
    "BEGINNER": 1,
    "INTERMEDIATE": 2,
    "ADVANCED": 3,
    "EXPERT": 4,
}

NUMERIC_LEVEL: Dict[int, str] = {
    0: "NOT_ADDED",
    1: "BEGINNER",
    2: "INTERMEDIATE",
    3: "ADVANCED",
    4: "EXPERT",
}


def level_to_numeric(level_str: Optional[str]) -> int:
    """Convert level string representation to numeric score (0-4)."""
    if not level_str:
        return 0
    cleaned = level_str.strip().upper()
    return LEVEL_NUMERIC.get(cleaned, 0)


def numeric_to_level(num: int) -> str:
    """Convert numeric score back to level string."""
    return NUMERIC_LEVEL.get(max(0, min(4, num)), "NOT_ADDED")


def determine_required_level(req: JobRequirement) -> Tuple[str, int]:
    """
    Centralized logic to determine the required proficiency level for a job requirement.
    
    Priority:
    1. If explicit level is defined in the requirement (or matched against valid level str), use it.
    2. Otherwise infer from requirement importance & required flag:
       - REQUIRED + HIGH -> ADVANCED (3)
       - REQUIRED + MEDIUM -> INTERMEDIATE (2)
       - REQUIRED + LOW -> INTERMEDIATE (2)
       - PREFERRED + HIGH -> INTERMEDIATE (2)
       - PREFERRED + MEDIUM -> INTERMEDIATE (2)
       - PREFERRED + LOW -> BEGINNER (1)
    """
    is_req = req.is_required
    imp = (req.importance_level or "HIGH").strip().upper()

    if is_req:
        if imp == "HIGH":
            req_str = "ADVANCED"
        elif imp in ["MEDIUM", "LOW"]:
            req_str = "INTERMEDIATE"
        else:
            req_str = "INTERMEDIATE"
    else:
        if imp in ["HIGH", "MEDIUM"]:
            req_str = "INTERMEDIATE"
        else:
            req_str = "BEGINNER"

    return req_str, level_to_numeric(req_str)


def calculate_skill_priority(
    is_required: bool,
    importance_level: str,
    status: str,
    gap_delta: int
) -> str:
    """
    Centralized priority calculation for target skills.
    
    HIGH:
    - Required + HIGH importance + Missing
    - Required + HIGH importance + Large gap (gap_delta >= 2)
    
    MEDIUM:
    - Required + MEDIUM importance
    - Partial gap with gap_delta >= 1
    
    LOW:
    - Preferred skills
    - Small gaps or already MATCHED skills
    """
    imp = (importance_level or "HIGH").strip().upper()

    if is_required and imp == "HIGH" and (status == "MISSING" or gap_delta >= 2):
        return "HIGH"
    if is_required and (imp == "MEDIUM" or status == "PARTIAL_GAP" and gap_delta >= 1):
        return "MEDIUM"
    if status == "PARTIAL_GAP" and is_required:
        return "MEDIUM"
    
    return "LOW"


def get_skill_weight(is_required: bool, importance_level: str) -> float:
    """
    Weighted scoring system:
    - Required + HIGH = 3
    - Required + MEDIUM = 2
    - Required + LOW = 1
    - Preferred + HIGH = 2
    - Preferred + MEDIUM = 1
    - Preferred + LOW = 1
    """
    imp = (importance_level or "HIGH").strip().upper()
    if is_required:
        if imp == "HIGH":
            return 3.0
        elif imp == "MEDIUM":
            return 2.0
        else:
            return 1.0
    else:
        if imp == "HIGH":
            return 2.0
        elif imp == "MEDIUM":
            return 1.0
        else:
            return 1.0


def calculate_skill_gap(
    job_analysis: JobAnalysis,
    user_skills: List[UserSkill],
    db: Session
) -> SkillGapReport:
    """
    Computes a comprehensive skill gap analysis comparing a user's actual database skills
    against job requirements. Updates or creates a persistent SkillGapReport record.
    """
    # 1. Map user skills (case-insensitive name -> user skill record)
    user_skill_map: Dict[str, UserSkill] = {}
    for us in user_skills:
        if us.skill and us.skill.name:
            user_skill_map[us.skill.name.strip().lower()] = us

    # 2. Iterate requirements and evaluate gap for each
    matching_skills: List[Dict[str, Any]] = []
    weak_skills: List[Dict[str, Any]] = []  # Partial Gaps
    missing_skills: List[Dict[str, Any]] = []
    all_analyzed_items: List[Dict[str, Any]] = []

    total_weighted_points = 0.0
    earned_weighted_points = 0.0

    requirements = job_analysis.requirements or []
    
    # If job analysis has no explicit requirement records, fall back to extracted JSON skills
    if not requirements and job_analysis.analysis_result:
        res = job_analysis.analysis_result
        req_skills = res.get("required_skills", [])
        pref_skills = res.get("preferred_skills", [])
        
        for name in req_skills:
            req_item = JobRequirement(
                job_analysis_id=job_analysis.id,
                skill_name=name,
                category="Technical",
                is_required=True,
                importance_level="HIGH"
            )
            requirements.append(req_item)
            
        for name in pref_skills:
            if not any(r.skill_name.lower() == name.lower() for r in requirements):
                req_item = JobRequirement(
                    job_analysis_id=job_analysis.id,
                    skill_name=name,
                    category="Technical",
                    is_required=False,
                    importance_level="MEDIUM"
                )
                requirements.append(req_item)

    for req in requirements:
        skill_key = req.skill_name.strip().lower()
        req_level_str, req_num = determine_required_level(req)
        weight = get_skill_weight(req.is_required, req.importance_level or "HIGH")

        total_weighted_points += weight

        user_sk = user_skill_map.get(skill_key)
        if user_sk:
            user_num = level_to_numeric(user_sk.self_assessed_level)
            user_level_str = user_sk.self_assessed_level.upper()
        else:
            user_num = 0
            user_level_str = "NOT_ADDED"

        # Determine Status
        if user_num >= req_num:
            status = "MATCHED"
            raw_gap = 0
            earned_points = 1.0 * weight
        elif user_num > 0:
            status = "PARTIAL_GAP"
            raw_gap = req_num - user_num
            earned_points = (user_num / float(req_num)) * weight
        else:
            status = "MISSING"
            raw_gap = req_num
            earned_points = 0.0

        earned_weighted_points += earned_points

        priority = calculate_skill_priority(
            is_required=req.is_required,
            importance_level=req.importance_level or "HIGH",
            status=status,
            gap_delta=raw_gap
        )

        item_dict = {
            "skill_name": req.skill_name,
            "status": status,
            "user_level": user_level_str,
            "required_level": req_level_str,
            "gap_delta": max(0, raw_gap),
            "priority": priority,
            "is_required": req.is_required,
            "importance_level": req.importance_level or "HIGH",
            "category": req.category or "Technical",
        }

        all_analyzed_items.append(item_dict)

        if status == "MATCHED":
            matching_skills.append(item_dict)
        elif status == "PARTIAL_GAP":
            weak_skills.append(item_dict)
        else:
            missing_skills.append(item_dict)

    # 3. Calculate Overall Weighted Match Percentage
    if total_weighted_points > 0:
        match_pct = round((earned_weighted_points / total_weighted_points) * 100.0, 1)
        match_pct = max(0.0, min(100.0, match_pct))
    else:
        match_pct = 100.0

    # 4. Determine Prioritized Recommended Skills (Top High & Medium Priority Missing/Weak Skills)
    unmatched_items = missing_skills + weak_skills
    priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
    sorted_recommendations = sorted(
        unmatched_items,
        key=lambda x: (
            priority_order.get(x["priority"], 3),
            0 if x["is_required"] else 1,
            -x["gap_delta"]
        )
    )
    recommended_skills = sorted_recommendations[:8]

    # 5. Save or Update SkillGapReport in Database
    existing_report = (
        db.query(SkillGapReport)
        .filter(
            SkillGapReport.user_id == job_analysis.user_id,
            SkillGapReport.job_analysis_id == job_analysis.id
        )
        .first()
    )

    if existing_report:
        existing_report.overall_match_percentage = match_pct
        existing_report.matching_skills = matching_skills
        existing_report.weak_skills = weak_skills
        existing_report.missing_skills = missing_skills
        existing_report.recommended_skills = recommended_skills
        report_record = existing_report
    else:
        report_record = SkillGapReport(
            user_id=job_analysis.user_id,
            job_analysis_id=job_analysis.id,
            overall_match_percentage=match_pct,
            matching_skills=matching_skills,
            weak_skills=weak_skills,
            missing_skills=missing_skills,
            recommended_skills=recommended_skills
        )
        db.add(report_record)

    db.commit()
    db.refresh(report_record)
    return report_record


def get_user_skill_gap_summary(user_id: int, db: Session) -> SkillGapSummaryResponse:
    """
    Computes summary statistics across all job analysis reports for a given user.
    """
    reports = (
        db.query(SkillGapReport)
        .filter(SkillGapReport.user_id == user_id)
        .all()
    )

    if not reports:
        return SkillGapSummaryResponse(
            total_analyzed_jobs=0,
            average_match_percentage=0.0,
            highest_match_percentage=0.0,
            lowest_match_percentage=0.0,
            total_unique_missing_skills=0,
            total_unique_weak_skills=0,
            total_matched_skills=0,
        )

    match_pcts = [r.overall_match_percentage for r in reports]
    avg_pct = round(sum(match_pcts) / len(match_pcts), 1)
    high_pct = round(max(match_pcts), 1)
    low_pct = round(min(match_pcts), 1)

    unique_missing = set()
    unique_weak = set()
    unique_matched = set()

    for r in reports:
        for item in (r.missing_skills or []):
            if isinstance(item, dict) and "skill_name" in item:
                unique_missing.add(item["skill_name"].lower())
        for item in (r.weak_skills or []):
            if isinstance(item, dict) and "skill_name" in item:
                unique_weak.add(item["skill_name"].lower())
        for item in (r.matching_skills or []):
            if isinstance(item, dict) and "skill_name" in item:
                unique_matched.add(item["skill_name"].lower())

    return SkillGapSummaryResponse(
        total_analyzed_jobs=len(reports),
        average_match_percentage=avg_pct,
        highest_match_percentage=high_pct,
        lowest_match_percentage=low_pct,
        total_unique_missing_skills=len(unique_missing),
        total_unique_weak_skills=len(unique_weak),
        total_matched_skills=len(unique_matched),
    )
