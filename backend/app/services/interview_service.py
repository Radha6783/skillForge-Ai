"""
Interview Service — Phase 8: AI Interview Simulator.

Orchestrates interview session creation, question grounding to JobAnalysis/SkillGapReport,
answer evaluation, session completion, and results computation.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer
from app.models.job_analysis import JobAnalysis, JobRequirement, SkillGapReport
from app.services.ai_service import generate_interview_questions_ai, evaluate_interview_answer_ai

logger = logging.getLogger(__name__)


def _readiness_label(score: float) -> str:
    if score >= 80:
        return "Strong"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Needs Improvement"
    return "Needs Significant Improvement"


def _build_skill_gaps_dict(report: Optional[SkillGapReport]) -> Dict[str, Any]:
    """Convert SkillGapReport model to the dict format expected by AI service."""
    if not report:
        return {"missing_skills": [], "weak_skills": [], "matching_skills": []}
    return {
        "missing_skills": report.missing_skills or [],
        "weak_skills": report.weak_skills or [],
        "matching_skills": report.matching_skills or [],
    }


def start_interview_session(
    db: Session,
    user_id: int,
    job_analysis_id: int,
    interview_type: str,
    difficulty: str,
    question_count: int,
) -> Dict[str, Any]:
    """
    Creates a new interview session:
    1. Loads JobAnalysis and verifies ownership.
    2. Loads JobRequirements.
    3. Loads latest SkillGapReport.
    4. Generates personalized questions via AI/fallback.
    5. Persists InterviewSession + InterviewQuestion records.
    Returns session dict + first question.
    """
    # 1. Fetch and verify ownership
    job_analysis: Optional[JobAnalysis] = db.query(JobAnalysis).filter(
        JobAnalysis.id == job_analysis_id,
        JobAnalysis.user_id == user_id,
    ).first()
    if not job_analysis:
        return {"error": "job_analysis_not_found", "message": "Job analysis not found or does not belong to you."}

    # 2. Load requirements
    requirements = db.query(JobRequirement).filter(
        JobRequirement.job_analysis_id == job_analysis_id
    ).all()
    req_dicts = [
        {
            "skill_name": r.skill_name,
            "category": r.category,
            "importance_level": r.importance_level or "HIGH",
            "is_required": r.is_required,
        }
        for r in requirements
    ]

    # 3. Load latest SkillGapReport
    gap_report: Optional[SkillGapReport] = (
        db.query(SkillGapReport)
        .filter(
            SkillGapReport.job_analysis_id == job_analysis_id,
            SkillGapReport.user_id == user_id,
        )
        .order_by(SkillGapReport.created_at.desc())
        .first()
    )
    skill_gaps = _build_skill_gaps_dict(gap_report)

    target_role = job_analysis.role_category or job_analysis.job_title
    topic = job_analysis.job_title

    # 4. Generate questions
    questions_data = generate_interview_questions_ai(
        target_role=target_role,
        job_title=job_analysis.job_title,
        job_requirements=req_dicts,
        skill_gaps=skill_gaps,
        interview_type=interview_type,
        difficulty=difficulty,
        count=question_count,
    )

    if not questions_data:
        return {"error": "generation_failed", "message": "Failed to generate interview questions. Please try again."}

    # 5. Create session
    session = InterviewSession(
        user_id=user_id,
        job_analysis_id=job_analysis_id,
        target_role=target_role,
        topic=topic,
        interview_type=interview_type,
        difficulty=difficulty,
        total_questions=question_count,
        status="IN_PROGRESS",
    )
    db.add(session)
    db.flush()  # get session.id before adding questions

    # 6. Create question records
    for q_data in questions_data:
        q = InterviewQuestion(
            session_id=session.id,
            question_order=q_data.get("question_order", 1),
            question_text=q_data.get("question_text", ""),
            question_type=q_data.get("question_type", "TECHNICAL"),
            skill_name=q_data.get("skill_name"),
            topic=q_data.get("topic"),
            difficulty=q_data.get("difficulty", difficulty),
            expected_key_points=q_data.get("expected_key_points", ""),
        )
        db.add(q)

    db.commit()
    db.refresh(session)

    return {"session": session, "first_question": session.questions[0] if session.questions else None}


def get_user_sessions(db: Session, user_id: int) -> List[InterviewSession]:
    """Returns all interview sessions for the user, newest first."""
    return (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.created_at.desc())
        .all()
    )


def get_session_detail(db: Session, session_id: int, user_id: int) -> Optional[InterviewSession]:
    """Returns a session with ownership check. None if not found or not owned."""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session or session.user_id != user_id:
        return None
    return session


def submit_answer(
    db: Session,
    session_id: int,
    question_id: int,
    user_answer: str,
    user_id: int,
) -> Dict[str, Any]:
    """
    Evaluates and stores a user's answer.
    Validates: session ownership, IN_PROGRESS status, question belongs to session, no duplicate answer.
    """
    # Verify session ownership + status
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session or session.user_id != user_id:
        return {"error": "session_not_found", "message": "Interview session not found."}
    if session.status != "IN_PROGRESS":
        return {"error": "session_completed", "message": "This interview session is already completed."}

    # Verify question belongs to this session
    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == question_id,
        InterviewQuestion.session_id == session_id,
    ).first()
    if not question:
        return {"error": "question_not_found", "message": "Question does not belong to this session."}

    # Check for duplicate submission
    existing = db.query(InterviewAnswer).filter(InterviewAnswer.question_id == question_id).first()
    if existing:
        return {"error": "already_answered", "message": "This question has already been answered.", "answer": existing}

    # Evaluate answer
    evaluation = evaluate_interview_answer_ai(
        question_text=question.question_text,
        skill_name=question.skill_name or question.topic or "General",
        expected_key_points=question.expected_key_points or "",
        difficulty=question.difficulty or session.difficulty,
        user_answer=user_answer,
    )

    # Store answer
    answer = InterviewAnswer(
        question_id=question_id,
        user_answer=user_answer,
        score=evaluation.get("score"),
        correctness_score=evaluation.get("correctness_score"),
        relevance_score=evaluation.get("relevance_score"),
        technical_depth_score=evaluation.get("technical_depth_score"),
        clarity_score=evaluation.get("clarity_score"),
        strengths=evaluation.get("strengths"),
        weaknesses=evaluation.get("weaknesses"),
        improvement_suggestion=evaluation.get("improvement_suggestion"),
        suggested_answer=evaluation.get("suggested_answer"),
        topics_to_revise=evaluation.get("topics_to_revise"),
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)

    return {"answer": answer}


def finish_session(db: Session, session_id: int, user_id: int) -> Dict[str, Any]:
    """
    Completes an interview session:
    - Calculates overall score from answered questions only (unanswered questions are not scored).
    - Generates summary feedback.
    - Sets status=COMPLETED, completed_at=now.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session or session.user_id != user_id:
        return {"error": "session_not_found", "message": "Interview session not found."}
    if session.status != "IN_PROGRESS":
        return {"error": "already_completed", "message": "Session is already completed."}

    # Gather answered questions
    answered = []
    for q in session.questions:
        if q.answer and q.answer.score is not None:
            answered.append(q.answer.score)

    if answered:
        overall = round(sum(answered) / len(answered), 1)
    else:
        overall = 0.0

    answered_count = len(answered)
    total = session.total_questions
    readiness = _readiness_label(overall)

    summary = (
        f"Completed {answered_count}/{total} questions. "
        f"Overall performance: {overall:.0f}/100 — {readiness}. "
    )
    if overall >= 80:
        summary += "Excellent preparation — you are well-positioned for this role."
    elif overall >= 60:
        summary += "Good foundation. Review weaker areas before the actual interview."
    elif overall >= 40:
        summary += "Needs improvement in core technical areas. Revisit recommended resources."
    else:
        summary += "Significant gaps identified. Focus on the skill-specific improvement suggestions."

    session.overall_score = overall
    session.summary_feedback = summary
    session.status = "COMPLETED"
    session.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)

    return {"session": session, "overall_score": overall, "readiness_level": readiness}


