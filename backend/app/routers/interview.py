"""
API Router for Phase 8: AI Interview Simulator endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.interview import (
    InterviewStartRequest,
    InterviewAnswerRequest,
    InterviewListItem,
    InterviewSessionResponse,
    InterviewAnswerResponse,
    InterviewResultsResponse,
)
from app.services.interview_service import (
    start_interview_session,
    get_user_sessions,
    get_session_detail,
    submit_answer,
    finish_session,
    get_session_results,
)
from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.post("/start", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
def start_interview(
    request: InterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new AI Interview Session.
    Generates personalized questions grounded in the selected JobAnalysis.
    """
    result = start_interview_session(
        db=db,
        user_id=current_user.id,
        job_analysis_id=request.job_analysis_id,
        interview_type=request.interview_type,
        difficulty=request.difficulty,
        question_count=request.question_count,
    )

    if "error" in result:
        if result["error"] == "job_analysis_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["message"])

    session = result["session"]
    return session


@router.get("", response_model=List[InterviewListItem])
def list_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all interview sessions for the authenticated user."""
    return get_user_sessions(db, current_user.id)


@router.get("/summary/recent", response_model=dict)
def recent_interview_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns summary data about the user's most recent interview session for Dashboard use."""
    sessions = get_user_sessions(db, current_user.id)
    if not sessions:
        return {"has_interviews": False, "total_sessions": 0}

    latest = sessions[0]
    completed = [s for s in sessions if s.status == "COMPLETED"]
    avg_score = round(
        sum(s.overall_score for s in completed if s.overall_score is not None) / len(completed), 1
    ) if completed else None

    return {
        "has_interviews": True,
        "total_sessions": len(sessions),
        "completed_sessions": len(completed),
        "latest_session": {
            "id": latest.id,
            "target_role": latest.target_role,
            "interview_type": latest.interview_type,
            "difficulty": latest.difficulty,
            "status": latest.status,
            "overall_score": latest.overall_score,
            "created_at": latest.created_at.isoformat(),
        },
        "average_score": avg_score,
    }


@router.get("/{session_id}", response_model=InterviewSessionResponse)
def get_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns full interview session details with questions and submitted answers."""
    session = get_session_detail(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")
    return session


@router.post("/{session_id}/answer", response_model=InterviewAnswerResponse, status_code=status.HTTP_201_CREATED)
def answer_question(
    session_id: int,
    request: InterviewAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit an answer to a question and receive immediate AI evaluation feedback."""
    result = submit_answer(
        db=db,
        session_id=session_id,
        question_id=request.question_id,
        user_answer=request.user_answer,
        user_id=current_user.id,
    )

    if "error" in result:
        if result["error"] in ("session_not_found", "question_not_found"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])
        if result["error"] == "session_completed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result["message"])
        if result["error"] == "already_answered":
            # Return the existing answer instead of error
            return result["answer"]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return result["answer"]


@router.post("/{session_id}/finish", status_code=status.HTTP_200_OK)
def finish_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Complete an interview session and calculate overall score.
    Score is computed from submitted answers only; unanswered questions are excluded.
    """
    result = finish_session(db, session_id, current_user.id)
    if "error" in result:
        if result["error"] == "session_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])
        if result["error"] == "already_completed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result["message"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return {
        "message": "Interview completed successfully.",
        "session_id": session_id,
        "overall_score": result["overall_score"],
        "readiness_level": result["readiness_level"],
        "summary_feedback": result["session"].summary_feedback,
    }


@router.get("/{session_id}/results", response_model=InterviewResultsResponse)
def get_results(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the full results breakdown including overall score, readiness level,
    skill-wise performance, and question-by-question feedback.
    """
    results = get_session_results(db, session_id, current_user.id)
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")
    return results


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an interview session and all associated questions and answers (cascade)."""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")
    db.delete(session)
    db.commit()
