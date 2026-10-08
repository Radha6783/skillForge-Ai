from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """
    Safe user response schema.
    Never exposes hashed_password.
    """
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
