"""
Security utilities for SkillForge AI.

Handles:
- Password hashing and verification using bcrypt directly
- JWT token creation and decoding
"""

import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv

load_dotenv()

# === JWT Configuration (loaded from environment, never hardcoded) ===
_secret_key = os.getenv("SECRET_KEY")
_app_env = os.getenv("APP_ENV", "development").lower()

if not _secret_key:
    if _app_env == "production":
        raise ValueError("SECRET_KEY environment variable is not set. It is required in production.")
    else:
        SECRET_KEY = "safe_development_secret_key_only"
else:
    SECRET_KEY = _secret_key

ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    Returns a UTF-8 string of the hashed password.
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.
    Returns True if valid, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    Payload contains:
    - sub: user ID (as string)
    - email: user email
    - role: user role
    - exp: expiration timestamp
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Raises:
        ExpiredSignatureError: If the token has expired.
        InvalidTokenError: If the token is invalid or tampered with.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
