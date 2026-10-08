"""
Authentication dependencies for FastAPI routes.

Provides:
- get_current_user(): Validates JWT and returns the authenticated User
- require_admin(): Ensures current user has ADMIN role

Design:
- Uses FastAPI's Depends() injection system
- Reads the Bearer token from the Authorization header via OAuth2PasswordBearer
- Never duplicates auth logic across routers
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import decode_access_token

# This tells FastAPI where clients should send the token (used by Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency: Validates JWT, extracts user_id, fetches and returns active User.
    Raises 401 if the token is missing, invalid, expired, or user is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, Exception):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact support.",
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency: Allows only ADMIN-role users to proceed.
    Raises 403 for STUDENT or any other role.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user