def get_session_results(db: Session, session_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Computes and returns the complete interview results including:
    - Overall score & readiness level
    - Skill-wise performance breakdown
    - Question-by-question results
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session or session.user_id != user_id:
        return None

    question_results = []
    skill_scores: Dict[str, List[float]] = {}

    for q in sorted(session.questions, key=lambda x: x.question_order):
        ans = q.answer
        answered = ans is not None
        score = ans.score if ans else None
        sn = q.skill_name or "General"

        if answered and score is not None:
            skill_scores.setdefault(sn, []).append(score)

        question_results.append({
            "question_order": q.question_order,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "skill_name": sn,
            "difficulty": q.difficulty,
            "user_answer": ans.user_answer if ans else None,
            "score": score,
            "correctness_score": ans.correctness_score if ans else None,
            "relevance_score": ans.relevance_score if ans else None,
            "technical_depth_score": ans.technical_depth_score if ans else None,
            "clarity_score": ans.clarity_score if ans else None,
            "strengths": ans.strengths if ans else None,
            "weaknesses": ans.weaknesses if ans else None,
            "improvement_suggestion": ans.improvement_suggestion if ans else None,
            "suggested_answer": ans.suggested_answer if ans else None,
            "answered": answered,
        })

    # Skill-wise performance
    skill_performance = []
    for sn, scores in skill_scores.items():
        avg = round(sum(scores) / len(scores), 1)
        skill_performance.append({
            "skill_name": sn,
            "average_score": avg,
            "question_count": len(scores),
            "performance_label": _readiness_label(avg),
        })
    skill_performance.sort(key=lambda x: x["average_score"])

    overall = session.overall_score or 0.0
    answered_count = sum(1 for q in session.questions if q.answer)

    # Top strengths and improvement areas from answers
    all_strengths = [q.answer.strengths for q in session.questions if q.answer and q.answer.strengths]
    all_improvements = [q.answer.improvement_suggestion for q in session.questions if q.answer and q.answer.improvement_suggestion]

    return {
        "session_id": session.id,
        "target_role": session.target_role,
        "topic": session.topic,
        "interview_type": session.interview_type,
        "difficulty": session.difficulty,
        "total_questions": session.total_questions,
        "answered_questions": answered_count,
        "overall_score": overall,
        "readiness_level": _readiness_label(overall),
        "summary_feedback": session.summary_feedback,
        "skill_performance": skill_performance,
        "question_results": question_results,
        "top_strengths": all_strengths[:3],
        "improvement_areas": all_improvements[:3],
    }
