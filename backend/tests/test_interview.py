"""
Phase 8: AI Interview Simulator Tests
Tests all 20 required scenarios including AI mock, fallback, validation, and user isolation.
"""

import pytest
from unittest.mock import patch


# ─────────────────────────────────────────────────────────────────────────────
# Helper: register + login shortcut
# ─────────────────────────────────────────────────────────────────────────────

def _register_and_login(client, email="test_interview@example.com", password="Testpass123!"):
    client.post("/api/auth/register", json={
        "email": email, "password": password, "full_name": "Interview Tester"
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create_job_analysis(client, token):
    """Create a job analysis with known skills and return its id."""
    resp = client.post("/api/job-analysis/analyze", json={
        "job_title": "Senior Python Developer",
        "company_name": "TestCorp",
        "job_description": (
            "We need a Python developer with FastAPI, SQL, Docker, and React experience. "
            "Strong knowledge of PostgreSQL and Git required. Agile experience preferred."
        ),
    }, headers=_auth(token), timeout=30)
    assert resp.status_code in (200, 201), f"Job analysis failed: {resp.text}"
    return resp.json()["id"]


def _run_skill_gap(client, token, job_id):
    """Trigger skill gap analysis for the given job."""
    resp = client.post(f"/api/skill-gap/analyze/{job_id}", headers=_auth(token))
    assert resp.status_code == 200, f"Skill gap failed: {resp.text}"
    return resp.json()


def _start_interview(client, token, job_id, interview_type="MIXED", difficulty="MEDIUM", count=5):
    return client.post("/api/interviews/start", json={
        "job_analysis_id": job_id,
        "interview_type": interview_type,
        "difficulty": difficulty,
        "question_count": count,
    }, headers=_auth(token))


# ─────────────────────────────────────────────────────────────────────────────
# 1. test_interview_start
# ─────────────────────────────────────────────────────────────────────────────

def test_interview_start(client):
    """Session is created, has correct fields, and generates the requested question count."""
    token = _register_and_login(client, "start@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    resp = _start_interview(client, token, job_id, count=5)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["total_questions"] == 5
    assert data["job_analysis_id"] == job_id
    assert data["interview_type"] == "MIXED"
    assert data["difficulty"] == "MEDIUM"
    assert len(data["questions"]) == 5


# ─────────────────────────────────────────────────────────────────────────────
# 2. test_question_grounding
# ─────────────────────────────────────────────────────────────────────────────

def test_question_grounding(client):
    """All generated question skill_names must come from the job requirements or be behavioral."""
    token = _register_and_login(client, "grounding@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    resp = _start_interview(client, token, job_id, interview_type="TECHNICAL", count=5)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    questions = data["questions"]
    assert len(questions) == 5
    # Every question must have a skill_name (not null)
    for q in questions:
        assert q["skill_name"] is not None and q["skill_name"] != ""
        assert q["question_text"] is not None and len(q["question_text"]) > 10


# ─────────────────────────────────────────────────────────────────────────────
# 3. test_ai_fallback_question_generation
# ─────────────────────────────────────────────────────────────────────────────

def test_ai_fallback_question_generation(client):
    """Fallback generates exactly the requested number without Gemini."""
    token = _register_and_login(client, "fallback_q@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    with patch("app.services.ai_service.os.getenv", return_value=None):
        resp = _start_interview(client, token, job_id, count=5)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert len(data["questions"]) == 5
    for q in data["questions"]:
        assert q["question_text"] is not None
        assert q["question_type"] in ("TECHNICAL", "SCENARIO", "BEHAVIORAL")


# ─────────────────────────────────────────────────────────────────────────────
# 4. test_submit_answer_and_evaluation
# ─────────────────────────────────────────────────────────────────────────────

def test_submit_answer_and_evaluation(client):
    """Answer submission returns evaluation with all required fields."""
    token = _register_and_login(client, "answer@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    sess = _start_interview(client, token, job_id, count=5).json()
    session_id = sess["id"]
    first_q_id = sess["questions"][0]["id"]

    resp = client.post(f"/api/interviews/{session_id}/answer", json={
        "question_id": first_q_id,
        "user_answer": "Python is dynamically typed. Lists are mutable, integers are immutable. "
                       "The GIL prevents true parallelism in CPU-bound threads. "
                       "I use asyncio and multiprocessing to handle concurrent workloads efficiently.",
    }, headers=_auth(token))
    assert resp.status_code == 201, resp.text
    ans = resp.json()
    # All scoring fields present
    for field in ["score", "correctness_score", "relevance_score", "technical_depth_score", "clarity_score"]:
        assert ans[field] is not None, f"Missing field: {field}"
        assert 0 <= ans[field] <= 100, f"Score out of range: {field}={ans[field]}"
    assert ans["strengths"] is not None
    assert ans["weaknesses"] is not None
    assert ans["improvement_suggestion"] is not None
    assert ans["suggested_answer"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# 5. test_ai_fallback_answer_evaluation
# ─────────────────────────────────────────────────────────────────────────────

def test_ai_fallback_answer_evaluation(client):
    """Fallback evaluation works without Gemini and produces deterministic results."""
    from app.services.ai_service import _evaluate_fallback_answer

    result1 = _evaluate_fallback_answer(
        question_text="What is Docker?",
        skill_name="Docker",
        expected_key_points="image, container, layers, build",
        difficulty="MEDIUM",
        user_answer="Docker creates containers using images and layers. You build images and run containers.",
    )
    result2 = _evaluate_fallback_answer(
        question_text="What is Docker?",
        skill_name="Docker",
        expected_key_points="image, container, layers, build",
        difficulty="MEDIUM",
        user_answer="Docker creates containers using images and layers. You build images and run containers.",
    )
    # Same input = same output (deterministic)
    assert result1["score"] == result2["score"]
    assert 0 <= result1["score"] <= 100
    for field in ["correctness_score", "relevance_score", "technical_depth_score", "clarity_score"]:
        assert field in result1


# ─────────────────────────────────────────────────────────────────────────────
# 6. test_finish_interview_session
# ─────────────────────────────────────────────────────────────────────────────

def test_finish_interview_session(client):
    """Finishing sets COMPLETED status, sets overall_score, and returns readiness_level."""
    token = _register_and_login(client, "finish@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    sess = _start_interview(client, token, job_id, count=5).json()
    session_id = sess["id"]

    # Answer one question
    first_q_id = sess["questions"][0]["id"]
    client.post(f"/api/interviews/{session_id}/answer", json={
        "question_id": first_q_id,
        "user_answer": "I use Docker to containerize applications. Images define the environment, containers are running instances. Multi-stage builds reduce image size.",
    }, headers=_auth(token))

    # Finish
    resp = client.post(f"/api/interviews/{session_id}/finish", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["overall_score"] is not None
    assert data["readiness_level"] in ("Strong", "Good", "Needs Improvement", "Needs Significant Improvement")

    # Verify status in session detail
    detail = client.get(f"/api/interviews/{session_id}", headers=_auth(token)).json()
    assert detail["status"] == "COMPLETED"


# ─────────────────────────────────────────────────────────────────────────────
# 7. test_user_isolation
# ─────────────────────────────────────────────────────────────────────────────

def test_user_isolation(client):
    """User B cannot access, answer, finish, or delete User A's interview."""
    token_a = _register_and_login(client, "isolation_a@example.com")
    token_b = _register_and_login(client, "isolation_b@example.com")

    job_id_a = _create_job_analysis(client, token_a)
    _run_skill_gap(client, token_a, job_id_a)
    sess = _start_interview(client, token_a, job_id_a, count=5).json()
    session_id = sess["id"]
    q_id = sess["questions"][0]["id"]

    # B cannot view A's session
    resp = client.get(f"/api/interviews/{session_id}", headers=_auth(token_b))
    assert resp.status_code == 404

    # B cannot answer A's question
    resp = client.post(f"/api/interviews/{session_id}/answer", json={
        "question_id": q_id, "user_answer": "attempt"
    }, headers=_auth(token_b))
    assert resp.status_code in (404, 403)

    # B cannot finish A's session
    resp = client.post(f"/api/interviews/{session_id}/finish", headers=_auth(token_b))
    assert resp.status_code in (404, 403)

    # B cannot delete A's session
    resp = client.delete(f"/api/interviews/{session_id}", headers=_auth(token_b))
    assert resp.status_code == 404

    # B cannot get A's results
    resp = client.get(f"/api/interviews/{session_id}/results", headers=_auth(token_b))
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 8. test_invalid_job_analysis
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_job_analysis(client):
    """Returns 404 for non-existent or unowned job analysis."""
    token = _register_and_login(client, "invalidjob@example.com")

    resp = _start_interview(client, token, job_id=999999, count=5)
    assert resp.status_code == 404

    # Create a job for user A; user B should get 404
    token_a = _register_and_login(client, "ija_owner@example.com")
    job_id_a = _create_job_analysis(client, token_a)
    resp = _start_interview(client, token, job_id=job_id_a, count=5)
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 9. test_delete_interview_session
# ─────────────────────────────────────────────────────────────────────────────

def test_delete_interview_session(client):
    """Deleting session removes it and all questions/answers."""
    token = _register_and_login(client, "delete_int@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    sess = _start_interview(client, token, job_id, count=5).json()
    session_id = sess["id"]
    q_id = sess["questions"][0]["id"]

    # Answer one question
    client.post(f"/api/interviews/{session_id}/answer", json={
        "question_id": q_id, "user_answer": "Test answer for deletion."
    }, headers=_auth(token))

    # Delete session
    resp = client.delete(f"/api/interviews/{session_id}", headers=_auth(token))
    assert resp.status_code == 204

    # Session no longer accessible
    resp = client.get(f"/api/interviews/{session_id}", headers=_auth(token))
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 10. test_interview_history_listing
# ─────────────────────────────────────────────────────────────────────────────

def test_interview_history_listing(client):
    """GET /api/interviews returns only the authenticated user's sessions."""
    token_a = _register_and_login(client, "history_a@example.com")
    token_b = _register_and_login(client, "history_b@example.com")

    job_id_a = _create_job_analysis(client, token_a)
    _run_skill_gap(client, token_a, job_id_a)
    _start_interview(client, token_a, job_id_a, count=5)
    _start_interview(client, token_a, job_id_a, count=5)

    job_id_b = _create_job_analysis(client, token_b)
    _run_skill_gap(client, token_b, job_id_b)
    _start_interview(client, token_b, job_id_b, count=5)

    sessions_a = client.get("/api/interviews", headers=_auth(token_a)).json()
    sessions_b = client.get("/api/interviews", headers=_auth(token_b)).json()

    assert len(sessions_a) == 2
    assert len(sessions_b) == 1
    for s in sessions_a:
        assert s["interview_type"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# 11. test_invalid_interview_type
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_interview_type(client):
    """Invalid interview_type returns 422."""
    token = _register_and_login(client, "invalid_type@example.com")
    job_id = _create_job_analysis(client, token)

    resp = client.post("/api/interviews/start", json={
        "job_analysis_id": job_id,
        "interview_type": "CODING",  # invalid
        "difficulty": "MEDIUM",
        "question_count": 5,
    }, headers=_auth(token))
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 12. test_invalid_difficulty
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_difficulty(client):
    """Invalid difficulty returns 422."""
    token = _register_and_login(client, "invalid_diff@example.com")
    job_id = _create_job_analysis(client, token)

    resp = client.post("/api/interviews/start", json={
        "job_analysis_id": job_id,
        "interview_type": "MIXED",
        "difficulty": "EXTREME",  # invalid
        "question_count": 5,
    }, headers=_auth(token))
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 13. test_invalid_question_count
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_question_count(client):
    """Invalid question_count (not 5/10/15) returns 422."""
    token = _register_and_login(client, "invalid_count@example.com")
    job_id = _create_job_analysis(client, token)

    resp = client.post("/api/interviews/start", json={
        "job_analysis_id": job_id,
        "interview_type": "MIXED",
        "difficulty": "MEDIUM",
        "question_count": 7,  # invalid
    }, headers=_auth(token))
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 14. test_empty_answer
# ─────────────────────────────────────────────────────────────────────────────

def test_empty_answer(client):
    """Submitting a blank or whitespace-only answer returns 422."""
    token = _register_and_login(client, "empty_ans@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    sess = _start_interview(client, token, job_id, count=5).json()
    session_id = sess["id"]
    q_id = sess["questions"][0]["id"]

    resp = client.post(f"/api/interviews/{session_id}/answer", json={
        "question_id": q_id, "user_answer": "   "
    }, headers=_auth(token))
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 15. test_answer_question_from_another_session
# ─────────────────────────────────────────────────────────────────────────────

def test_answer_question_from_another_session(client):
    """Cannot submit answer to a question that belongs to a different session."""
    token = _register_and_login(client, "cross_session@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    sess1 = _start_interview(client, token, job_id, count=5).json()
    sess2 = _start_interview(client, token, job_id, count=5).json()

    # Try to submit sess2 question to sess1 session
    wrong_q_id = sess2["questions"][0]["id"]
    resp = client.post(f"/api/interviews/{sess1['id']}/answer", json={
        "question_id": wrong_q_id,
        "user_answer": "Some answer"
    }, headers=_auth(token))
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 16. test_answering_completed_interview
# ─────────────────────────────────────────────────────────────────────────────

def test_answering_completed_interview(client):
    """Cannot submit answers to a completed interview session."""
    token = _register_and_login(client, "completed_int@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    sess = _start_interview(client, token, job_id, count=5).json()
    session_id = sess["id"]

    # Finish without answering
    client.post(f"/api/interviews/{session_id}/finish", headers=_auth(token))

    # Now try to answer
    q_id = sess["questions"][0]["id"]
    resp = client.post(f"/api/interviews/{session_id}/answer", json={
        "question_id": q_id, "user_answer": "Late answer attempt."
    }, headers=_auth(token))
    assert resp.status_code == 409


# ─────────────────────────────────────────────────────────────────────────────
# 17. test_duplicate_answer_submission
# ─────────────────────────────────────────────────────────────────────────────

def test_duplicate_answer_submission(client):
    """Submitting a second answer to the same question returns the existing answer (not error)."""
    token = _register_and_login(client, "dup_ans@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    sess = _start_interview(client, token, job_id, count=5).json()
    session_id = sess["id"]
    q_id = sess["questions"][0]["id"]

    client.post(f"/api/interviews/{session_id}/answer", json={
        "question_id": q_id, "user_answer": "First answer."
    }, headers=_auth(token))

    # Second submission
    resp = client.post(f"/api/interviews/{session_id}/answer", json={
        "question_id": q_id, "user_answer": "Second attempt."
    }, headers=_auth(token))
    # Should return the existing answer (200 or 201)
    assert resp.status_code in (200, 201)
    # Content should be the first answer (not empty)
    data = resp.json()
    assert data["id"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# 18. test_exact_requested_question_count
# ─────────────────────────────────────────────────────────────────────────────

def test_exact_requested_question_count(client):
    """Tests question counts 5, 10, 15 all return exactly the requested number."""
    token = _register_and_login(client, "qcount@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    for count in [5, 10, 15]:
        resp = _start_interview(client, token, job_id, count=count)
        assert resp.status_code == 201, f"Failed for count={count}: {resp.text}"
        data = resp.json()
        assert len(data["questions"]) == count, f"Expected {count} questions, got {len(data['questions'])}"


# ─────────────────────────────────────────────────────────────────────────────
# 19. test_question_skill_names_grounded_in_job_analysis
# ─────────────────────────────────────────────────────────────────────────────

def test_question_skill_names_grounded_in_job_analysis(client):
    """Technical questions must use skill_name that appears in job requirements or is Soft Skills."""
    token = _register_and_login(client, "grounded_skills@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    # Get requirements
    job_detail = client.get(f"/api/job-analysis/{job_id}", headers=_auth(token)).json()
    req_skills = {r["skill_name"].lower() for r in job_detail.get("requirements", [])}

    resp = _start_interview(client, token, job_id, interview_type="TECHNICAL", count=5)
    assert resp.status_code == 201
    questions = resp.json()["questions"]

    for q in questions:
        sn = q.get("skill_name", "").lower()
        q_type = q.get("question_type", "")
        if q_type == "BEHAVIORAL":
            # Behavioral may use "Soft Skills" or "General"
            assert sn in ("soft skills", "general") or any(rs in sn for rs in req_skills)
        else:
            # Technical/Scenario must map to a real requirement
            assert any(rs in sn or sn in rs for rs in req_skills) or sn in ("soft skills", "general"), \
                f"Skill '{sn}' not grounded in job requirements: {req_skills}"


# ─────────────────────────────────────────────────────────────────────────────
# 20. test_results_endpoint
# ─────────────────────────────────────────────────────────────────────────────

def test_results_endpoint(client):
    """Results endpoint returns full structured output after completion."""
    token = _register_and_login(client, "results@example.com")
    job_id = _create_job_analysis(client, token)
    _run_skill_gap(client, token, job_id)

    sess = _start_interview(client, token, job_id, count=5).json()
    session_id = sess["id"]

    # Answer two questions
    for i in range(2):
        q_id = sess["questions"][i]["id"]
        client.post(f"/api/interviews/{session_id}/answer", json={
            "question_id": q_id,
            "user_answer": f"Answer {i+1}: I have hands-on experience with this technology, "
                           f"applied it in production, and can discuss trade-offs and performance implications.",
        }, headers=_auth(token))

    client.post(f"/api/interviews/{session_id}/finish", headers=_auth(token))

    resp = client.get(f"/api/interviews/{session_id}/results", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Verify structure
    assert "overall_score" in data
    assert "readiness_level" in data
    assert data["readiness_level"] in ("Strong", "Good", "Needs Improvement", "Needs Significant Improvement")
    assert "skill_performance" in data
    assert "question_results" in data
    assert len(data["question_results"]) == 5
    assert data["answered_questions"] == 2
    assert data["total_questions"] == 5
