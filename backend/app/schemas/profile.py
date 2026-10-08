from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ProfileBase(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255, description="Full name of the student")
    college: Optional[str] = Field(None, max_length=255, description="College or University name")
    degree: Optional[str] = Field(None, max_length=100, description="Degree (e.g. B.Tech, B.S., M.S.)")
    branch: Optional[str] = Field(None, max_length=100, description="Branch/Specialization (e.g. Computer Science)")
    graduation_year: Optional[int] = Field(None, description="Graduation year (e.g. 2026)")
    target_role: Optional[str] = Field(None, max_length=100, description="Target job role (e.g. Backend Engineer)")
    experience_level: Optional[str] = Field(None, max_length=50, description="Overall experience level (BEGINNER, INTERMEDIATE, ADVANCED)")

    @field_validator("graduation_year")
    @classmethod
    def validate_grad_year(cls, v):
        if v is not None and (v < 1980 or v > 2040):
            raise ValueError("Graduation year must be between 1980 and 2040")
        return v

class ProfileUpdate(ProfileBase):
    pass

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    target_role: Optional[str] = None
    experience_level: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
