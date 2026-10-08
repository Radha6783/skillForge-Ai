from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ─── Request Schemas ─────────────────────────────────────────────────────────

class InterviewStartRequest(BaseModel):
    job_analysis_id: int
    interview_type: str = Field(default="MIXED")
    difficulty: str = Field(default="MEDIUM")
    question_count: int = Field(default=5)

    @field_validator("interview_type")
    @classmethod
    def validate_interview_type(cls, v: str) -> str:
        allowed = {"TECHNICAL", "BEHAVIORAL", "MIXED"}
        val = v.upper()
        if val not in allowed:
            raise ValueError(f"interview_type must be one of {allowed}")
        return val

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        allowed = {"EASY", "MEDIUM", "HARD"}
        val = v.upper()
        if val not in allowed:
            raise ValueError(f"difficulty must be one of {allowed}")
        return val

    @field_validator("question_count")
    @classmethod
    def validate_question_count(cls, v: int) -> int:
        allowed = {5, 10, 15}
        if v not in allowed:
            raise ValueError(f"question_count must be one of {allowed}")
        return v


class InterviewAnswerRequest(BaseModel):
    question_id: int
    user_answer: str = Field(min_length=1)

    @field_validator("user_answer")
    @classmethod
    def validate_answer_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("user_answer must not be blank")
        return v.strip()


# ─── Response Schemas ─────────────────────────────────────────────────────────

class InterviewAnswerResponse(BaseModel):
    id: int
    question_id: int
    user_answer: str
    score: Optional[float]
    correctness_score: Optional[float]
    relevance_score: Optional[float]
    technical_depth_score: Optional[float]
    clarity_score: Optional[float]
    strengths: Optional[str]
    weaknesses: Optional[str]
    improvement_suggestion: Optional[str]
    suggested_answer: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewQuestionResponse(BaseModel):
    id: int
    session_id: int
    question_order: int
    question_text: str
    question_type: Optional[str]
    skill_name: Optional[str]
    topic: Optional[str]
    difficulty: Optional[str]
    answer: Optional[InterviewAnswerResponse]

    class Config:
        from_attributes = True


class InterviewSessionResponse(BaseModel):
    id: int
    user_id: int
    job_analysis_id: Optional[int]
    target_role: str
    topic: str
    interview_type: str
    difficulty: str
    total_questions: int
    overall_score: Optional[float]
    summary_feedback: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    questions: List[InterviewQuestionResponse] = []

    class Config:
        from_attributes = True


class InterviewListItem(BaseModel):
    id: int
    job_analysis_id: Optional[int]
    target_role: str
    topic: str
    interview_type: str
    difficulty: str
    total_questions: int
    overall_score: Optional[float]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SkillPerformance(BaseModel):
    skill_name: str
    average_score: float
    question_count: int
    performance_label: str


class QuestionResult(BaseModel):
    question_order: int
    question_text: str
    question_type: Optional[str]
    skill_name: Optional[str]
    difficulty: Optional[str]
    user_answer: Optional[str]
    score: Optional[float]
    correctness_score: Optional[float]
    relevance_score: Optional[float]
    technical_depth_score: Optional[float]
    clarity_score: Optional[float]
    strengths: Optional[str]
    weaknesses: Optional[str]
    improvement_suggestion: Optional[str]
    suggested_answer: Optional[str]
    answered: bool


class InterviewResultsResponse(BaseModel):
    session_id: int
    target_role: str
    topic: str
    interview_type: str
    difficulty: str
    total_questions: int
    answered_questions: int
    overall_score: float
    readiness_level: str
    summary_feedback: Optional[str]
    skill_performance: List[SkillPerformance]
    question_results: List[QuestionResult]
    top_strengths: List[str]
    improvement_areas: List[str]
