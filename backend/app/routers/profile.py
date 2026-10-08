from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.schemas.profile import ProfileUpdate, ProfileResponse
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])

@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the authenticated user's profile details.
    If no profile exists yet, initializes a default empty profile.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=current_user.full_name,
        college=profile.college,
        degree=profile.degree,
        branch=profile.branch,
        graduation_year=profile.graduation_year,
        target_role=profile.target_role,
        experience_level=profile.experience_level,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )

@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update the authenticated user's profile details.
    Also updates full_name on the User record if supplied.
    """
    # Update full_name on User model if provided
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name.strip()

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)

    # Update profile attributes
    if profile_data.college is not None:
        profile.college = profile_data.college.strip()
    if profile_data.degree is not None:
        profile.degree = profile_data.degree.strip()
    if profile_data.branch is not None:
        profile.branch = profile_data.branch.strip()
    if profile_data.graduation_year is not None:
        profile.graduation_year = profile_data.graduation_year
    if profile_data.target_role is not None:
        profile.target_role = profile_data.target_role.strip()
    if profile_data.experience_level is not None:
        profile.experience_level = profile_data.experience_level

    db.commit()
    db.refresh(current_user)
    db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=current_user.full_name,
        college=profile.college,
        degree=profile.degree,
        branch=profile.branch,
        graduation_year=profile.graduation_year,
        target_role=profile.target_role,
        experience_level=profile.experience_level,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )
