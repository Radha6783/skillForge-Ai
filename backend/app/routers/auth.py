"""
Authentication router for SkillForge AI.

Endpoints:
- POST /api/auth/register   → Register new STUDENT account
- POST /api/auth/login      → Login and receive JWT token
- GET  /api/auth/me         → Get currently authenticated user (protected)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.utils.security import hash_password, verify_password, create_access_token
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.

    - Role is always STUDENT regardless of what the client sends.
    - Password is hashed with bcrypt before storage.
    - Returns the new user (without password).
    """
    # Check for duplicate email
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.STUDENT,   # Always STUDENT on self-registration
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get an access token",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate and return a JWT bearer token.

    The token payload contains: user ID, email, role, and expiration.
    """
    user = db.query(User).filter(User.email == payload.email).first()

    # Use the same error for both "no user" and "wrong password" to prevent email enumeration
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact support.",
        )

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    }
    access_token = create_access_token(token_data)
    return TokenResponse(access_token=access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Protected endpoint. Returns the currently authenticated user's profile.
    Requires a valid Bearer token in the Authorization header.
    """
    return current_user
