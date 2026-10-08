from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.schemas.skill import (
    UserSkillCreate,
    UserSkillUpdate,
    UserSkillResponse,
    SkillResponse,
)
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/skills", tags=["skills"])

@router.get("/me", response_model=List[UserSkillResponse])
def get_my_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all skills added by the current authenticated user.
    """
    user_skills = (
        db.query(UserSkill)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == current_user.id)
        .all()
    )

    response = []
    for us in user_skills:
        response.append(
            UserSkillResponse(
                id=us.id,
                user_id=us.user_id,
                skill_id=us.skill_id,
                skill_name=us.skill.name,
                category=us.skill.category or "Technical",
                self_assessed_level=us.self_assessed_level,
                experience_months=us.experience_months,
                created_at=us.created_at,
                updated_at=us.updated_at,
            )
        )
    return response

@router.post("/me", response_model=UserSkillResponse, status_code=status.HTTP_201_CREATED)
def add_user_skill(
    skill_in: UserSkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a skill to the user's profile.
    Automatically creates the global Skill entry if it does not already exist.
    """
    cleaned_name = skill_in.skill_name.strip()
    category = skill_in.category.strip() if skill_in.category else "Technical"

    # 1. Find or create the master Skill record (case-insensitive lookup)
    skill = (
        db.query(Skill)
        .filter(func.lower(Skill.name) == func.lower(cleaned_name))
        .first()
    )

    if not skill:
        skill = Skill(name=cleaned_name, category=category)
        db.add(skill)
        db.commit()
        db.refresh(skill)
    elif category and skill.category != category:
        # Update category if master skill has default
        skill.category = category
        db.commit()

    # 2. Check if user already has this skill in user_skills
    existing_user_skill = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == current_user.id, UserSkill.skill_id == skill.id)
        .first()
    )

    if existing_user_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill '{cleaned_name}' is already in your skills profile. You can edit it instead."
        )

    # 3. Create UserSkill record
    user_skill = UserSkill(
        user_id=current_user.id,
        skill_id=skill.id,
        self_assessed_level=skill_in.self_assessed_level.value,
        experience_months=skill_in.experience_months
    )
    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)

    return UserSkillResponse(
        id=user_skill.id,
        user_id=user_skill.user_id,
        skill_id=user_skill.skill_id,
        skill_name=skill.name,
        category=skill.category or "Technical",
        self_assessed_level=user_skill.self_assessed_level,
        experience_months=user_skill.experience_months,
        created_at=user_skill.created_at,
        updated_at=user_skill.updated_at,
    )

@router.put("/me/{user_skill_id}", response_model=UserSkillResponse)
def update_user_skill(
    user_skill_id: int,
    skill_update: UserSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a skill entry for the authenticated user.
    Enforces that users can only update their own skills.
    """
    user_skill = (
        db.query(UserSkill)
        .filter(UserSkill.id == user_skill_id, UserSkill.user_id == current_user.id)
        .first()
    )

    if not user_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill entry not found in your profile."
        )

    if skill_update.self_assessed_level is not None:
        user_skill.self_assessed_level = skill_update.self_assessed_level.value

    if skill_update.experience_months is not None:
        user_skill.experience_months = skill_update.experience_months

    if skill_update.category is not None and user_skill.skill:
        user_skill.skill.category = skill_update.category.strip()

    db.commit()
    db.refresh(user_skill)

    return UserSkillResponse(
        id=user_skill.id,
        user_id=user_skill.user_id,
        skill_id=user_skill.skill_id,
        skill_name=user_skill.skill.name,
        category=user_skill.skill.category or "Technical",
        self_assessed_level=user_skill.self_assessed_level,
        experience_months=user_skill.experience_months,
        created_at=user_skill.created_at,
        updated_at=user_skill.updated_at,
    )

@router.delete("/me/{user_skill_id}")
def delete_user_skill(
    user_skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a skill from the authenticated user's profile.
    Enforces ownership check.
    """
    user_skill = (
        db.query(UserSkill)
        .filter(UserSkill.id == user_skill_id, UserSkill.user_id == current_user.id)
        .first()
    )

    if not user_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill entry not found in your profile."
        )

    db.delete(user_skill)
    db.commit()

    return {"message": "Skill removed successfully", "user_skill_id": user_skill_id}

@router.get("/catalog", response_model=List[SkillResponse])
def get_skills_catalog(db: Session = Depends(get_db)):
    """
    Get all master skills in the system for autocomplete & suggestions.
    """
    skills = db.query(Skill).order_by(Skill.name.asc()).all()
    return skills
