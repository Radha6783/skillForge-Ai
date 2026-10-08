"""
Phase 7: Personalized Learning Roadmap Service.

Responsibilities:
- Extract and prioritize skill gaps for a given JobAnalysis
- Deduplicate and prioritize:
  1. HIGH missing
  2. MEDIUM missing
  3. LOW missing
  4. HIGH partial
  5. MEDIUM partial
  6. LOW partial
- Generate structured week-by-week curriculum via AI service with deterministic fallback
- Persist Roadmap and RoadmapItems
- Progress tracking and completion status updates
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.job_analysis import JobAnalysis, SkillGapReport
from app.models.skill import UserSkill
from app.models.roadmap import Roadmap, RoadmapItem
from app.services.skill_gap_service import calculate_skill_gap
from app.services.ai_service import generate_roadmap_ai
from app.schemas.roadmap import (
    RoadmapResponse,
    RoadmapItemResponse,
    RoadmapListItem,
    RoadmapProgressSummary,
)


def format_roadmap_response(roadmap: Roadmap) -> RoadmapResponse:
    """Computes completion statistics and maps Roadmap model to RoadmapResponse."""
    items_list = roadmap.items or []
    total_items = len(items_list)
    completed_items = sum(1 for it in items_list if it.is_completed)
    completion_pct = round((completed_items / total_items * 100.0), 1) if total_items > 0 else 0.0

    item_responses = [
        RoadmapItemResponse(
            id=it.id,
            week_number=it.week_number,
            skill_name=it.skill_name,
            topic=it.topic,
            priority=it.priority,
            estimated_hours=it.estimated_hours,
            learning_objectives=it.learning_objectives,
            practice_task=it.practice_task,
            suggested_project=it.suggested_project,
            is_completed=it.is_completed,
            completed_at=it.completed_at
        )
        for it in items_list
    ]

    return RoadmapResponse(
        id=roadmap.id,
        title=roadmap.title,
        description=roadmap.description,
        target_role=roadmap.target_role,
        job_analysis_id=roadmap.job_analysis_id,
        total_weeks=roadmap.total_weeks,
        created_at=roadmap.created_at,
        updated_at=roadmap.updated_at,
        items=item_responses,
        total_items=total_items,
        completed_items=completed_items,
        completion_percentage=completion_pct
    )


def format_roadmap_list_item(roadmap: Roadmap) -> RoadmapListItem:
    """Helper to convert Roadmap ORM model to lightweight RoadmapListItem."""
    items_list = roadmap.items or []
    total_items = len(items_list)
    completed_items = sum(1 for it in items_list if it.is_completed)
    completion_pct = round((completed_items / total_items * 100.0), 1) if total_items > 0 else 0.0

    return RoadmapListItem(
        id=roadmap.id,
        title=roadmap.title,
        description=roadmap.description,
        target_role=roadmap.target_role,
        job_analysis_id=roadmap.job_analysis_id,
        total_weeks=roadmap.total_weeks,
        created_at=roadmap.created_at,
        total_items=total_items,
        completed_items=completed_items,
        completion_percentage=completion_pct
    )


def generate_personalized_roadmap(
    job_analysis_id: int,
    user_id: int,
    db: Session
) -> Roadmap:
    """
    Generates and persists a customized learning roadmap targeting the user's specific gaps
    for a selected job analysis.
    """
    # 1. Load JobAnalysis and verify ownership
    job_analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.id == job_analysis_id, JobAnalysis.user_id == user_id)
        .first()
    )
    if not job_analysis:
        return None

    # 2. Load latest SkillGapReport or compute if missing
    gap_report = (
        db.query(SkillGapReport)
        .filter(SkillGapReport.job_analysis_id == job_analysis_id, SkillGapReport.user_id == user_id)
        .first()
    )

    if not gap_report:
        user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
        gap_report = calculate_skill_gap(job_analysis, user_skills, db)

    # 3. Extract and prioritize skill gaps
    missing_items = gap_report.missing_skills or []
    weak_items = gap_report.weak_skills or []

    # Priority Rank Helper:
    # 1: HIGH missing, 2: MEDIUM missing, 3: LOW missing
    # 4: HIGH partial, 5: MEDIUM partial, 6: LOW partial
    priority_map = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}

    prioritized_list = []
    seen_skills = set()

    # Process Missing Skills
    sorted_missing = sorted(
        missing_items,
        key=lambda x: priority_map.get((x.get("priority") or "MEDIUM").upper(), 2)
    )
    for m in sorted_missing:
        name = m.get("skill_name", "").strip()
        norm = name.lower()
        if norm and norm not in seen_skills:
            seen_skills.add(norm)
            prioritized_list.append({
                "skill_name": name,
                "status": "MISSING",
                "priority": (m.get("priority") or "HIGH").upper(),
                "required_level": m.get("required_level", "INTERMEDIATE"),
                "user_level": "NOT_ADDED"
            })

    # Process Partial-Gap Skills
    sorted_weak = sorted(
        weak_items,
        key=lambda x: priority_map.get((x.get("priority") or "MEDIUM").upper(), 2)
    )
    for w in sorted_weak:
        name = w.get("skill_name", "").strip()
        norm = name.lower()
        if norm and norm not in seen_skills:
            seen_skills.add(norm)
            prioritized_list.append({
                "skill_name": name,
                "status": "PARTIAL_GAP",
                "priority": (w.get("priority") or "MEDIUM").upper(),
                "required_level": w.get("required_level", "INTERMEDIATE"),
                "user_level": w.get("user_level", "BEGINNER")
            })

    # Select up to top 8 skills for an achievable roadmap
    top_gaps = prioritized_list[:8]

    # If user has zero gaps (all matched), include target role mastery
    if not top_gaps:
        top_gaps = [{
            "skill_name": job_analysis.job_title,
            "status": "MASTERY",
            "priority": "HIGH",
            "required_level": "ADVANCED",
            "user_level": "ADVANCED"
        }]

    target_role = job_analysis.role_category or job_analysis.job_title

    # 4. Generate structured roadmap through AI service with deterministic fallback
    generated_content = generate_roadmap_ai(
        target_role=target_role,
        job_title=job_analysis.job_title,
        gap_skills=top_gaps
    )

    roadmap_title = generated_content.get("title") or f"{job_analysis.job_title} Accelerated Roadmap"
    roadmap_desc = generated_content.get("description") or "Personalized career roadmap targeting your verified skill gaps."
    total_weeks = generated_content.get("total_weeks") or len(generated_content.get("weekly_phases", []))
    total_weeks = max(1, total_weeks)

    # 5. Persist Roadmap
    roadmap = Roadmap(
        user_id=user_id,
        job_analysis_id=job_analysis.id,
        title=roadmap_title,
        description=roadmap_desc,
        target_role=target_role,
        total_weeks=total_weeks
    )
    db.add(roadmap)
    db.flush()

    # 6. Persist Roadmap Items
    phases = generated_content.get("weekly_phases", [])
    roadmap_items = []

    for idx, p in enumerate(phases):
        week_num = p.get("week_number") or (idx + 1)
        r_item = RoadmapItem(
            roadmap_id=roadmap.id,
            week_number=week_num,
            skill_name=p.get("skill_name"),
            topic=p.get("topic") or f"Week {week_num} Mastery",
            priority=p.get("priority", "MEDIUM"),
            estimated_hours=p.get("estimated_hours", 10),
            learning_objectives=p.get("learning_objectives"),
            practice_task=p.get("practice_task"),
            suggested_project=p.get("suggested_project"),
            is_completed=False,
            completed_at=None
        )
        roadmap_items.append(r_item)

    db.add_all(roadmap_items)
    db.commit()
    db.refresh(roadmap)

    return roadmap


def get_user_roadmaps(user_id: int, db: Session) -> List[RoadmapListItem]:
    """Retrieve all roadmaps created by the current user."""
    roadmaps = (
        db.query(Roadmap)
        .filter(Roadmap.user_id == user_id)
        .order_by(desc(Roadmap.created_at))
        .all()
    )
    return [format_roadmap_list_item(r) for r in roadmaps]


def get_roadmap_by_id(roadmap_id: int, user_id: int, db: Session) -> Optional[Roadmap]:
    """Retrieve a specific roadmap by ID enforcing user ownership."""
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id)
        .first()
    )
    return roadmap


def update_roadmap_item_status(
    roadmap_id: int,
    item_id: int,
    is_completed: bool,
    user_id: int,
    db: Session
) -> Optional[RoadmapItem]:
    """
    Toggles completion status for a roadmap item.
    Enforces user ownership on both the roadmap and the item.
    """
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id)
        .first()
    )
    if not roadmap:
        return None

    item = (
        db.query(RoadmapItem)
        .filter(RoadmapItem.id == item_id, RoadmapItem.roadmap_id == roadmap.id)
        .first()
    )
    if not item:
        return None

    item.is_completed = is_completed
    item.completed_at = datetime.now(timezone.utc) if is_completed else None

    db.commit()
    db.refresh(item)
    return item


def delete_roadmap(roadmap_id: int, user_id: int, db: Session) -> bool:
    """Deletes a roadmap and cascades to its items."""
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id)
        .first()
    )
    if not roadmap:
        return False

    db.delete(roadmap)
    db.commit()
    return True


def get_roadmap_progress_summary(user_id: int, db: Session) -> RoadmapProgressSummary:
    """Calculates active roadmap metrics for user dashboard."""
    roadmaps = (
        db.query(Roadmap)
        .filter(Roadmap.user_id == user_id)
        .order_by(desc(Roadmap.created_at))
        .all()
    )

    if not roadmaps:
        return RoadmapProgressSummary(
            active_roadmap=None,
            total_roadmaps=0,
            total_items=0,
            completed_items=0,
            completion_percentage=0.0
        )

    # Active roadmap is the most recently created or in-progress roadmap
    active = roadmaps[0]
    items_list = active.items or []
    tot = len(items_list)
    comp = sum(1 for it in items_list if it.is_completed)
    pct = round((comp / tot * 100.0), 1) if tot > 0 else 0.0

    # Total across all roadmaps
    all_total_items = sum(len(r.items or []) for r in roadmaps)
    all_completed_items = sum(sum(1 for it in (r.items or []) if it.is_completed) for r in roadmaps)
    all_pct = round((all_completed_items / all_total_items * 100.0), 1) if all_total_items > 0 else 0.0

    return RoadmapProgressSummary(
        active_roadmap=format_roadmap_list_item(active),
        total_roadmaps=len(roadmaps),
        total_items=all_total_items,
        completed_items=all_completed_items,
        completion_percentage=all_pct
    )
